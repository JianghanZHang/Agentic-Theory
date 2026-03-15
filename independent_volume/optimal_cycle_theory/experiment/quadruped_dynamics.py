"""Centroidal quadruped dynamics for trajectory optimization + MuJoCo simulation.

Two models:
1. CentroidalQuadrupedDynamics: simplified centroidal model for SQP planning.
   Subclasses diffmpc's Dynamics base class. Pure JAX, differentiable.

2. MuJoCoQuadruped: full-physics simulation via MuJoCo with implicit Euler
   and high contact solver iterations. Ground truth evaluation of gaits.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional

import jax
import jax.numpy as jnp
import numpy as np

from diffmpc.dynamics.base_dynamics import Dynamics
from config import ROBOT, NX, NU, MUJOCO


# ═══════════════════════════════════════════════════════════════════
# Planning model: centroidal dynamics (for SQP-ADMM inner solver)
# ═══════════════════════════════════════════════════════════════════

class CentroidalQuadrupedDynamics(Dynamics):
    """Centroidal dynamics with barrier-smoothed force activation.

    Contact enters via params["force_scale"]: (4,) continuous array in [0, 1].
    Computed from barrier: scale_k = λ_k / (λ_k + 1) where λ_k = ε / h_k.
    ≈ 1 when foot on ground (stance), ≈ 0 when foot in air (swing).
    Smooth and differentiable — no binary contact mask.

    Also accepts legacy params["contact_mask"] for backward compatibility.

    State (13): [px,py,pz, vx,vy,vz, phi_x,phi_y,phi_z, wx,wy,wz, phase]
    Control (12): [f0_x,f0_y,f0_z, ..., f3_x,f3_y,f3_z]
    """

    def __init__(self, mass=None, inertia=None, foot_positions=None):
        params = {
            "num_states": NX,
            "num_controls": NU,
            "names_states": [
                "px", "py", "pz", "vx", "vy", "vz",
                "phi_x", "phi_y", "phi_z", "wx", "wy", "wz", "phase",
            ],
            "names_controls": [f"f{k}_{d}" for k in range(4) for d in "xyz"],
        }
        super().__init__(params)
        self.mass = mass if mass is not None else ROBOT["mass"]
        self.inertia = inertia if inertia is not None else ROBOT["inertia"]
        self.foot_pos = foot_positions if foot_positions is not None else ROBOT["foot_positions"]

    def state_dot(self, state, control, params):
        v = state[3:6]
        omega = state[9:12]

        forces = control.reshape(4, 3)

        # Barrier-smoothed force scaling (continuous, differentiable)
        # Falls back to legacy binary contact_mask if force_scale not provided
        if "force_scale" in params:
            scale = params["force_scale"]  # (4,) continuous in [0, 1]
        else:
            scale = params["contact_mask"]  # (4,) binary (legacy)
        forces = forces * scale[:, None]

        # Translational: m * dv = sum(f_k) + m*g
        total_force = jnp.sum(forces, axis=0)
        dv = total_force / self.mass + jnp.array([0.0, 0.0, -9.81])

        # Rotational: I * dw = sum(r_k × f_k)
        torques = jnp.sum(jnp.cross(self.foot_pos, forces), axis=0)
        dw = torques / self.inertia

        # Orientation rate: dphi = omega (small angle)
        dphi = omega

        # Phase clock
        stride_freq = params.get("stride_frequency", ROBOT["stride_frequency"])
        dphase = jnp.array([stride_freq])

        return jnp.concatenate([v, dv, dphi, dw, dphase])


# ═══════════════════════════════════════════════════════════════════
# Simulation model: MuJoCo Go2 (ground truth)
# ═══════════════════════════════════════════════════════════════════

# Go2 leg ordering (MuJoCo XML + gait_sampler): FL, FR, RL, RR
# Each leg has 3 joints: hip, thigh, calf → 12 actuators total
# MuJoCo qpos: [x,y,z, qw,qx,qy,qz, 12 joint angles] = 19
# MuJoCo qvel: [vx,vy,vz, wx,wy,wz, 12 joint velocities] = 18
# Gait phase: phi = [phi_FL, phi_RL, phi_RR], FR is reference at phase 0

_GO2_SCENE = Path(__file__).parent / "assets" / "mujoco_menagerie" / "unitree_go2" / "scene.xml"

# Foot body names in Go2 model (calf links contain the foot geoms)
_FOOT_BODY_NAMES = ["FL_calf", "FR_calf", "RL_calf", "RR_calf"]

# Default standing joint configuration (from go2.xml keyframe "home")
_STANDING_QPOS_JOINTS = np.array([
    0.0,  0.9, -1.8,   # FL: hip, thigh, calf
    0.0,  0.9, -1.8,   # FR
    0.0,  0.9, -1.8,   # RL
    0.0,  0.9, -1.8,   # RR
])

# ── Joint-space renormalization ──
# Map each joint's physical range → normalized space centered on standing pose.
# q̃ = (q - q_stand) / (q_range / 2)
# Standing pose maps to q̃ = 0; joint limits at q̃ = a_i, b_i (asymmetric).
# Barrier: V_joint = -ε [log(q̃ - a) + log(b - q̃)] repels from limits.
#
# Uniform PD gains in normalized space = correct per-joint gains in physical space.

# Go2 joint ranges from XML (per leg type)
_JOINT_RANGE = {
    "FL": np.array([[-1.0472, 1.0472], [-1.5708, 3.4907], [-2.7227, -0.8378]]),
    "FR": np.array([[-1.0472, 1.0472], [-1.5708, 3.4907], [-2.7227, -0.8378]]),
    "RL": np.array([[-1.0472, 1.0472], [-0.5236, 4.5379], [-2.7227, -0.8378]]),
    "RR": np.array([[-1.0472, 1.0472], [-0.5236, 4.5379], [-2.7227, -0.8378]]),
}

# Flat (12,) arrays for vectorized operations
_Q_MIN = np.concatenate([_JOINT_RANGE[leg][:, 0] for leg in ["FL", "FR", "RL", "RR"]])
_Q_MAX = np.concatenate([_JOINT_RANGE[leg][:, 1] for leg in ["FL", "FR", "RL", "RR"]])
_Q_CENTER = _STANDING_QPOS_JOINTS.copy()  # standing = 0 in normalized space
_Q_HALF_RANGE = 0.5 * (_Q_MAX - _Q_MIN)

# Precomputed normalized joint limits (asymmetric when standing ≠ midpoint)
_Q_NORM_MIN = (_Q_MIN - _Q_CENTER) / _Q_HALF_RANGE
_Q_NORM_MAX = (_Q_MAX - _Q_CENTER) / _Q_HALF_RANGE

# Actuator torque limits from go2.xml (per joint type, repeated per leg)
_TORQUE_LIMIT = np.array([
    23.7, 23.7, 45.43,   # FL: hip, thigh, calf
    23.7, 23.7, 45.43,   # FR
    23.7, 23.7, 45.43,   # RL
    23.7, 23.7, 45.43,   # RR
])

def normalize_joints(q_phys: np.ndarray) -> np.ndarray:
    """Physical joint angles → normalized (standing = 0)."""
    return (q_phys - _Q_CENTER) / _Q_HALF_RANGE

def denormalize_joints(q_norm: np.ndarray) -> np.ndarray:
    """Normalized → physical joint angles."""
    return q_norm * _Q_HALF_RANGE + _Q_CENTER

# Standing pose in normalized coordinates: zero by construction
_STANDING_NORMALIZED = np.zeros(12)


class MuJoCoQuadruped:
    """MuJoCo Go2 simulation wrapper for ground-truth gait evaluation.

    Uses implicit Euler with high contact solver iterations to suppress
    simulation artifacts. The real articulated model provides honest physics
    that the centroidal planning model cannot.

    Controls: 12 joint torques [FL_hip, FL_thigh, FL_calf, FR_..., RL_..., RR_...]
    The MPPI loop provides desired foot forces from the centroidal plan;
    a Jacobian-transpose mapping converts these to joint torques.
    """

    def __init__(self, scene_path: Optional[str] = None,
                 mujoco_config: Optional[Dict] = None):
        import mujoco

        cfg = mujoco_config or MUJOCO
        path = scene_path or str(_GO2_SCENE)
        self.model = mujoco.MjModel.from_xml_path(path)

        # Override simulation settings for robust contact solving
        self.model.opt.timestep = cfg["timestep"]
        self.model.opt.integrator = getattr(
            mujoco.mjtIntegrator, f"mjINT_{cfg['integrator'].upper()}"
        )
        self.model.opt.solver = getattr(
            mujoco.mjtSolver, f"mjSOL_{cfg['solver'].upper()}"
        )
        self.model.opt.iterations = cfg["niter"]
        self.model.opt.tolerance = cfg["tolerance"]

        self.data = mujoco.MjData(self.model)
        self._mujoco = mujoco
        self._dt_sim = cfg["timestep"]

        # Cache foot body IDs for contact detection
        self._foot_body_ids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, name)
            for name in _FOOT_BODY_NAMES
        ]
        self._floor_geom_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_GEOM, "floor"
        )

        # Cache Jacobian workspace
        self._jacp = np.zeros((3, self.model.nv))
        self._jacr = np.zeros((3, self.model.nv))

        # PID integrator state (persistent across steps, reset on reset())
        self._z_integrator = np.zeros(12)

    def reset(self, x0_centroidal: Optional[np.ndarray] = None):
        """Reset to standing pose, optionally with centroidal initial state.

        Args:
            x0_centroidal: (13,) centroidal state [pos, vel, phi, omega, phase].
                           Joint angles are set to nominal standing pose.
        """
        self._mujoco.mj_resetData(self.model, self.data)

        # Set nominal standing joint configuration
        self.data.qpos[7:] = _STANDING_QPOS_JOINTS

        if x0_centroidal is not None:
            x0 = np.asarray(x0_centroidal)
            # Base position
            self.data.qpos[:3] = x0[:3]
            # Base orientation: Rodrigues → quaternion
            phi = x0[6:9]
            angle = np.linalg.norm(phi)
            if angle > 1e-8:
                axis = phi / angle
                self.data.qpos[3] = np.cos(angle / 2)
                self.data.qpos[4:7] = axis * np.sin(angle / 2)
            else:
                self.data.qpos[3] = 1.0
                self.data.qpos[4:7] = 0.0
            # Base velocity
            self.data.qvel[:3] = x0[3:6]
            self.data.qvel[3:6] = x0[9:12]

        self._mujoco.mj_forward(self.model, self.data)
        self._z_integrator[:] = 0.0  # reset integrator on new episode

    def step_torques(self, joint_torques: np.ndarray, dt_ocp: float):
        """Simulate one OCP timestep with joint torques.

        Args:
            joint_torques: (12,) joint torques
            dt_ocp: OCP discretization time (e.g. 0.02s)
        """
        n_substeps = max(1, int(round(dt_ocp / self._dt_sim)))
        self.data.ctrl[:12] = np.asarray(joint_torques)
        for _ in range(n_substeps):
            self._mujoco.mj_step(self.model, self.data)

    def foot_forces_to_joint_torques(self, foot_forces: np.ndarray,
                                     contact_mask: np.ndarray) -> np.ndarray:
        """Convert centroidal foot forces → joint torques via Jacobian transpose.

        τ = J^T f  for each leg in stance.

        Args:
            foot_forces: (12,) = [f0_x,f0_y,f0_z, ..., f3_x,f3_y,f3_z]
            contact_mask: (4,) binary

        Returns:
            joint_torques: (12,) joint torques
        """
        forces = foot_forces.reshape(4, 3)
        torques = np.zeros(12)

        for k in range(4):
            if contact_mask[k] < 0.5:
                continue
            # Get foot Jacobian (3×nv) for foot body k
            self._mujoco.mj_jacBody(
                self.model, self.data, self._jacp, self._jacr,
                self._foot_body_ids[k]
            )
            # Extract the 3 joint columns for this leg
            # Joints are ordered: joint 1+3k, 2+3k, 3+3k
            # In qvel, they map to indices 6+3k : 6+3(k+1)
            jac_leg = self._jacp[:, 6 + 3*k : 6 + 3*(k+1)]  # (3, 3)
            torques[3*k : 3*(k+1)] = jac_leg.T @ forces[k]

        return torques

    def step_foot_forces(self, foot_forces: np.ndarray,
                         contact_mask: np.ndarray, dt_ocp: float):
        """Simulate one OCP timestep with centroidal foot forces.

        Converts foot forces → joint torques via Jacobian transpose, then steps.
        For swing legs, applies a PD controller to track a default retracted pose.

        Args:
            foot_forces: (12,) foot forces from centroidal planner
            contact_mask: (4,) binary (which feet are in stance)
            dt_ocp: OCP timestep
        """
        # Stance legs: Jacobian transpose mapping
        torques = self.foot_forces_to_joint_torques(foot_forces, contact_mask)

        # Swing legs: PD tracking to retracted pose
        kp, kd = 40.0, 2.0
        swing_target = np.array([0.0, 1.3, -2.2])  # swing peak per leg
        for k in range(4):
            if contact_mask[k] > 0.5:
                continue
            q_leg = self.data.qpos[7 + 3*k : 7 + 3*(k+1)]
            v_leg = self.data.qvel[6 + 3*k : 6 + 3*(k+1)]
            torques[3*k : 3*(k+1)] = kp * (swing_target - q_leg) - kd * v_leg

        self.step_torques(torques, dt_ocp)

    def step_impedance(self, barrier_scales: np.ndarray,
                       foot_height_frac: np.ndarray, dt_ocp: float,
                       epsilon: float = 1.0):
        """Physical-space PID impedance controller with anti-windup.

        Gains are defined in physical space (N·m/rad, N·m·s/rad) to avoid
        the non-uniform physical stiffness that arises from normalized-space
        PD with disparate joint ranges (see §articulated, "Pitfall").

        The barrier scale σ_k modulates the gains:
            K_p(σ) = K_p^swing + (K_p^stance - K_p^swing) · σ
            K_i(σ) = K_i^stance · σ   (integral active only in stance)
        Joint-limit barrier adds repulsive torque (in normalized space,
        converted to physical).

        Anti-windup: when |τ_k| ≥ τ_max, the integrator freezes (ż=0).
        This prevents fictitious winding-number accumulation on R.

        Args:
            barrier_scales: (4,) in [0,1], ≈1 stance, ≈0 swing.
            foot_height_frac: (4,) h_k/h_max in [0,1]. 0=ground, 1=peak.
            dt_ocp: OCP timestep.
            epsilon: barrier/temperature parameter (same ε as contact/MPPI).
        """
        # Physical-space gains (uniform across all joints — no range distortion)
        kp_stance, kd_stance, ki_stance = 30.0, 0.5, 5.0
        kp_swing, kd_swing = 10.0, 0.3

        # Gravity compensation from inverse dynamics
        grav_comp = self.data.qfrc_bias[6:18].copy()

        # Swing peak in physical joint angles
        q_swing_peak = np.array([
            0.0, 1.3, -2.2,   # FL
            0.0, 1.3, -2.2,   # FR
            0.0, 1.3, -2.2,   # RL
            0.0, 1.3, -2.2,   # RR
        ])

        # Current physical state
        q_phys = self.data.qpos[7:19].copy()
        v_phys = self.data.qvel[6:18].copy()

        # Raibert foot placement: offset = k * (v_des - v) * T_stance / (2*L)
        # Go2 convention: +thigh angle = foot backward. At v < v_des,
        # positive offset → foot behind hip → forward push.
        v_forward = self.data.qvel[0]  # body x-velocity (world frame)
        v_des = float(ROBOT.get("target_velocity_x", 1.0))
        k_raibert = ROBOT.get("k_raibert", 0.0)
        T_stance = ROBOT["duty_factor"] * ROBOT["stride_period"]
        L_leg = ROBOT["standing_height"]
        delta_thigh = k_raibert * (v_des - v_forward) * T_stance / (2.0 * L_leg)

        # Normalized state (for joint-limit barrier only)
        q_norm = normalize_joints(q_phys)

        # Joint-limit barrier weight
        w_jb = 0.1

        torques = np.zeros(12)
        position_errors = np.zeros(12)

        for k in range(4):
            s = barrier_scales[k]
            h_frac = foot_height_frac[k]
            idx = slice(3*k, 3*(k+1))

            # Interpolate gains by barrier scale (physical space)
            kp = kp_swing + (kp_stance - kp_swing) * s
            kd = kd_swing + (kd_stance - kd_swing) * s
            ki = ki_stance * s  # integral only in stance

            # Target in physical space: blend standing ↔ swing peak
            q_target = _STANDING_QPOS_JOINTS[idx] + h_frac * (
                q_swing_peak[idx] - _STANDING_QPOS_JOINTS[idx]
            )
            # Raibert: offset thigh angle during swing for forward foot placement
            if h_frac > 0.1:
                q_target[1] += delta_thigh

            # Position error (physical space)
            e = q_target - q_phys[idx]
            position_errors[idx] = e

            # PID in physical space
            tau = kp * e + ki * self._z_integrator[idx] - kd * v_phys[idx]

            # Gravity compensation (modulated: full in stance, off in swing)
            tau += s * grav_comp[idx]

            # Joint-limit barrier (computed in normalized space, converted)
            # τ_barrier_phys = w_jb · ε · [1/(q̃-a) - 1/(b-q̃)] / r
            q_lo = np.maximum(q_norm[idx] - _Q_NORM_MIN[idx], 1e-4)
            q_hi = np.maximum(_Q_NORM_MAX[idx] - q_norm[idx], 1e-4)
            tau_barrier_norm = w_jb * epsilon * (1.0 / q_lo - 1.0 / q_hi)
            tau += tau_barrier_norm / _Q_HALF_RANGE[idx]

            torques[idx] = tau

        # ── Anti-windup: freeze integrator where torque saturates ──
        # eq:anti-windup from paper: ż_k = e_k if |τ| < τ_max, 0 otherwise
        saturated = np.abs(torques) >= _TORQUE_LIMIT * 0.95
        for i in range(12):
            if not saturated[i]:
                self._z_integrator[i] += position_errors[i] * dt_ocp

        # Hard clip (safety net — anti-windup should prevent most saturation)
        torques = np.clip(torques, -_TORQUE_LIMIT, _TORQUE_LIMIT)
        self.step_torques(torques, dt_ocp)

    def step_tvlqr(self, K_t: np.ndarray, k_t: np.ndarray,
                   x_ref_t: np.ndarray, barrier_scales: np.ndarray,
                   foot_height_frac: np.ndarray, dt_ocp: float,
                   epsilon: float = 1.0):
        """DEPRECATED: Uses mj_jacBody J^T mapping which is architecturally wrong.

        MuJoCo should only be the plant. Optimization uses centroidal
        forward_simulate(); playback uses step_impedance().
        Kept for backward compatibility with saved data only.

        The Riccati solver gives optimal centroidal foot forces:
            u = k_t - K_t @ (x - x_ref_t)
        Mapped to joint torques via:
            stance (σ≈1): τ = J^T f  (Jacobian transpose)
            swing  (σ≈0): τ = PD tracking to swing trajectory
        Blended continuously by barrier scale σ_k.

        Args:
            K_t: (12, 13) feedback gain at this timestep
            k_t: (12,) feedforward at this timestep
            x_ref_t: (13,) reference centroidal state
            barrier_scales: (4,) σ_k values in [0,1]
            foot_height_frac: (4,) h_k/h_max for swing target
            dt_ocp: OCP timestep
            epsilon: barrier parameter
        """
        # 1. Get centroidal state
        x = self.get_centroidal_state()

        # 2. Compute optimal foot forces from Riccati
        u = k_t - K_t @ (x - x_ref_t)  # (12,)

        # Clip foot forces (safety, matches OCP["force_limit"])
        u = np.clip(u, -100.0, 100.0)

        # 3. Map foot forces → joint torques
        grav_comp = self.data.qfrc_bias[6:18].copy()
        q_phys = self.data.qpos[7:19].copy()
        v_phys = self.data.qvel[6:18].copy()
        q_norm = normalize_joints(q_phys)

        # Swing target in physical joint angles
        q_swing_peak = np.array([
            0.0, 1.3, -2.2,  0.0, 1.3, -2.2,
            0.0, 1.3, -2.2,  0.0, 1.3, -2.2,
        ])

        kp_swing, kd_swing = 20.0, 1.0
        w_jb = 0.1

        torques = np.zeros(12)
        forces = u.reshape(4, 3)

        for k in range(4):
            s = barrier_scales[k]
            h_frac = foot_height_frac[k]
            idx = slice(3*k, 3*(k+1))

            # Riccati forces → joint torques via J^T
            self._mujoco.mj_jacBody(
                self.model, self.data, self._jacp, self._jacr,
                self._foot_body_ids[k]
            )
            jac_leg = self._jacp[:, 6 + 3*k : 6 + 3*(k+1)]  # (3, 3)
            tau_riccati = jac_leg.T @ forces[k]

            # PD swing tracking
            q_target = _STANDING_QPOS_JOINTS[idx] + h_frac * (
                q_swing_peak[idx] - _STANDING_QPOS_JOINTS[idx]
            )
            tau_swing = kp_swing * (q_target - q_phys[idx]) - kd_swing * v_phys[idx]

            # Blend by barrier scale: stance → J^T, swing → PD
            tau = s * tau_riccati + (1.0 - s) * tau_swing

            # Gravity compensation (modulated by σ)
            tau += s * grav_comp[idx]

            # Joint-limit barrier (normalized → physical)
            q_lo = np.maximum(q_norm[idx] - _Q_NORM_MIN[idx], 1e-4)
            q_hi = np.maximum(_Q_NORM_MAX[idx] - q_norm[idx], 1e-4)
            tau_barrier_norm = w_jb * epsilon * (1.0 / q_lo - 1.0 / q_hi)
            tau += tau_barrier_norm / _Q_HALF_RANGE[idx]

            torques[idx] = tau

        torques = np.clip(torques, -_TORQUE_LIMIT, _TORQUE_LIMIT)
        self.step_torques(torques, dt_ocp)

    def get_centroidal_state(self) -> np.ndarray:
        """Extract centroidal state from MuJoCo (13,)."""
        pos = self.data.qpos[:3].copy()
        vel = self.data.qvel[:3].copy()

        # Quaternion → Rodrigues
        qw = self.data.qpos[3]
        qv = self.data.qpos[4:7].copy()
        angle = 2.0 * np.arccos(np.clip(qw, -1.0, 1.0))
        if angle > 1e-8:
            axis = qv / np.sin(angle / 2)
            phi = axis * angle
        else:
            phi = np.zeros(3)

        omega = self.data.qvel[3:6].copy()
        phase = np.array([self.data.time * ROBOT["stride_frequency"] % 1.0])

        return np.concatenate([pos, vel, phi, omega, phase])

    def get_contact_feet(self) -> np.ndarray:
        """Return binary (4,) indicating which feet are in ground contact."""
        contacts = np.zeros(4)
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            g1_body = self.model.geom_bodyid[c.geom1]
            g2_body = self.model.geom_bodyid[c.geom2]
            is_floor_1 = (c.geom1 == self._floor_geom_id)
            is_floor_2 = (c.geom2 == self._floor_geom_id)
            if not (is_floor_1 or is_floor_2):
                continue
            other_body = g2_body if is_floor_1 else g1_body
            for k, fid in enumerate(self._foot_body_ids):
                if other_body == fid:
                    contacts[k] = 1.0
        return contacts

    def simulate_trajectory(self, foot_forces: np.ndarray,
                            contact_masks: np.ndarray,
                            dt_ocp: float,
                            x0: Optional[np.ndarray] = None) -> np.ndarray:
        """Simulate a full trajectory with contact-mode-dependent foot forces.

        Args:
            foot_forces: (H, 12) foot force sequence
            contact_masks: (H, 4) binary contact masks per timestep
            dt_ocp: OCP timestep
            x0: (13,) initial centroidal state

        Returns:
            states: (H+1, 13) centroidal state trajectory
        """
        self.reset(x0)
        H = foot_forces.shape[0]
        states = np.zeros((H + 1, 13))
        states[0] = self.get_centroidal_state()
        for t in range(H):
            self.step_foot_forces(foot_forces[t], contact_masks[t], dt_ocp)
            states[t + 1] = self.get_centroidal_state()
        return states

    def evaluate_cost(self, foot_forces: np.ndarray,
                      contact_masks: np.ndarray,
                      dt_ocp: float,
                      x0: np.ndarray,
                      target_velocity: np.ndarray,
                      epsilon: float = 1.0,
                      constraints: dict = None) -> float:
        """Evaluate trajectory cost in MuJoCo simulation.

        Ground-truth cost for MPPI Boltzmann reweighting.
        Includes height and orientation log-barriers when constraints provided.
        """
        states = self.simulate_trajectory(foot_forces, contact_masks, dt_ocp, x0)
        cost = 0.0
        for t in range(foot_forces.shape[0]):
            vel_err = states[t, 3:6] - np.asarray(target_velocity)
            cost += float(np.sum(vel_err**2))
            cost += 1e-4 * float(np.sum(foot_forces[t]**2))

            if constraints is not None:
                # Height tracking (quadratic)
                z_err = states[t, 2] - constraints["z_target"]
                cost += constraints["w_height"] * float(z_err**2)

                # Height barrier (log-barrier, same ε as contact)
                pz = float(states[t, 2])
                z_lo = max(pz - constraints["z_min"], 1e-6)
                z_hi = max(constraints["z_max"] - pz, 1e-6)
                cost -= constraints["w_height_barrier"] * epsilon * (
                    np.log(z_lo) + np.log(z_hi)
                )

                # Orientation barrier (pitch/roll within ±30°)
                phi_x = float(states[t, 6])
                phi_y = float(states[t, 7])
                phi_max2 = constraints["phi_max"]**2
                ori_x = max(phi_max2 - phi_x**2, 1e-6)
                ori_y = max(phi_max2 - phi_y**2, 1e-6)
                cost -= constraints["w_ori_barrier"] * epsilon * (
                    np.log(ori_x) + np.log(ori_y)
                )

                # Joint-limit barrier
                if "w_joint_barrier" in constraints:
                    q_joints = self.data.qpos[7:19].copy()
                    q_norm = normalize_joints(q_joints)
                    q_lo = np.maximum(q_norm - _Q_NORM_MIN, 1e-4)
                    q_hi = np.maximum(_Q_NORM_MAX - q_norm, 1e-4)
                    cost -= constraints["w_joint_barrier"] * epsilon * float(
                        np.sum(np.log(q_lo) + np.log(q_hi))
                    )
        return cost
