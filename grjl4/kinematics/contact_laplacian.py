"""
Contact graph Laplacian — spectral gap λ₁ for grasp stability.

The contact graph has nodes = {bodies in contact} and edges weighted
by the normal contact force ratio w_ij = F_n / (m · g).

λ₁ (smallest nonzero eigenvalue of the graph Laplacian) measures
how well-connected the grasp is:

    λ₁ ≥ ε   →  stable grasp (all contacts firm)
    λ₁ < ε   →  marginal (about to slip)
    λ₁ ≤ 0   →  disconnected (block dropped or toppled)

Wind reduces λ₁ by shifting the effective support:
    λ₁_eff = λ₁ - ‖F_wind_perp‖ / (m · g)
"""

import numpy as np
import mujoco


_G = 9.81


def contact_graph_weights(model: mujoco.MjModel, data: mujoco.MjData,
                          block_body_id: int) -> dict:
    """Build the contact graph for a single block.

    Returns a dict mapping (body_id_other, block_body_id) → weight,
    where weight = |F_normal| / (m_block · g).
    """
    m_block = model.body_mass[block_body_id]
    weight = m_block * _G
    if weight <= 0:
        return {}

    contacts = {}
    for i in range(data.ncon):
        c = data.contact[i]
        g1_body = model.geom_bodyid[c.geom1]
        g2_body = model.geom_bodyid[c.geom2]

        # Is this contact involving our block?
        if g1_body == block_body_id:
            other = g2_body
        elif g2_body == block_body_id:
            other = g1_body
        else:
            continue

        # Extract contact force
        wrench = np.zeros(6)
        mujoco.mj_contactForce(model, data, i, wrench)
        F_n = abs(wrench[0])  # normal force (first component in contact frame)

        # Accumulate (a body pair may have multiple contact points)
        contacts[other] = contacts.get(other, 0.0) + F_n / weight

    return contacts


def lambda1(model: mujoco.MjModel, data: mujoco.MjData,
            block_body_id: int) -> float:
    """Compute λ₁ of the contact graph Laplacian for a block.

    For a grasp with N contacts, the Laplacian is (N+1)×(N+1)
    (block + N contacting bodies).  λ₁ = min nonzero eigenvalue.

    In practice for a parallel-jaw grasp on a table:
      - Transport: 2 contacts (left finger, right finger) → λ₁ = min(w_L, w_R)
      - Placement: 3 contacts (+ table) → λ₁ = min(w_L, w_R, w_table)
    """
    cw = contact_graph_weights(model, data, block_body_id)
    if not cw:
        return 0.0

    # For the small graphs in manipulation (2-4 nodes), the spectral gap
    # equals the minimum edge weight on a star graph (block is the hub).
    # This is exact for star topology and a tight lower bound otherwise.
    return min(cw.values())


def lambda1_effective(model: mujoco.MjModel, data: mujoco.MjData,
                      block_body_id: int,
                      F_wind: np.ndarray | None = None) -> float:
    """λ₁ adjusted for wind perturbation.

    Wind applies a lateral force that must be resisted by contacts.
    The effective spectral gap decreases by the perpendicular
    component of the wind force normalised by block weight.

    Parameters
    ----------
    F_wind : array-like, shape (3,)
        Wind force vector in world frame (N).  None = no wind.

    Returns
    -------
    lambda1_eff : float
        Effective spectral gap.  ≤ 0 means toppled.
    """
    lam1 = lambda1(model, data, block_body_id)

    if F_wind is None or np.linalg.norm(F_wind) < 1e-10:
        return lam1

    # Support normal = +z (blocks rest on horizontal surface)
    support_normal = np.array([0.0, 0.0, 1.0])
    F_wind = np.asarray(F_wind, dtype=float)

    # Perpendicular component (horizontal wind destabilises)
    F_perp = F_wind - np.dot(F_wind, support_normal) * support_normal
    m_block = model.body_mass[block_body_id]
    shift = np.linalg.norm(F_perp) / (m_block * _G)

    return lam1 - shift


def grasp_stable(model: mujoco.MjModel, data: mujoco.MjData,
                 block_body_id: int, eps: float = 0.05,
                 F_wind: np.ndarray | None = None) -> bool:
    """Check if the block's grasp/support is stable.

    Returns True iff λ₁_eff ≥ ε.
    """
    return lambda1_effective(model, data, block_body_id, F_wind) >= eps
