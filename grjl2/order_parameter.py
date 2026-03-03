"""
Order Parameter ρ — The heart of GRJL 2.0

Everything in 2.0 is a smooth function of the single scalar:

    ρ = F_repulsion / F_attraction

Edge weight w(ρ) is a C∞ sigmoid composition with closed-form derivative.
No discrete MODE_* enums, no if/else chains.

Reference: threebody.tex eq:3b-rho.
"""

import numpy as np
from numpy.linalg import eigvalsh


# ── Core computations ──────────────────────────────────────

def compute_rho(F_repulsion, F_attraction, eps=1e-12):
    """Compute the order parameter ρ = F_repulsion / F_attraction.

    Parameters
    ----------
    F_repulsion : float
        Magnitude of repulsive / contact / constraint force.
    F_attraction : float
        Magnitude of attractive / gravitational / weight force.
    eps : float
        Regulariser to avoid division by zero.

    Returns
    -------
    rho : float
        Non-negative scalar.  ρ < 1 → separating, ρ = 1 → sliding,
        ρ > 1 → sticking, ρ → ∞ → clamped.
    """
    return F_repulsion / max(F_attraction, eps)


def _sigmoid(x):
    """Numerically stable logistic sigmoid."""
    x = np.atleast_1d(np.asarray(x, dtype=float))
    out = np.empty_like(x)
    pos = x >= 0
    neg = ~pos
    if np.any(pos):
        out[pos] = 1.0 / (1.0 + np.exp(-x[pos]))
    if np.any(neg):
        exp_x = np.exp(x[neg])
        out[neg] = exp_x / (1.0 + exp_x)
    return float(out[0]) if out.size == 1 else out


def _sigmoid_deriv(x):
    """σ'(x) = σ(x)(1 − σ(x))."""
    s = _sigmoid(x)
    return s * (1.0 - s)


def smooth_edge_weight(rho, k_n=1.0, k_t=1.0, mu=0.5, beta=20.0):
    """Smooth edge weight as a function of ρ.

    w(ρ) = w_slide · σ(β(ρ−1)) + (w_stick − w_slide) · σ(β(ρ−1.1))

    Parameters
    ----------
    rho : float or array
        Order parameter value(s).
    k_n : float
        Normal stiffness.
    k_t : float
        Tangential stiffness.
    mu : float
        Friction coefficient.
    beta : float
        Sigmoid sharpness (≈20 for near-step transition).

    Returns
    -------
    w : float or array
        Edge weight, C∞ in ρ.
    """
    rho = np.asarray(rho, dtype=float)
    w_slide = k_n * (1.0 + mu)
    w_stick = k_n + k_t

    w = w_slide * _sigmoid(beta * (rho - 1.0)) \
        + (w_stick - w_slide) * _sigmoid(beta * (rho - 1.1))
    return float(w) if np.ndim(w) == 0 else w


def d_smooth_edge_weight_d_rho(rho, k_n=1.0, k_t=1.0, mu=0.5, beta=20.0):
    """Analytical derivative dw/dρ.

    dw/dρ = β · w_slide · σ'(β(ρ−1))
          + β · (w_stick − w_slide) · σ'(β(ρ−1.1))

    Returns
    -------
    dw : float or array
    """
    rho = np.asarray(rho, dtype=float)
    w_slide = k_n * (1.0 + mu)
    w_stick = k_n + k_t

    dw = beta * w_slide * _sigmoid_deriv(beta * (rho - 1.0)) \
        + beta * (w_stick - w_slide) * _sigmoid_deriv(beta * (rho - 1.1))
    return float(dw) if np.ndim(dw) == 0 else dw


def verify_smooth_weight(k_n=1.0, k_t=1.0, mu=0.5, beta=20.0,
                         rho_test=None, delta=1e-6):
    """Verify analytical dw/dρ against finite differences.

    Returns
    -------
    max_rel_error : float
        Maximum relative error across test points.
    passed : bool
        True if max_rel_error < 1e-6.
    """
    if rho_test is None:
        rho_test = np.linspace(0.0, 3.0, 200)
    rho_test = np.asarray(rho_test, dtype=float)

    # Analytical
    dw_analytical = d_smooth_edge_weight_d_rho(
        rho_test, k_n, k_t, mu, beta)

    # Finite difference
    w_plus = smooth_edge_weight(rho_test + delta, k_n, k_t, mu, beta)
    w_minus = smooth_edge_weight(rho_test - delta, k_n, k_t, mu, beta)
    dw_numerical = (w_plus - w_minus) / (2.0 * delta)

    # Relative error (skip near-zero derivatives where ratio is ill-defined)
    mask = np.abs(dw_analytical) > 0.01
    if not np.any(mask):
        return 0.0, True

    rel_err = np.abs(dw_analytical[mask] - dw_numerical[mask]) / \
        np.abs(dw_analytical[mask])
    max_rel_error = float(np.max(rel_err))
    return max_rel_error, max_rel_error < 1e-6


# ── Graph Laplacian from ρ ─────────────────────────────────

def build_laplacian_from_rho(rho_pairs, n_bodies, k_n=1.0, k_t=1.0,
                              mu=0.5, beta=20.0):
    """Build graph Laplacian from pairwise ρ values.

    Parameters
    ----------
    rho_pairs : dict
        Maps (i, j) tuples (i < j) to ρ values.
    n_bodies : int
        Number of nodes.
    k_n, k_t, mu, beta : float
        Parameters for smooth_edge_weight.

    Returns
    -------
    L : (n_bodies, n_bodies) array
        Graph Laplacian.
    lambda1 : float
        Fiedler eigenvalue.
    weights : dict
        Maps (i, j) to computed edge weight.
    """
    L = np.zeros((n_bodies, n_bodies))
    weights = {}

    for (i, j), rho in rho_pairs.items():
        w = smooth_edge_weight(rho, k_n, k_t, mu, beta)
        weights[(i, j)] = w
        L[i, i] += w
        L[j, j] += w
        L[i, j] -= w
        L[j, i] -= w

    evals = eigvalsh(L)
    lambda1 = float(evals[1]) if n_bodies > 1 else 0.0
    return L, lambda1, weights


# ── Tidal ρ for gravity systems ────────────────────────────

def tidal_rho(positions, masses, damper_idx, body_idx,
              G=0.5, softening=0.05):
    """Compute ρ for a damper–body pair in a gravitational system.

    ρ = w_damper_body / w_natural

    where:
    - w_damper_body = tidal weight of the damper–body edge
    - w_natural = mean tidal weight of body–body edges

    ρ > 1 means the damper's coupling to this body exceeds the
    natural body-body coupling → sticking regime.
    ρ < 1 means the damper is losing authority → separating.

    Parameters
    ----------
    positions : list of (3,) arrays
    masses : list of float
    damper_idx : int
    body_idx : int
    G : float
    softening : float

    Returns
    -------
    rho : float
    """
    from numpy.linalg import norm

    n = len(masses)
    q_d = np.asarray(positions[damper_idx])
    q_b = np.asarray(positions[body_idx])
    m_d = masses[damper_idx]
    m_b = masses[body_idx]

    # Tidal weight of damper-body edge: G m_d m_b / d^3
    d_db = max(norm(q_d - q_b), softening)
    w_damper = G * m_d * m_b / d_db**3

    # Mean tidal weight of body-body edges (excluding damper)
    w_sum = 0.0
    n_pairs = 0
    for i in range(n):
        if i == damper_idx:
            continue
        for j in range(i + 1, n):
            if j == damper_idx:
                continue
            d_ij = max(norm(np.asarray(positions[i]) -
                           np.asarray(positions[j])), softening)
            w_sum += G * masses[i] * masses[j] / d_ij**3
            n_pairs += 1

    w_natural = w_sum / max(n_pairs, 1)
    w_natural = max(w_natural, 1e-12)
    return w_damper / w_natural


if __name__ == '__main__':
    # Self-test
    err, passed = verify_smooth_weight()
    print(f"dw/dρ verification: max_rel_error = {err:.2e}, "
          f"{'PASS' if passed else 'FAIL'}")

    # Quick ρ sweep
    rhos = np.linspace(0, 3, 7)
    for r in rhos:
        w = smooth_edge_weight(r)
        dw = d_smooth_edge_weight_d_rho(r)
        print(f"  ρ = {r:.1f}  w = {w:.4f}  dw/dρ = {dw:.4f}")
