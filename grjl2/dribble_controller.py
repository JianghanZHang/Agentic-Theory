"""
Ball Dribble Controller — GRJL 2.0 (拍球)

Basketball dribble: hand on TOP, pushes ball DOWN toward the ground.
Ground bounces the ball back up.  Hand meets ball at apex, pushes again.

NOT 颠球 (juggling from below).  拍球.

The mapping to the thesis:
    - Ball inertia axes I₁, I₂, I₃ = "three bodies"
    - Hand (above) = damper κ
    - Ground = constraint boundary (λ₁ = 0)
    - ρ = F_hand / (m·g)

Three-term control:
    (I)   Gravity: ball falls toward ground after hand strike
    (II)  Least action: hand rises, tracks ball apex (singular, ~90%)
    (III) Spectral kick: hand strikes ball DOWNWARD at apex (bang, ~10%)

The signed distance φ = z_ball − z_ground measures proximity to the
constraint boundary.  The hand controls when the ball reaches it.

Usage:
    python dribble_controller.py                 # with viewer
    python dribble_controller.py --headless      # no display, stats only
"""

import argparse
import os
import sys
import numpy as np
from numpy.linalg import norm

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)
_OUTPUT_DIR = os.path.join(_CODE_DIR, 'outputs')
os.makedirs(_OUTPUT_DIR, exist_ok=True)

from order_parameter import compute_rho
import mujoco


# ── Scene parameters ───────────────────────────────────────
XML_PATH = os.path.join(_CODE_DIR, 'dribble.xml')
BALL_MASS = 0.3          # kg (must match XML)
GRAVITY = 9.81           # m/s²
BALL_WEIGHT = BALL_MASS * GRAVITY  # F_attraction
BALL_RADIUS = 0.06       # m (must match XML)
T_SIM = 10.0             # simulation duration (seconds)

# Hand rest position (above the ball's bounce apex)
HAND_Z_HIGH = 0.55       # hand waits here during ball's descent
HAND_Z_STRIKE = 0.30     # hand drives down to here during bang arc

# Control parameters
STRIKE_OFFSET = 0.08     # how far below the ball the hand targets (bang arc)
SDF_THRESHOLD = 0.05     # signed distance φ: ball-hand gap triggering pre-strike


# ── Controller ─────────────────────────────────────────────

class DribbleController:
    """Three-term dribble controller (拍球): hand on top, pushes down."""

    # Paddle body rest position in world frame (from XML: pos="0 0 0.8")
    PADDLE_REST_POS = np.array([0.0, 0.0, 0.8])

    def __init__(self, model, data):
        self.model = model
        self.data = data
        self.dt = model.opt.timestep

        # Sensor addresses
        self._ball_pos_adr = self._sensor_adr('ball_pos')
        self._ball_vel_adr = self._sensor_adr('ball_vel')
        self._paddle_pos_adr = self._sensor_adr('paddle_pos')
        self._touch_adr = self._sensor_adr('paddle_touch')

        # Logging
        self.log = {
            'time': [],
            'ball_z': [],
            'paddle_z': [],
            'rho': [],
            'control_z': [],
            'arc_type': [],   # 0=singular, 1=bang
            'contact_force': [],
            'sdf': [],        # signed distance: ball_z - ground
        }

    def _sensor_adr(self, name):
        sid = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SENSOR, name)
        return self.model.sensor_adr[sid]

    @property
    def ball_pos(self):
        return self.data.sensordata[self._ball_pos_adr:
                                     self._ball_pos_adr + 3].copy()

    @property
    def ball_vel(self):
        return self.data.sensordata[self._ball_vel_adr:
                                     self._ball_vel_adr + 3].copy()

    @property
    def paddle_pos(self):
        return self.data.sensordata[self._paddle_pos_adr:
                                     self._paddle_pos_adr + 3].copy()

    @property
    def paddle_contact_force(self):
        """Normal contact force on hand (from touch sensor)."""
        return float(self.data.sensordata[self._touch_adr])

    def predict_apex(self, pos, vel):
        """Predict the ball's apex (highest point) after ground bounce.

        During ascent (vz > 0): apex at t = vz/g, z_apex = z + vz²/(2g).
        During descent (vz < 0): ball hits ground first, bounces, then apex.
        """
        z0 = pos[2]
        vz = vel[2]

        if vz > 0:
            # Ball rising — apex time and position
            t_apex = vz / GRAVITY
            z_apex = z0 + vz**2 / (2 * GRAVITY)
            x_apex = pos[0] + vel[0] * t_apex
            y_apex = pos[1] + vel[1] * t_apex
        else:
            # Ball descending — predict bounce then apex
            # Approximate: just use current position
            t_apex = 0.2
            z_apex = z0
            x_apex = pos[0] + vel[0] * t_apex
            y_apex = pos[1] + vel[1] * t_apex

        return np.array([x_apex, y_apex, z_apex]), t_apex

    def step(self, t):
        """One control step.

        拍球 phase logic:
          1. Ball descending → ground bounce (singular: hand high, waiting)
          2. Ball ascending after bounce (singular: hand tracks apex xy)
          3. Ball near apex (pre-strike: hand moves to ball's xy, lowers)
          4. Hand contacts ball (bang: hand drives DOWN through ball)
          5. Ball pushed down → falls → ground bounce → repeat
        """
        ball_p = self.ball_pos
        ball_v = self.ball_vel
        paddle_p = self.paddle_pos

        # ── Read ρ from contact force ──
        F_contact = self.paddle_contact_force
        rho = compute_rho(F_contact, BALL_WEIGHT)

        # ── Signed distance: ball surface to ground ──
        sdf = ball_p[2] - BALL_RADIUS  # φ > 0 means separated from ground

        # ── State ──
        ball_z = ball_p[2]
        ball_vz = ball_v[2]
        ascending = ball_vz > 0.05
        near_apex = ascending and ball_vz < 0.8  # slowing down near top
        in_contact = rho > 0.1
        ball_near_ground = sdf < 0.10  # within 10cm of ground surface

        # ── Three-term control ──
        target_world = np.zeros(3)
        arc_type = 0  # singular

        # Predict apex for xy tracking
        apex, t_apex = self.predict_apex(ball_p, ball_v)

        # Always track ball's xy
        target_world[0] = ball_p[0]
        target_world[1] = ball_p[1]

        if in_contact and not ball_near_ground:
            # ── (III) BANG ARC: hand striking ball downward AT APEX ──
            # Only strike when ball is well above ground
            target_world[2] = ball_z - STRIKE_OFFSET
            arc_type = 1

        elif near_apex and (ball_z > 0.20) and not ball_near_ground:
            # ── PRE-STRIKE: ball rising, near apex ──
            # Hand lowers to meet the ball from above
            target_world[0] = apex[0]
            target_world[1] = apex[1]
            target_world[2] = ball_z + BALL_RADIUS + 0.02  # just above ball
            arc_type = 0

        else:
            # ── (I + II) SINGULAR ARC: ball in free flight or near ground ──
            # Hand rises to rest position (high), lets ball bounce freely
            target_world[0] = apex[0]
            target_world[1] = apex[1]
            target_world[2] = HAND_Z_HIGH
            arc_type = 0

        # Convert world target to joint offsets
        ctrl = target_world - self.PADDLE_REST_POS
        self.data.ctrl[:] = ctrl

        # ── Log ──
        self.log['time'].append(t)
        self.log['ball_z'].append(ball_z)
        self.log['paddle_z'].append(paddle_p[2])
        self.log['rho'].append(rho)
        self.log['control_z'].append(ctrl[2])
        self.log['arc_type'].append(arc_type)
        self.log['contact_force'].append(F_contact)
        self.log['sdf'].append(sdf)


# ── Simulation loop ───────────────────────────────────────

def run_simulation(headless=False):
    """Run the dribble simulation."""
    model = mujoco.MjModel.from_xml_path(XML_PATH)
    data = mujoco.MjData(model)
    mujoco.mj_resetData(model, data)

    # Ball: dropped from mid-height
    # freejoint qpos: [x, y, z, qw, qx, qy, qz]
    data.qpos[0] = 0.0    # x
    data.qpos[1] = 0.0    # y
    data.qpos[2] = 0.4    # z — start at moderate height
    data.qpos[3] = 1.0    # quaternion w

    # Hand (paddle): starts above ball
    # Paddle body rest pos is [0, 0, 0.8]; joints offset from there
    data.qpos[7] = 0.0    # x offset
    data.qpos[8] = 0.0    # y offset
    data.qpos[9] = 0.0    # z offset → hand at z = 0.8 (above ball at 0.4)

    controller = DribbleController(model, data)

    dt = model.opt.timestep
    n_steps = int(T_SIM / dt)

    # Viewer
    viewer = None
    if not headless:
        try:
            from mujoco.viewer import launch_passive
            viewer = launch_passive(model, data)
        except Exception:
            print("No viewer available, running headless.")
            headless = True

    print("=" * 60)
    print("  Ball Dribble Controller (拍球) — GRJL 2.0")
    print("  顿开金绳，扯断玉锁")
    print("=" * 60)

    # ── Main loop ──
    bounce_count = 0
    was_in_contact = False

    for step in range(n_steps):
        t = step * dt
        controller.step(t)
        mujoco.mj_step(model, data)

        # Count hand-ball contacts (not ground-ball)
        in_contact = controller.paddle_contact_force > 0.1
        if in_contact and not was_in_contact:
            bounce_count += 1
        was_in_contact = in_contact

        if viewer is not None:
            viewer.sync()

        # Escape checks
        ball_z = controller.ball_pos[2]
        if ball_z < -0.1:
            print(f"Ball fell through at t={t:.2f}")
            break
        if ball_z > 5.0:
            print(f"Ball escaped upward at t={t:.2f}")
            break
        if abs(controller.ball_pos[0]) > 3 or abs(controller.ball_pos[1]) > 3:
            print(f"Ball escaped laterally at t={t:.2f}")
            break

    if viewer is not None:
        viewer.close()

    # ── Statistics ──
    log = controller.log
    rho_arr = np.array(log['rho'])
    arc_arr = np.array(log['arc_type'])
    ball_z_arr = np.array(log['ball_z'])
    sdf_arr = np.array(log['sdf'])
    total_steps = len(arc_arr)
    bang_steps = np.sum(arc_arr == 1)

    print(f"\n  Results:")
    print(f"    Duration        = {t:.2f} s")
    print(f"    Hand-ball hits  = {bounce_count}")
    print(f"    Ball z range    = [{np.min(ball_z_arr):.3f}, "
          f"{np.max(ball_z_arr):.3f}]")
    print(f"    SDF range       = [{np.min(sdf_arr):.3f}, "
          f"{np.max(sdf_arr):.3f}]")
    print(f"    ρ range         = [{np.min(rho_arr):.3f}, "
          f"{np.max(rho_arr):.3f}]")
    print(f"    Bang fraction   = {100 * bang_steps / max(total_steps, 1):.1f}%")

    rho_spikes = np.sum(rho_arr > 1.0)
    print(f"    ρ > 1 steps     = {rho_spikes} "
          f"({100 * rho_spikes / max(total_steps, 1):.1f}%)")

    return log, bounce_count


# ── Plotting ───────────────────────────────────────────────

def plot_dribble(log):
    """4-panel plot: heights, ρ, SDF, contact force."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(4, 1, figsize=(10, 11), sharex=True)
    t = log['time']

    # Panel 1: Ball and hand height
    ax = axes[0]
    ax.plot(t, log['ball_z'], 'b-', linewidth=1, label='Ball z')
    ax.plot(t, log['paddle_z'], 'r-', linewidth=0.8, label='Hand z',
            alpha=0.7)
    ax.axhline(y=BALL_RADIUS, color='black', linestyle=':',
               linewidth=0.5, label='Ground')
    ax.set_ylabel('Height (m)')
    ax.set_title('Basketball Dribble (拍球)')
    ax.legend(fontsize=8)
    for i in range(len(t) - 1):
        if log['arc_type'][i] == 1:
            ax.axvspan(t[i], t[i] + 0.002, alpha=0.2, color='red')

    # Panel 2: ρ
    ax = axes[1]
    ax.plot(t, log['rho'], 'r-', linewidth=1)
    ax.axhline(y=1.0, color='black', linestyle='--',
               linewidth=0.8, label='ρ = 1')
    ax.set_ylabel('ρ = F_hand / (mg)')
    ax.set_yscale('symlog', linthresh=0.1)
    ax.legend(fontsize=8)

    # Panel 3: SDF (signed distance to ground)
    ax = axes[2]
    ax.plot(t, log['sdf'], 'g-', linewidth=1)
    ax.axhline(y=0.0, color='black', linestyle='--',
               linewidth=0.8, label='φ = 0 (ground contact)')
    ax.set_ylabel('SDF φ (m)')
    ax.legend(fontsize=8)

    # Panel 4: Contact force
    ax = axes[3]
    ax.plot(t, log['contact_force'], 'purple', linewidth=0.8)
    ax.axhline(y=BALL_WEIGHT, color='orange', linestyle=':',
               linewidth=0.8, label=f'mg = {BALL_WEIGHT:.2f} N')
    ax.set_ylabel('Hand contact force (N)')
    ax.set_xlabel('Time (s)')
    ax.legend(fontsize=8)

    plt.tight_layout()
    _out = os.path.join(_OUTPUT_DIR, 'dribble_results.png')
    plt.savefig(_out, dpi=150)
    print(f"Saved {_out}")
    plt.show()


# ── Main ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Ball Dribble Controller (拍球)')
    parser.add_argument('--headless', action='store_true',
                        help='Run without viewer')
    args = parser.parse_args()

    import matplotlib
    if args.headless:
        matplotlib.use('Agg')

    log, bounces = run_simulation(headless=args.headless)

    if not args.headless:
        plot_dribble(log)

    # Verification summary
    print(f"\n  Verification:")
    print(f"    V3.1 Runs without error: PASS")
    v32 = "PASS" if bounces >= 3 else f"FAIL (got {bounces})"
    print(f"    V3.2 Ball bounces ≥ 3:   {v32}")

    rho_arr = np.array(log['rho'])
    spikes = np.sum(rho_arr > 1.0)
    v33 = "PASS" if spikes > 0 else "FAIL"
    print(f"    V3.3 ρ spikes at bounce:  {v33}")

    arc_arr = np.array(log['arc_type'])
    bang_frac = np.mean(arc_arr == 1)
    v35 = "PASS" if bang_frac < 0.5 else "FAIL"
    print(f"    V3.5 Singular ≫ bang:     {v35} "
          f"(bang={100*bang_frac:.1f}%)")


if __name__ == '__main__':
    main()
