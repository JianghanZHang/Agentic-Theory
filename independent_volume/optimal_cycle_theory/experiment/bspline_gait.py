"""Log-space periodic cubic B-spline contact mode parameterization.

Action-cycle → state-cycle composition:
    B-spline coeffs c_k ∈ ℝ → β_k(t) = Spline(c_k, t) → σ_k = sigmoid(β_k)
        → h_k = ε·exp(-β_k) → barrier forces → Riccati → trajectory

The parameterization lives in the Lie algebra (ℝ, unconstrained, additive).
The contact mode σ_k lives in the Lie group ((0,1), constrained, multiplicative).
The sigmoid IS the exponential map.

Reference: Alvarez-Padilla et al. (arXiv 2409.10469) use cubic spline
action sampling with 4 knots over 40-step horizon in their MPPI.
"""

import numpy as np
from scipy.interpolate import CubicSpline

from config import MPPI


def _sigmoid(x):
    """Numerically stable sigmoid."""
    return np.where(x >= 0,
                    1.0 / (1.0 + np.exp(-x)),
                    np.exp(x) / (1.0 + np.exp(x)))


def periodic_bspline_logcontact(control_points, n_steps, T_stride, epsilon=1.0):
    """Evaluate periodic cubic B-spline in log-contact space.

    Args:
        control_points: (4, n_knots) B-spline coefficients in ℝ (log space).
            c[k, j] = foot k's log-contact mode at knot j.
        n_steps: number of output timesteps
        T_stride: stride period (seconds)
        epsilon: barrier parameter (for computing foot heights)

    Returns:
        beta: (n_steps, 4)    log-contact mode β_k(t) ∈ ℝ
        sigma: (n_steps, 4)   contact mode σ_k(t) ∈ (0,1)
        heights: (n_steps, 4) foot heights h_k(t) ≥ 0
    """
    n_feet, n_knots = control_points.shape
    knot_times = np.linspace(0, T_stride, n_knots)
    dt = T_stride / n_steps
    eval_times = np.arange(n_steps) * dt

    beta = np.zeros((n_steps, n_feet))
    for k in range(n_feet):
        cs = CubicSpline(knot_times, control_points[k], bc_type='not-a-knot')
        beta[:, k] = cs(eval_times)

    # Action-cycle → state-cycle: sigmoid is the exponential map
    sigma = _sigmoid(beta)
    # h_k = ε · exp(-β_k)  (from σ = ε/(h+ε) → h = ε(σ⁻¹ - 1) = ε·e^{-β})
    heights = epsilon * np.exp(-beta)

    return beta, sigma, heights


def sample_logspace_gaits(n_knots, N_samples, T_stride, rng, beta_scale=None):
    """Sample N gait schedules as log-space B-spline coefficients.

    Prior: Gaussian noise in ℝ^{4×n_knots} with trot-like phase structure.
    β > 0 → swing (σ > 0.5); β < 0 → stance (σ < 0.5).

    Trot prior: FL/RR are in anti-phase with FR/RL.
    Each foot has a sinusoidal mean with phase offset, plus Gaussian noise.

    Args:
        n_knots: control points per foot
        N_samples: number of samples
        T_stride: stride period
        rng: numpy random generator
        beta_scale: std dev of coefficient noise (default from config)

    Returns:
        control_points: (N_samples, 4, n_knots) in ℝ
    """
    if beta_scale is None:
        beta_scale = MPPI.get("beta_scale", 3.0)

    cp = np.zeros((N_samples, 4, n_knots))

    # Trot phase offsets: FL=0, FR=π, RL=π, RR=0 (diagonal pairs in sync)
    trot_offsets = np.array([0.0, np.pi, np.pi, 0.0])
    knot_phases = np.linspace(0, 2 * np.pi, n_knots, endpoint=False)

    for i in range(N_samples):
        for k in range(4):
            # Sinusoidal mean: positive during swing, negative during stance
            mean = beta_scale * 0.5 * np.sin(knot_phases + trot_offsets[k])
            noise = rng.normal(0, beta_scale * 0.3, size=n_knots)
            cp[i, k] = mean + noise

    return cp


# ── Backward compatibility wrappers ──

def periodic_bspline_height(control_points, n_steps, T_stride):
    """Legacy wrapper: evaluate h_k-space B-spline (non-negative clamp).

    Used when control_points are in the old h_k ≥ 0 parameterization.
    """
    n_feet, n_knots = control_points.shape
    knot_times = np.linspace(0, T_stride, n_knots, endpoint=False)
    knot_times_ext = np.concatenate([knot_times, [T_stride]])
    dt = T_stride / n_steps
    eval_times = np.arange(n_steps) * dt

    heights = np.zeros((n_steps, n_feet))
    for k in range(n_feet):
        cp_ext = np.concatenate([control_points[k], [control_points[k, 0]]])
        cs = CubicSpline(knot_times_ext, cp_ext, bc_type='periodic')
        heights[:, k] = np.maximum(cs(eval_times), 0.0)

    return heights


def sample_bspline_gaits(n_knots, N_samples, T_stride, rng,
                         h_max=0.08, duty_factor=0.5):
    """Legacy wrapper: sample h_k-space B-spline coefficients."""
    n_stance = max(1, int(n_knots * duty_factor))
    n_swing = n_knots - n_stance
    cp = np.zeros((N_samples, 4, n_knots))

    for i in range(N_samples):
        for k in range(4):
            offset = rng.integers(0, n_knots)
            for j in range(n_swing):
                idx = (offset + n_stance + j) % n_knots
                cp[i, k, idx] = rng.uniform(0.01, h_max)

    return cp
