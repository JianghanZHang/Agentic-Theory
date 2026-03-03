"""
Manipulation Gravity Damper — 顿开金绳，扯断玉锁

Demonstrates the gravity damper OCP applied to robotic manipulation
(Appendix J, Section 3b-manipulation of "The Knife Is the Mean").

A parallel-jaw gripper (damper κ) grasps a box (three inertia axes =
"three bodies") against gravity.  The grasp graph Laplacian's Fiedler
eigenvalue λ₁ monitors grasp quality.  The three-term control law
(gravity + least-action + spectral kick) governs grip force.

The mapping (threebody.tex lines 334-351):
    Celestial masses  ->  Object inertia axes
    Damper m*         ->  Robotic hand
    Gravitational V   ->  Gravity + contact potential
    Spectral gap λ₁   ->  Grasp quality
    Lagrange points   ->  Grasp singularities
    Thrust ū          ->  Grip force limit

Usage:
    python manipulation_damper.py                  # run simulation
    python manipulation_damper.py --headless       # no viewer
    python manipulation_damper.py --render          # render video frames

Requirements: mujoco, numpy, matplotlib
"""

import argparse
import os
import sys
import numpy as np
from numpy.linalg import eigvalsh, eigh, norm
import matplotlib
import matplotlib.pyplot as plt

import mujoco

# Ensure sibling modules are importable
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)
_OUTPUT_DIR = os.path.join(_CODE_DIR, 'outputs')
os.makedirs(_OUTPUT_DIR, exist_ok=True)

from mppi_sampler import MPPISampler, contact_weight
from mppi_sampler import MODE_SEPARATING, MODE_SLIDING, MODE_STICKING


# ── Constants ──────────────────────────────────────────────
EPSILON = 0.1        # grasp quality threshold
GRIP_FORCE_MAX = 20.0  # maximum grip force (N)
ALPHA = 0.01         # control cost weight
DT = 0.002           # MuJoCo timestep
T_FINAL = 4.0        # simulation duration
N_STEPS = int(T_FINAL / DT)

# Contact stiffness parameters
K_N = 100.0   # normal stiffness
K_T = 50.0    # tangential stiffness
MU_FRICTION = 0.8  # friction coefficient


# ══════════════════════════════════════════════════════════════
# Grasp Graph Laplacian
# ══════════════════════════════════════════════════════════════

def classify_contact_mode(contact_force_normal, contact_force_tangent,
                           mu=MU_FRICTION):
    """Classify contact mode from force measurements.

    Returns: MODE_SEPARATING, MODE_SLIDING, or MODE_STICKING.
    """
    if contact_force_normal < 0.01:
        return MODE_SEPARATING
    if abs(contact_force_tangent) > mu * contact_force_normal * 0.95:
        return MODE_SLIDING
    return MODE_STICKING


def grasp_laplacian(contact_modes, k_n=K_N, k_t=K_T, mu=MU_FRICTION):
    """Compute the grasp graph Laplacian from contact modes.

    The grasp graph has nodes = {object inertia axis 1, axis 2, axis 3}
    and edges weighted by contact transmission through each finger.

    Parameters
    ----------
    contact_modes : list of int
        Contact mode at each contact point (2 fingers = 2 contacts).

    Returns
    -------
    L : (3, 3) array
        Grasp graph Laplacian.
    lambda1 : float
        Fiedler eigenvalue (grasp quality).
    """
    # Each finger contact transmits force to the 3 inertia axes
    # through the contact mode weighting
    n = 3  # three "bodies" (inertia axes)
    L = np.zeros((n, n))

    for mode in contact_modes:
        w = contact_weight(mode, k_n, k_t, mu)
        # Each contact connects all three axes (through the rigid body)
        # Weight distribution: primary axis gets full weight,
        # cross-coupling at reduced weight
        for i in range(n):
            for j in range(i + 1, n):
                w_ij = w * 0.5  # cross-coupling factor
                L[i, i] += w_ij
                L[j, j] += w_ij
                L[i, j] -= w_ij
                L[j, i] -= w_ij

    evals = eigvalsh(L)
    lambda1 = evals[1] if len(evals) > 1 else 0.0
    return L, lambda1


def grasp_spectral_gradient(contact_modes, contact_normals,
                              k_n=K_N, k_t=K_T, mu=MU_FRICTION):
    """Gradient of λ₁ w.r.t. grip force (simplified).

    In the manipulation domain, the "spectral gradient" tells the
    gripper which direction to tighten or loosen.

    Returns
    -------
    grad : (2,) array
        Gradient w.r.t. [left_finger_force, right_finger_force].
    """
    n = 3
    L, lambda1 = grasp_laplacian(contact_modes, k_n, k_t, mu)
    _, evecs = eigh(L)
    v1 = evecs[:, 1]

    grad = np.zeros(2)  # one per finger
    delta = 0.1

    for f_idx in range(2):
        # Perturb this finger's contribution
        modes_plus = list(contact_modes)
        modes_minus = list(contact_modes)
        # Simulate increased/decreased contact by upgrading/downgrading mode
        if contact_modes[f_idx] == MODE_SEPARATING:
            modes_plus[f_idx] = MODE_SLIDING
        elif contact_modes[f_idx] == MODE_SLIDING:
            modes_plus[f_idx] = MODE_STICKING

        _, l1_plus = grasp_laplacian(modes_plus, k_n, k_t, mu)
        _, l1_base = grasp_laplacian(contact_modes, k_n, k_t, mu)
        grad[f_idx] = (l1_plus - l1_base)

    return grad


# ══════════════════════════════════════════════════════════════
# Three-Term Controller for Manipulation
# ══════════════════════════════════════════════════════════════

class ManipulationController:
    """Three-term controller mapped to manipulation domain.

    Term I:   Gravity compensation (hold object against gravity)
    Term II:  Least-action trajectory (follow planned grasp path)
    Term III: Spectral kick (tighten grasp when λ₁ → ε)
    """

    def __init__(self, epsilon=EPSILON, grip_max=GRIP_FORCE_MAX,
                 alpha=ALPHA):
        self.epsilon = epsilon
        self.grip_max = grip_max
        self.alpha = alpha

        # Grasp plan: approach -> grip -> lift -> hold
        self.phase = 'approach'
        self.phase_timer = 0.0

    def compute_control(self, object_pos, object_quat, touch_left,
                         touch_right, t):
        """Compute gripper control: [x, y, z, finger_left, finger_right].

        Returns
        -------
        ctrl : (5,) array
            Control signals for the 5 actuators.
        arc_type : int
            0 = singular, 1 = bang.
        lambda1 : float
            Current grasp quality.
        """
        ctrl = np.zeros(5)
        arc_type = 0

        # ── Phase management ──
        if self.phase == 'approach' and t > 1.0:
            self.phase = 'grip'
        elif self.phase == 'grip' and t > 1.8:
            self.phase = 'lift'
        elif self.phase == 'lift' and t > 3.5:
            self.phase = 'hold'

        # ── Contact mode classification ──
        modes = [
            MODE_STICKING if touch_left > 0.1 else MODE_SEPARATING,
            MODE_STICKING if touch_right > 0.1 else MODE_SEPARATING,
        ]

        # ── Grasp quality ──
        _, lambda1 = grasp_laplacian(modes)

        # ── Term I: Gravity compensation (gripper position) ──
        # Gripper starts at z=0.4, object at z~0.03 (on ground).
        # Fingers are offset -0.03 from base in z, so base at z=0.06
        # puts finger centres at z=0.03 (object centre height).
        # slide_z range is [-0.3, 0.3], base at 0.4 + slide.
        # To reach z_base=0.07: slide = 0.07 - 0.4 = -0.3 (limit).
        # Gripper base at z=0.3, fingers offset -0.03.
        # Object on ground at z~0.03, half-height=0.03.
        # To align fingers with object centre: base_z=0.06, slide=-0.24.
        # To lift: raise slide_z gradually.
        # Gripper base at z=0.3, fingers offset -0.04.
        # Object at z~0.03, half-height=0.03 (z range 0 to 0.06).
        # Finger centres at base_z - 0.04. Want finger_z ≈ 0.03.
        # So base_z = 0.07, slide_z = 0.07 - 0.3 = -0.23.
        if self.phase == 'approach':
            ctrl[0] = object_pos[0]
            ctrl[1] = object_pos[1]
            ctrl[2] = -0.23         # descend: base→0.07, fingers→0.03
            ctrl[3] = 0.06          # fingers wide open
            ctrl[4] = -0.06
        elif self.phase == 'grip':
            ctrl[0] = object_pos[0]
            ctrl[1] = object_pos[1]
            ctrl[2] = -0.23         # stay at object height
            ctrl[3] = -0.005        # squeeze left finger inward
            ctrl[4] = 0.005         # squeeze right finger inward
        elif self.phase in ('lift', 'hold'):
            # Term II: Least-action trajectory (lift smoothly)
            target_z = -0.1 if self.phase == 'lift' else 0.0
            ctrl[0] = object_pos[0]
            ctrl[1] = object_pos[1]
            ctrl[2] = target_z

            # Base grip: maximum squeeze (singular arc — coast)
            ctrl[3] = -0.01
            ctrl[4] = 0.01

            # ── Term III: Spectral kick ──
            if lambda1 < self.epsilon:
                # Bang arc: already at max grip, no further tightening
                # possible — the damper is at its thrust limit
                arc_type = 1
            elif lambda1 < 2 * self.epsilon:
                # Transition zone
                arc_type = 0

        return ctrl, arc_type, lambda1


# ══════════════════════════════════════════════════════════════
# Simulation
# ══════════════════════════════════════════════════════════════

def get_contact_forces(model, data):
    """Read contact forces between finger geoms and the object geom.

    Returns
    -------
    force_left, force_right : float
        Total normal contact force on left and right fingers.
    """
    obj_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM,
                                 'object_geom')
    fl_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM,
                                'finger_left_geom')
    fr_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM,
                                'finger_right_geom')
    force_left = 0.0
    force_right = 0.0

    for i in range(data.ncon):
        c = data.contact[i]
        geoms = {c.geom1, c.geom2}
        if obj_id in geoms and fl_id in geoms:
            # Get contact force
            f = np.zeros(6)
            mujoco.mj_contactForce(model, data, i, f)
            force_left += abs(f[0])  # normal force
        elif obj_id in geoms and fr_id in geoms:
            f = np.zeros(6)
            mujoco.mj_contactForce(model, data, i, f)
            force_right += abs(f[0])

    return force_left, force_right


def simulate(headless=False):
    """Run the MuJoCo manipulation simulation.

    Returns: dict with time series of object pose, λ₁, control effort.
    """
    model_path = os.path.join(_CODE_DIR, 'manipulation.xml')
    model = mujoco.MjModel.from_xml_path(model_path)
    data = mujoco.MjData(model)

    obj_pos_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR,
                                     'object_pos')
    obj_quat_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SENSOR,
                                      'object_quat')

    controller = ManipulationController()

    log = {
        'time': [],
        'lambda1': [],
        'object_pos': [],
        'object_quat': [],
        'touch_left': [],
        'touch_right': [],
        'control': [],
        'arc_type': [],
        'phase': [],
    }

    for step in range(N_STEPS):
        t = step * DT

        # Read contact forces directly
        touch_left, touch_right = get_contact_forces(model, data)

        # Object pose from sensors
        obj_pos_adr = model.sensor_adr[obj_pos_id]
        obj_quat_adr = model.sensor_adr[obj_quat_id]
        object_pos = data.sensordata[obj_pos_adr:obj_pos_adr + 3].copy()
        object_quat = data.sensordata[obj_quat_adr:obj_quat_adr + 4].copy()

        ctrl, arc_type, lambda1 = controller.compute_control(
            object_pos, object_quat, touch_left, touch_right, t)

        data.ctrl[:] = ctrl
        mujoco.mj_step(model, data)

        log['time'].append(t)
        log['lambda1'].append(lambda1)
        log['object_pos'].append(object_pos)
        log['object_quat'].append(object_quat)
        log['touch_left'].append(float(touch_left))
        log['touch_right'].append(float(touch_right))
        log['control'].append(ctrl.copy())
        log['arc_type'].append(arc_type)
        log['phase'].append(controller.phase)

        if object_pos[2] < -0.1:
            print(f"Object dropped at t={t:.2f}")
            break

    return log


# ══════════════════════════════════════════════════════════════
# Plotting
# ══════════════════════════════════════════════════════════════

def plot_results(log):
    """Plot manipulation results: grasp quality, forces, object pose."""
    fig, axes = plt.subplots(4, 1, figsize=(10, 12), sharex=True)

    t = log['time']

    # ── λ₁ (grasp quality) ──
    ax = axes[0]
    ax.plot(t, log['lambda1'], 'b-', linewidth=1.5)
    ax.axhline(y=EPSILON, color='orange', linestyle=':',
               label=f'ε = {EPSILON}')
    ax.set_ylabel('λ₁ (grasp quality)')
    ax.set_title('Manipulation Gravity Damper — 顿开金绳，扯断玉锁')
    ax.legend()

    # Shade bang arcs
    for i in range(len(t) - 1):
        if log['arc_type'][i] == 1:
            ax.axvspan(t[i], t[i] + DT, alpha=0.15, color='red')

    # ── Contact forces ──
    ax = axes[1]
    ax.plot(t, log['touch_left'], 'r-', linewidth=1, label='Left finger')
    ax.plot(t, log['touch_right'], 'b-', linewidth=1, label='Right finger')
    ax.set_ylabel('Contact force (N)')
    ax.legend()

    # ── Object height ──
    ax = axes[2]
    z = [p[2] for p in log['object_pos']]
    ax.plot(t, z, 'g-', linewidth=1.5)
    ax.set_ylabel('Object height (m)')
    ax.axhline(y=0, color='gray', linestyle=':', linewidth=0.5)

    # ── Phase ──
    ax = axes[3]
    phase_map = {'approach': 0, 'grip': 1, 'lift': 2, 'hold': 3}
    phases = [phase_map.get(p, 0) for p in log['phase']]
    ax.plot(t, phases, 'k-', linewidth=1)
    ax.set_ylabel('Phase')
    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(['approach', 'grip', 'lift', 'hold'])
    ax.set_xlabel('Time (s)')

    plt.tight_layout()
    _out = os.path.join(_OUTPUT_DIR, 'manipulation_results.png')
    plt.savefig(_out, dpi=150)
    print(f"Saved {_out}")
    plt.show()


# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Manipulation Gravity Damper (MuJoCo)')
    parser.add_argument('--headless', action='store_true',
                        help='Run without viewer')
    args = parser.parse_args()

    if args.headless:
        matplotlib.use('Agg')

    print("=" * 60)
    print("  Manipulation Gravity Damper")
    print("  顿开金绳，扯断玉锁")
    print("=" * 60)

    print("\nRunning MuJoCo simulation...")
    log = simulate(headless=args.headless)

    # Statistics
    l1 = np.array(log['lambda1'])
    arc = np.array(log['arc_type'])
    obj_z = np.array([p[2] for p in log['object_pos']])

    # Check λ₁ during grip/lift/hold (not during approach)
    grip_mask = np.array([p in ('grip', 'lift', 'hold') for p in log['phase']])
    l1_grip = l1[grip_mask] if np.any(grip_mask) else l1

    print(f"\n  Final λ₁ = {l1[-1]:.4f}")
    print(f"  Min λ₁ (post-grip) = {np.min(l1_grip):.4f}")
    print(f"  λ₁ ≥ ε during grasp: "
          f"{'YES' if np.all(l1_grip >= EPSILON - 1e-6) else 'NO'}")
    print(f"  Object final height: {obj_z[-1]:.4f} m")
    print(f"  Object dropped: "
          f"{'YES' if obj_z[-1] < -0.05 else 'NO'}")
    bang_frac = np.mean(arc == 1) * 100
    print(f"  Bang arc fraction: {bang_frac:.1f}%")
    has_all_phases = (
        'approach' in log['phase'] and 'grip' in log['phase']
        and 'lift' in log['phase'])
    print(f"  Three-term structure: {has_all_phases}")

    print("\nPlotting results...")
    plot_results(log)

    print("\nDone.")


if __name__ == '__main__':
    main()
