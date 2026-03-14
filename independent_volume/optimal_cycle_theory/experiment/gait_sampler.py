"""Student-t mollifier on T^3 for gait phase sampling.

The gait space is T^3: three phase offsets (phi_FL, phi_RL, phi_RR)
relative to FR (leg 1, fixed at phase 0). Each phi_k in [0, 1) encodes
the fraction of a stride period by which leg k leads FR.

Student-t_nu on T^3 interpolates:
  nu=1 (Cauchy): maximum exploration, H(f) ~ infinity
  nu→∞ (Gaussian): heat kernel on T^3, H(f) → 0

The convergence student-t → Gaussian IS the re-cycle:
  holonomy H(f_{t_nu}) = O(1/nu)

Wrapping: sample from R^3, then wrap onto [0,1)^3. For the torus this is
exact (quotient map). The wrapped student-t is the periodic extension.
"""

from typing import Tuple

import jax
import jax.numpy as jnp
import numpy as np
from scipy.stats import multivariate_t

from config import ROBOT


# ── Known gait phase patterns (for reference / validation) ──
KNOWN_GAITS = {
    "trot":     jnp.array([0.5, 0.5, 0.0]),  # diagonal pairs alternate
    "pace":     jnp.array([0.5, 0.0, 0.5]),  # lateral pairs alternate
    "bound":    jnp.array([0.0, 0.5, 0.5]),  # front/back pairs alternate
    "walk":     jnp.array([0.5, 0.25, 0.75]),  # sequential footfall
    "pronk":    jnp.array([0.0, 0.0, 0.0]),  # all feet together
}


def sample_student_t_torus(nu: float, mu: jnp.ndarray, Sigma: jnp.ndarray,
                           N: int, rng_key: jax.Array) -> jnp.ndarray:
    """Sample N points from wrapped student-t_nu on T^3.

    Args:
        nu: degrees of freedom (nu=1: Cauchy, nu→∞: Gaussian)
        mu: (3,) center on T^3
        Sigma: (3,3) scale matrix
        N: number of samples
        rng_key: JAX PRNG key

    Returns:
        phis: (N, 3) samples on [0, 1)^3
    """
    # Use scipy for multivariate-t sampling (JAX doesn't have it natively)
    seed = int(jax.random.bits(rng_key))
    rng = np.random.default_rng(seed)
    rv = multivariate_t(
        loc=np.array(mu),
        shape=np.array(Sigma),
        df=nu,
    )
    samples = rv.rvs(size=N, random_state=rng)
    # Wrap onto T^3 = [0, 1)^3
    return jnp.array(samples % 1.0)


def decode_gait(phi: jnp.ndarray, beta: float,
                horizon: int, dt: float) -> jnp.ndarray:
    """Convert gait phase offsets → contact sequence.

    Leg 0 (FR) has phase 0. Legs 1,2,3 (FL,RL,RR) have phases phi[0..2].
    A leg is in stance when its phase-in-cycle < beta (duty factor).

    Args:
        phi: (3,) phase offsets of FL, RL, RR relative to FR
        beta: duty factor (fraction of stride in stance)
        horizon: number of OCP timesteps
        dt: OCP timestep

    Returns:
        contacts: (horizon+1, 4) binary contact matrix
                  columns: [FR, FL, RL, RR]
    """
    stride_period = ROBOT["stride_period"]
    phases = jnp.array([0.0, phi[0], phi[1], phi[2]])  # FR, FL, RL, RR
    t_steps = jnp.arange(horizon + 1) * dt
    cycle_pos = (t_steps[:, None] / stride_period + phases[None, :]) % 1.0
    contacts = (cycle_pos < beta).astype(jnp.float32)
    return contacts


def entropy_empirical(weights: jnp.ndarray) -> float:
    """Shannon entropy of normalized weight vector.

    H = -sum(w_i log w_i)
    Maximum H = log(N) when uniform.
    Minimum H = 0 when concentrated on single sample.
    """
    w = jnp.clip(weights, 1e-30, None)
    return -jnp.sum(w * jnp.log(w))


def effective_sample_size(weights: jnp.ndarray) -> float:
    """ESS = 1 / sum(w_i^2). Ranges from 1 (degenerate) to N (uniform)."""
    return 1.0 / jnp.sum(weights**2)


def weighted_circular_mean(phis: jnp.ndarray,
                           weights: jnp.ndarray) -> jnp.ndarray:
    """Weighted Frechet mean on T^3 via circular statistics.

    Args:
        phis: (N, 3) phase samples on [0, 1)^3
        weights: (N,) normalized weights

    Returns:
        mu: (3,) weighted circular mean on [0, 1)^3
    """
    sin_mean = jnp.sum(weights[:, None] * jnp.sin(2 * jnp.pi * phis), axis=0)
    cos_mean = jnp.sum(weights[:, None] * jnp.cos(2 * jnp.pi * phis), axis=0)
    return jnp.arctan2(sin_mean, cos_mean) / (2 * jnp.pi) % 1.0


def weighted_circular_variance(phis: jnp.ndarray,
                               weights: jnp.ndarray) -> jnp.ndarray:
    """Weighted circular variance on T^3.

    V = 1 - |mean resultant vector|. V=0 when concentrated, V=1 when uniform.

    Returns:
        var: (3,) circular variance per dimension
    """
    sin_mean = jnp.sum(weights[:, None] * jnp.sin(2 * jnp.pi * phis), axis=0)
    cos_mean = jnp.sum(weights[:, None] * jnp.cos(2 * jnp.pi * phis), axis=0)
    R = jnp.sqrt(sin_mean**2 + cos_mean**2)
    return 1.0 - R


def contact_mask_to_foot_forces_reference(contact_mask: jnp.ndarray,
                                          mass: float) -> jnp.ndarray:
    """Generate reference foot forces for a given contact mask.

    Stance feet share body weight equally in z. Swing feet have zero force.

    Args:
        contact_mask: (4,) binary
        mass: robot mass

    Returns:
        ref_forces: (12,) foot force reference [f0_xyz, f1_xyz, f2_xyz, f3_xyz]
    """
    n_stance = jnp.sum(contact_mask)
    # Avoid division by zero when no feet in contact
    n_stance = jnp.maximum(n_stance, 1.0)
    fz_per_foot = mass * 9.81 / n_stance
    forces = jnp.zeros(12)
    for k in range(4):
        forces = forces.at[3*k + 2].set(contact_mask[k] * fz_per_foot)
    return forces


# ── Barrier-smoothed contact (replaces binary contact_mask) ──

def foot_height_schedule(phi: jnp.ndarray, beta: float,
                         horizon: int, dt: float,
                         h_max: float = None) -> jnp.ndarray:
    """Convert gait phase → continuous foot height schedule.

    Implements eq. (foot-height) from the paper:
    h_k(t; φ) = h_max * (1/2 - 1/2 cos(2π [swing_frac])) during swing
    h_k = 0 during stance

    Args:
        phi: (3,) phase offsets of FL, RL, RR relative to FR
        beta: duty factor (fraction of stride in stance)
        horizon: number of OCP timesteps
        dt: OCP timestep
        h_max: maximum swing height (default from config)

    Returns:
        heights: (horizon+1, 4) continuous foot heights ≥ 0
    """
    if h_max is None:
        h_max = ROBOT["swing_height"]
    stride_period = ROBOT["stride_period"]
    phases = jnp.array([0.0, phi[0], phi[1], phi[2]])  # FR, FL, RL, RR
    t_steps = jnp.arange(horizon + 1) * dt
    cycle_pos = (t_steps[:, None] / stride_period + phases[None, :]) % 1.0

    # Stance: cycle_pos < beta → h = 0
    # Swing:  cycle_pos >= beta → smooth cosine lift
    swing_frac = jnp.clip((cycle_pos - beta) / (1.0 - beta), 0.0, 1.0)
    heights = h_max * 0.5 * (1.0 - jnp.cos(2 * jnp.pi * swing_frac))
    # Zero during stance
    heights = jnp.where(cycle_pos < beta, 0.0, heights)
    return heights


def barrier_contact_force(heights: jnp.ndarray, epsilon: float,
                          mass: float,
                          h_min: float = 1e-4) -> jnp.ndarray:
    """Barrier-smoothed contact force: distribute mg proportional to λ_k.

    Each foot gets fz_k = (λ_k / Σ_j λ_j) * mg, where λ_k = ε / h_k.
    Total vertical force sums to mg (supporting body weight).
    Stance feet (h ≈ 0) get most of the weight; swing feet get little.

    Args:
        heights: (..., 4) foot heights
        epsilon: barrier/temperature parameter
        mass: robot mass (for force scaling)
        h_min: floor to prevent division by zero

    Returns:
        forces_z: (..., 4) vertical contact forces per foot
    """
    h_clamped = jnp.maximum(heights, h_min)
    lam = epsilon / h_clamped  # (..., 4) barrier forces
    lam_sum = jnp.sum(lam, axis=-1, keepdims=True)  # (..., 1)
    lam_sum = jnp.maximum(lam_sum, 1e-10)  # prevent /0
    # Distribute body weight proportional to barrier activation
    return (lam / lam_sum) * mass * 9.81


def barrier_force_scale(heights: jnp.ndarray, epsilon: float,
                        h_min: float = 1e-4) -> jnp.ndarray:
    """Sigmoid-like force activation: scale_k = λ_k / (λ_k + 1).

    Continuous replacement for binary contact_mask.
    ≈ 1 when foot on ground (h → 0), ≈ 0 when foot in air (h large).

    Args:
        heights: (..., 4) foot heights
        epsilon: barrier parameter
        h_min: floor to prevent division by zero

    Returns:
        scale: (..., 4) continuous force scale in [0, 1]
    """
    h_clamped = jnp.maximum(heights, h_min)
    lam = epsilon / h_clamped
    return lam / (lam + 1.0)


def barrier_foot_forces_reference(heights: jnp.ndarray, epsilon: float,
                                  mass: float) -> jnp.ndarray:
    """Generate reference foot forces from barrier-smoothed contact.

    Instead of binary stance/swing, forces decay smoothly with foot height.

    Args:
        heights: (4,) foot heights at current timestep
        epsilon: barrier parameter
        mass: robot mass

    Returns:
        ref_forces: (12,) foot force reference [f0_xyz, f1_xyz, f2_xyz, f3_xyz]
    """
    fz = barrier_contact_force(heights[None, :], epsilon, mass)[0]
    forces = jnp.zeros(12)
    for k in range(4):
        forces = forces.at[3*k + 2].set(fz[k])
    return forces
