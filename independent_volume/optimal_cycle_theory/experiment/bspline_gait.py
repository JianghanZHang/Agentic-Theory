"""Periodic cubic B-spline foot height parameterization.

Replaces the rigid sinusoidal foot height schedule with a periodic cubic
B-spline.  The spline parameterizes the *smooth part* (foot height h_k(t)),
and the barrier handles the *non-smooth part* (contact mode sigma_k).

Composition:
    spline coeffs c_k -> h_k(t) = Spline(c_k, t) -> lambda_k = eps/h_k
        -> sigma_k -> K_p(sigma_k) -> tau

Reference: Alvarez-Padilla et al. (arXiv 2409.10469) use cubic spline
action sampling with 4 knots over 40-step horizon in their MPPI.
"""

import numpy as np
from scipy.interpolate import CubicSpline


def periodic_bspline_height(control_points, n_steps, T_stride):
    """Evaluate periodic cubic B-spline foot height schedule.

    Args:
        control_points: (4, n_knots) spline coefficients per foot.
            c[k, j] = foot k's height at knot j.
        n_steps: number of output timesteps
        T_stride: stride period (seconds)

    Returns:
        heights: (n_steps, 4) foot heights, non-negative
    """
    n_feet, n_knots = control_points.shape
    # Knot times: evenly spaced within one stride
    knot_times = np.linspace(0, T_stride, n_knots, endpoint=False)
    # Append wrap-around for periodicity
    knot_times_ext = np.concatenate([knot_times, [T_stride]])
    dt = T_stride / n_steps
    eval_times = np.arange(n_steps) * dt

    heights = np.zeros((n_steps, n_feet))
    for k in range(n_feet):
        cp_ext = np.concatenate([control_points[k], [control_points[k, 0]]])
        cs = CubicSpline(knot_times_ext, cp_ext, bc_type='periodic')
        heights[:, k] = np.maximum(cs(eval_times), 0.0)  # non-negative

    return heights


def sample_bspline_gaits(n_knots, N_samples, T_stride, rng,
                         h_max=0.08, duty_factor=0.5):
    """Sample N gait schedules as B-spline control points.

    Prior: each foot has n_knots control points.
    ~duty_factor fraction should be zero (stance).
    Remaining are positive (swing), sampled from half-normal.

    Args:
        n_knots: control points per foot
        N_samples: number of samples
        T_stride: stride period
        rng: numpy random generator
        h_max: maximum swing height
        duty_factor: fraction of stride in stance

    Returns:
        control_points: (N_samples, 4, n_knots)
    """
    n_stance = max(1, int(n_knots * duty_factor))
    n_swing = n_knots - n_stance
    cp = np.zeros((N_samples, 4, n_knots))

    for i in range(N_samples):
        for k in range(4):
            # Random phase offset for this foot
            offset = rng.integers(0, n_knots)
            # Swing knots get positive heights
            for j in range(n_swing):
                idx = (offset + n_stance + j) % n_knots
                cp[i, k, idx] = rng.uniform(0.01, h_max)
            # Stance knots stay at 0

    return cp
