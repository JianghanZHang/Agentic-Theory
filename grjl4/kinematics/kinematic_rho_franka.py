"""
Kinematic ρ — contact order parameter for Franka Panda.

ρ(t) measures the ratio of external (contact) force to gravitational
force on the grasped block.  It is the core observable that drives
the FSM phase transitions:

    ρ < 1  →  no firm contact (approach / retreat)
    ρ ≥ 1  →  firm contact (grasp established)

Computation:
    τ_expected = M(q)·ddq + C(q,dq)·dq + g(q)    (mj_inverse)
    τ_ext      = τ_cmd - τ_expected                (residual)
    F_contact  = J†ᵀ · τ_ext                       (project to Cartesian)
    ρ          = ‖F_contact‖ / (m_block · g)       (normalise)

The raw ρ is noisy; an EMA filter smooths it for crossing detection.
"""

import numpy as np
import mujoco


# ── Constants ──────────────────────────────────────────────────────
_G = 9.81
_ARM_NV = 7   # Franka has 7 arm DOFs in velocity space


class KinematicRho:
    """Compute and filter the contact order parameter ρ(t)."""

    def __init__(self, model: mujoco.MjModel, ee_body: str = "hand",
                 alpha: float = 0.3):
        """
        Parameters
        ----------
        model : MjModel
            The loaded MuJoCo model (franka_scene.xml).
        ee_body : str
            Name of the end-effector body for Jacobian computation.
        alpha : float
            EMA smoothing factor (0 < α ≤ 1).  Larger = less smoothing.
        """
        self.model = model
        self.ee_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY,
                                             ee_body)
        self.alpha = alpha

        # Pre-allocate Jacobian buffers (3×nv each for pos and rot)
        self._jacp = np.zeros((3, model.nv))
        self._jacr = np.zeros((3, model.nv))

        # State
        self._rho_filtered = 0.0
        self._rho_raw = 0.0

    # ── Core computation ──────────────────────────────────────────

    def compute(self, data: mujoco.MjData, m_block: float) -> float:
        """Compute raw ρ from the current MuJoCo state.

        Must be called AFTER mj_step (or mj_forward) so that
        data.qfrc_inverse, data.qfrc_actuator, etc. are current.

        Parameters
        ----------
        data : MjData
            Current simulation state.
        m_block : float
            Mass of the block being grasped (kg).

        Returns
        -------
        rho_raw : float
            Un-filtered contact order parameter.
        """
        # 1. Inverse dynamics: τ_expected = M·ddq + C·dq + g
        #    MuJoCo stores this in data.qfrc_inverse after mj_inverse.
        #    We use a scratch copy to avoid mutating the live data.
        d_inv = mujoco.MjData(self.model)
        d_inv.qpos[:] = data.qpos[:]
        d_inv.qvel[:] = data.qvel[:]
        d_inv.qacc[:] = data.qacc[:]
        mujoco.mj_inverse(self.model, d_inv)
        tau_expected = d_inv.qfrc_inverse[:_ARM_NV]

        # 2. Commanded torque (from actuators, arm joints only)
        tau_cmd = data.qfrc_actuator[:_ARM_NV]

        # 3. External torque residual
        tau_ext = tau_cmd - tau_expected

        # 4. End-effector Jacobian (positional part, arm joints only)
        mujoco.mj_jacBody(self.model, data,
                          self._jacp, self._jacr, self.ee_body_id)
        J_pos = self._jacp[:, :_ARM_NV]  # 3 × 7

        # 5. Project to Cartesian force: F = J†ᵀ · τ_ext
        #    Since J is 3×7 (more cols than rows), J† = Jᵀ(JJᵀ)⁻¹
        #    and F = J†ᵀ · τ = (JJᵀ)⁻¹ J · τ
        #    But simpler: F = pinv(Jᵀ) · τ_ext
        J_T = J_pos.T  # 7 × 3
        F_contact, _, _, _ = np.linalg.lstsq(J_T, tau_ext, rcond=None)

        # 6. Normalise
        F_norm = np.linalg.norm(F_contact)
        self._rho_raw = F_norm / (m_block * _G) if m_block > 0 else 0.0
        return self._rho_raw

    # ── EMA filter ────────────────────────────────────────────────

    def update(self, data: mujoco.MjData, m_block: float) -> float:
        """Compute ρ and apply EMA filter.  Returns filtered ρ."""
        rho_raw = self.compute(data, m_block)
        self._rho_filtered += self.alpha * (rho_raw - self._rho_filtered)
        return self._rho_filtered

    # ── Accessors ─────────────────────────────────────────────────

    @property
    def rho_raw(self) -> float:
        return self._rho_raw

    @property
    def rho_filtered(self) -> float:
        return self._rho_filtered

    def reset(self):
        """Reset filter state (call at episode start)."""
        self._rho_filtered = 0.0
        self._rho_raw = 0.0


def rho_from_contacts(model: mujoco.MjModel, data: mujoco.MjData,
                      block_body_id: int) -> float:
    """Ground-truth ρ from MuJoCo's contact solver (for verification).

    Sums all contact forces acting on the given block body and normalises
    by the block's weight.
    """
    total_force = np.zeros(3)
    for i in range(data.ncon):
        c = data.contact[i]
        geom1_body = model.geom_bodyid[c.geom1]
        geom2_body = model.geom_bodyid[c.geom2]
        if geom1_body == block_body_id or geom2_body == block_body_id:
            # Extract 6D wrench for this contact
            wrench = np.zeros(6)
            mujoco.mj_contactForce(model, data, i, wrench)
            # Contact frame normal force (first 3 components are force)
            # Rotate from contact frame to world frame
            frame = c.frame.reshape(3, 3)
            f_world = frame.T @ wrench[:3]
            if geom2_body == block_body_id:
                f_world = -f_world  # flip sign for body2
            total_force += f_world

    m_block = model.body_mass[block_body_id]
    weight = m_block * _G
    return np.linalg.norm(total_force) / weight if weight > 0 else 0.0
