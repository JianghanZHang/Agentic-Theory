"""
Kinematic ρ — GRJL 3.0 (force elimination)

ρ is computed from kinematics (q, q̇, q̈) alone.
Force never enters the interface.

Three entry points:
    kinematic_rho_threebody  — tidal coupling ratio (positions only)
    kinematic_rho_dribble    — |q̈_z/g + 1| (velocity differences only)
    kinematic_rho_general    — M(q)q̈ decomposition (any EL system)
"""

import numpy as np


# ── Three-body (Backend 1) ────────────────────────────────

def kinematic_rho_threebody(positions, masses, damper_idx, body_idx):
    """ρ from positions only — tidal coupling ratio.

    Identical to tidal_rho() in grjl2/order_parameter.py.
    Already force-free: ρ = w_damper / w_natural, where weights
    are gravitational tidal couplings G·m_i·m_j / ||r_ij||³.

    Parameters
    ----------
    positions : (n, 3) array — body positions
    masses : (n,) array — body masses
    damper_idx : int — index of the damper body
    body_idx : int — index of the target body

    Returns
    -------
    rho : float — order parameter (tidal ratio)
    """
    G = 1.0  # gravitational constant (normalised)
    n = len(masses)

    # Damper-body tidal weight
    r_dj = positions[damper_idx] - positions[body_idx]
    dist_dj = np.linalg.norm(r_dj)
    w_damper = G * masses[damper_idx] * masses[body_idx] / max(dist_dj**3, 1e-12)

    # Body-body tidal weights (edges not involving damper)
    body_indices = [i for i in range(n) if i != damper_idx]
    w_body = []
    for i in range(len(body_indices)):
        for j in range(i + 1, len(body_indices)):
            bi, bj = body_indices[i], body_indices[j]
            r_ij = positions[bi] - positions[bj]
            dist_ij = np.linalg.norm(r_ij)
            w_ij = G * masses[bi] * masses[bj] / max(dist_ij**3, 1e-12)
            w_body.append(w_ij)

    w_natural = np.mean(w_body) if w_body else 1e-12
    rho = w_damper / max(w_natural, 1e-12)
    return rho


# ── Dribble (Backend 2) ──────────────────────────────────

def kinematic_rho_dribble(vz, vz_prev, dt, g=9.81):
    """ρ = |q̈_z/g + 1| — pure kinematics, no force sensor.

    Derivation:
        Newton:    F_net = m·q̈
        Decompose: F_net = F_gravity + F_contact
                         = -m·g     + F_contact
        So:        F_contact = m·(q̈ + g)
        Therefore: ρ = |F_contact|/(m·g) = |q̈/g + 1|

    Free fall:     q̈ = -g  →  ρ = |-1 + 1| = 0   ✓
    Static:        q̈ = 0   →  ρ = |0 + 1|  = 1   ✓
    Hand strikes:  q̈ > 0   →  ρ = |q̈/g+1| > 1   ✓

    Parameters
    ----------
    vz : float — current vertical velocity of ball
    vz_prev : float — previous vertical velocity (one timestep ago)
    dt : float — timestep
    g : float — gravitational acceleration magnitude (positive)

    Returns
    -------
    rho : float — order parameter (kinematic)
    """
    if dt < 1e-12:
        return 0.0
    qddot_z = (vz - vz_prev) / dt
    rho = abs(qddot_z / g + 1.0)
    return rho


# ── General EL system ────────────────────────────────────

def kinematic_rho_general(M_q, qddot, gravity_proj, contact_proj):
    """ρ from M(q)q̈ decomposition for any EL system.

    Given the mass matrix M(q) and acceleration q̈, compute
    τ = M(q)q̈ and decompose into gravity and contact components.

    Parameters
    ----------
    M_q : (n, n) array — mass-inertia matrix at current config
    qddot : (n,) array — generalised acceleration
    gravity_proj : callable — projects τ onto gravity component
    contact_proj : callable — projects τ onto contact component

    Returns
    -------
    rho : float — |τ_contact| / |τ_gravity|
    """
    tau = M_q @ qddot
    F_gravity = np.linalg.norm(gravity_proj(tau))
    F_contact = np.linalg.norm(contact_proj(tau))
    if F_gravity < 1e-12:
        return float('inf') if F_contact > 1e-12 else 0.0
    return F_contact / F_gravity


# ── Smoothed kinematic ρ (for noisy q̈) ───────────────────

class KinematicRhoFilter:
    """Exponential moving average filter for kinematic ρ.

    Finite-differencing q̇ to get q̈ amplifies noise.  This filter
    smooths the result while preserving the phase transitions
    (ρ crossing 1.0).
    """

    def __init__(self, alpha=0.3):
        """
        Parameters
        ----------
        alpha : float — smoothing factor (0 = no update, 1 = no smoothing)
        """
        self.alpha = alpha
        self.rho_smooth = 0.0

    def update(self, rho_raw):
        """Update with new raw ρ, return smoothed value."""
        self.rho_smooth = self.alpha * rho_raw + (1 - self.alpha) * self.rho_smooth
        return self.rho_smooth

    def reset(self):
        self.rho_smooth = 0.0


# ── Verification ─────────────────────────────────────────

def verify_kinematic_rho():
    """Verify kinematic ρ matches expected values."""
    g = 9.81

    # Free fall: q̈ = -g
    vz_prev = 0.0
    vz = -g * 0.002  # after 1 timestep at dt=0.002
    rho = kinematic_rho_dribble(vz, vz_prev, dt=0.002, g=g)
    assert abs(rho) < 0.01, f"Free fall: expected ρ≈0, got {rho}"

    # Static: q̈ = 0
    rho = kinematic_rho_dribble(0.0, 0.0, dt=0.002, g=g)
    assert abs(rho - 1.0) < 0.01, f"Static: expected ρ≈1, got {rho}"

    # Upward acceleration: q̈ = +g (hand strikes with force = 2mg)
    vz_prev = 0.0
    vz = g * 0.002
    rho = kinematic_rho_dribble(vz, vz_prev, dt=0.002, g=g)
    assert abs(rho - 2.0) < 0.01, f"Strike: expected ρ≈2, got {rho}"

    print("  kinematic_rho verification: PASS")
    print(f"    Free fall: ρ = {kinematic_rho_dribble(-g*0.002, 0.0, 0.002, g):.4f} (expected 0)")
    print(f"    Static:    ρ = {kinematic_rho_dribble(0.0, 0.0, 0.002, g):.4f} (expected 1)")
    print(f"    Strike 2g: ρ = {kinematic_rho_dribble(g*0.002, 0.0, 0.002, g):.4f} (expected 2)")


if __name__ == '__main__':
    verify_kinematic_rho()
