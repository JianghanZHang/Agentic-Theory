"""
Analytical Spectral Gradient (Step 2d)

Replaces finite-difference spectral_gradient() with analytical gradient
via eigenvector perturbation theory:

    d lambda_1 / d q*_k = v_1^T (dL/dq*_k) v_1

where v_1 is the Fiedler eigenvector of the graph Laplacian L.

Reference: threebody.tex lines 50-55 (tidal coupling weights),
           existing graph_laplacian() in threebody_damper.py line 56.
"""

import numpy as np
from numpy.linalg import eigh, norm


def graph_laplacian_with_eigenvectors(positions, masses, G=0.5,
                                       softening=0.05):
    """Compute graph Laplacian, eigenvalues, and eigenvectors.

    Returns
    -------
    L : (n, n) array
    eigenvalues : (n,) array, ascending
    eigenvectors : (n, n) array, columns are eigenvectors
    """
    n = len(masses)
    L = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = max(norm(positions[i] - positions[j]), softening)
            w = G * masses[i] * masses[j] / d**3
            L[i, i] += w
            L[j, j] += w
            L[i, j] -= w
            L[j, i] -= w
    eigenvalues, eigenvectors = eigh(L)
    return L, eigenvalues, eigenvectors


def spectral_gradient_analytical(positions, masses, damper_idx=3,
                                  G=0.5, softening=0.05):
    """Analytical gradient of the Fiedler eigenvalue w.r.t. damper position.

    For each coordinate k of q*, computes:
        d lambda_1 / d q*_k = v_1^T (dL/dq*_k) v_1

    where dL/dq*_k involves the derivative of tidal weights:
        d w_{*j} / d q*_k = -3 G m_* m_j / |q_j - q*|^5 * (q_j - q*)_k

    Parameters
    ----------
    positions : list of (3,) arrays
    masses : list of float
    damper_idx : int
    G : float
    softening : float

    Returns
    -------
    grad : (3,) array
        Gradient of lambda_1 w.r.t. q*.
    """
    n = len(masses)
    _, eigenvalues, eigenvectors = graph_laplacian_with_eigenvectors(
        positions, masses, G, softening)

    v1 = eigenvectors[:, 1]  # Fiedler eigenvector
    lambda1 = eigenvalues[1]

    q_star = np.asarray(positions[damper_idx])
    m_star = masses[damper_idx]
    grad = np.zeros(3)

    for j in range(n):
        if j == damper_idx:
            continue

        r = np.asarray(positions[j]) - q_star
        d = max(norm(r), softening)

        # dw_{*j}/dq*  (3-vector)
        # w = G m_* m_j / d^3,  d = |q_j - q*|
        # dd/dq*_k = -(q_j - q*)_k / d = -r_k / d
        # dw/dq*_k = -3 G m_* m_j / d^4 * (dd/dq*_k)
        #          = +3 G m_* m_j / d^5 * r_k
        dw_dqstar = 3.0 * G * m_star * masses[j] / d**5 * r

        # For each coordinate k, build dL/dq*_k and compute v1^T dL v1
        # dL/dq*_k has entries:
        #   dL[*,*] += dw_k,  dL[j,j] += dw_k
        #   dL[*,j] -= dw_k,  dL[j,*] -= dw_k
        #
        # v1^T dL v1 = dw_k * (v1[*]^2 + v1[j]^2 - 2*v1[*]*v1[j])
        #            = dw_k * (v1[*] - v1[j])^2
        diff_sq = (v1[damper_idx] - v1[j])**2

        grad += dw_dqstar * diff_sq

    return grad


def spectral_gradient_finite_diff(positions, masses, damper_idx=3,
                                   G=0.5, delta=1e-4):
    """Finite-difference gradient for verification."""
    from numpy.linalg import eigvalsh

    def _lambda1(pos_list):
        n = len(masses)
        L = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = max(norm(pos_list[i] - pos_list[j]), 0.05)
                w = G * masses[i] * masses[j] / d**3
                L[i, i] += w
                L[j, j] += w
                L[i, j] -= w
                L[j, i] -= w
        return eigvalsh(L)[1]

    grad = np.zeros(3)
    for k in range(3):
        pos_plus = [p.copy() for p in positions]
        pos_minus = [p.copy() for p in positions]
        pos_plus[damper_idx][k] += delta
        pos_minus[damper_idx][k] -= delta
        grad[k] = (_lambda1(pos_plus) - _lambda1(pos_minus)) / (2 * delta)
    return grad


def verify_gradient(positions=None, masses=None, G=0.5):
    """Verify analytical gradient against finite differences.

    Returns
    -------
    analytical : (3,) array
    numerical : (3,) array
    relative_error : float
    """
    if positions is None:
        positions = [
            np.array([1.5, 0.0, 0.0]),
            np.array([-0.75, 1.3, 0.0]),
            np.array([-0.75, -1.3, 0.0]),
            np.array([0.0, 0.0, 0.3]),
        ]
    if masses is None:
        masses = [1.0, 1.0, 1.0, 0.5]

    analytical = spectral_gradient_analytical(positions, masses, G=G)
    numerical = spectral_gradient_finite_diff(positions, masses, G=G)

    rel_err = norm(analytical - numerical) / max(norm(numerical), 1e-10)
    return analytical, numerical, rel_err
