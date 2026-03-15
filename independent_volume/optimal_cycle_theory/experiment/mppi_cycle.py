"""MPPI outer loop with dual ascent on temperature.

Hierarchy:
  MPPI (stochastic, barrier-smoothed — no contact mode switching)
    └── MuJoCo simulation (ground truth evaluation)
        └── Go2 model, implicit Euler, high contact solver iterations

The temperature ε serves a DUAL role (the unification):
  1. Barrier sharpness: λ_k = ε / h_k (contact force from foot height)
  2. MPPI temperature: w(φ) ∝ exp(-J(φ)/ε) (Boltzmann reweighting)

Both are log-transforms: barrier converts complementarity to smooth potential,
Hopf-Cole converts nonlinear HJB to linear heat equation. Same ε.

Dual ascent on ε:
  min_f E_f[J]  s.t.  H(f) ≥ H_target
  Solution: f*(φ) ∝ exp(-J(φ)/ε), with ε adjusted by dual ascent.

Re-cycle convergence: student-t_ν → Gaussian on T^3 as ν → ∞,
with holonomy H(f_{t_ν}) = O(1/ν).
"""

from typing import Dict, List, Optional, Tuple

import jax
import jax.numpy as jnp
import numpy as np

from gait_sampler import (
    sample_student_t_torus,
    foot_height_schedule,
    barrier_foot_forces_reference,
    barrier_force_scale,
    entropy_empirical,
    effective_sample_size,
    weighted_circular_mean,
    weighted_circular_variance,
)
from quadruped_dynamics import MuJoCoQuadruped
from config import ROBOT, OCP, MPPI, CONSTRAINTS


class OptimalCycleMPPI:
    """MPPI over gait phases with barrier-smoothed contact and dual ascent.

    Each iteration:
      1. Sample N gait phases φ^(i) ∈ T^3 from student-t mollifier
      2. Decode each φ^(i) → continuous foot height schedule h_k(t; φ)
      3. Barrier forces: λ_k = ε / h_k (smooth, no binary mask)
      4. Simulate each gait in MuJoCo → cost J^(i)
      5. Boltzmann reweight: w^(i) = softmax(-J / ε)  (same ε!)
      6. Dual ascent: ε ← α_up · ε or α_down · ε  [multiplicative]
      7. Compress entropy bound
      8. Update student-t center (weighted circular mean on T^3)
    """

    def __init__(self, sim: Optional[MuJoCoQuadruped] = None,
                 N: int = None, nu_init: float = None,
                 epsilon_init: float = None,
                 compression_rate: float = None):

        self.sim = sim or MuJoCoQuadruped()
        self.N = N or MPPI["N_samples"]

        # Student-t state (re-cycle)
        self.nu = nu_init or MPPI["nu_init"]
        self.mu = jnp.array([0.5, 0.5, 0.0])  # start near trot
        self.Sigma = 0.25 * jnp.eye(3)

        # Dual ascent state — ε controls BOTH barrier sharpness AND temperature
        self.epsilon = epsilon_init or MPPI["epsilon_init"]
        self.H_target = float(jnp.log(self.N))  # start at max entropy
        self.compression_rate = compression_rate or MPPI["compression_rate"]

        # Diagnostics history
        self.history: Dict[str, List] = {
            'holonomy': [],
            'entropy': [],
            'epsilon': [],
            'ess': [],
            'cost_mean': [],
            'cost_std': [],
            'cost_best': [],
            'best_gait': [],
            'mu': [],
            'circular_var': [],
        }

    def _evaluate_gait(self, phi: np.ndarray, x0: np.ndarray,
                       target_velocity: np.ndarray) -> float:
        """Evaluate a single gait in MuJoCo with barrier-smoothed contact.

        The barrier force λ_k = ε / h_k replaces the binary contact mask.
        As ε → 0, forces sharpen to complementarity AND the MPPI distribution
        concentrates on the optimal gait — simultaneously.

        Args:
            phi: (3,) gait phase offsets
            x0: (13,) initial centroidal state
            target_velocity: (3,) target CoM velocity

        Returns:
            cost: scalar trajectory cost
        """
        horizon = OCP["horizon"]
        dt = float(OCP["dt"])
        beta = ROBOT["duty_factor"]
        mass = ROBOT["mass"]
        h_min = MPPI.get("h_min", 1e-4)

        # Continuous foot height schedule from gait phase (no binary decode)
        heights = np.array(foot_height_schedule(
            jnp.array(phi), beta, horizon, dt
        ))

        # Barrier-smoothed force scale: scale_k = λ_k / (λ_k + 1)
        # Continuous in [0, 1], replaces binary contact_mask
        scales = np.array(barrier_force_scale(
            jnp.array(heights), self.epsilon, h_min
        ))

        # Generate barrier-smoothed foot force reference for each timestep
        foot_forces = np.zeros((horizon, 12))
        for t in range(horizon):
            ref = barrier_foot_forces_reference(
                jnp.array(heights[t]), self.epsilon, mass
            )
            foot_forces[t] = np.array(ref)

        # For MuJoCo: use force_scale as soft contact mask
        # scale > 0.5 → stance-like behavior, scale < 0.5 → swing-like
        cost = self.sim.evaluate_cost(
            foot_forces, scales[:horizon], dt, x0, target_velocity,
            epsilon=self.epsilon, constraints=CONSTRAINTS
        )
        return cost

    def step(self, x0: jnp.ndarray, rng_key: jax.Array,
             target_velocity: Optional[jnp.ndarray] = None) -> Tuple[dict, dict]:
        """One MPPI re-cycle iteration.

        Args:
            x0: (13,) initial centroidal state
            rng_key: JAX PRNG key
            target_velocity: (3,) target velocity (default from config)

        Returns:
            (best_gait_info, diagnostics) tuple
        """
        if target_velocity is None:
            target_velocity = OCP["target_velocity"]

        x0_np = np.array(x0)
        tv_np = np.array(target_velocity)

        # 1. Sample N gaits from student-t on T^3
        phis = sample_student_t_torus(
            self.nu, self.mu, self.Sigma, self.N, rng_key
        )

        # 2. Evaluate each gait in MuJoCo (barrier-smoothed, no binary modes)
        costs = np.zeros(self.N)
        for i in range(self.N):
            costs[i] = self._evaluate_gait(np.array(phis[i]), x0_np, tv_np)

        costs_jnp = jnp.array(costs)

        # 3. Boltzmann reweight (same ε as barrier — the unification)
        log_w = -(costs_jnp - costs_jnp.min()) / self.epsilon
        weights = jax.nn.softmax(log_w)

        # 4. Measure holonomy, entropy, ESS
        cost_var = float(jnp.var(costs_jnp))
        entropy = float(entropy_empirical(weights))
        ess = float(effective_sample_size(weights))
        circ_var = weighted_circular_variance(phis, weights)

        # 5. Multiplicative dual ascent  [paper step 7]
        #    ε increases when entropy is too low (need more exploration)
        #    ε decreases when entropy is too high (can exploit more)
        #    This SIMULTANEOUSLY adjusts barrier sharpness and temperature
        if entropy < self.H_target:
            self.epsilon *= MPPI["alpha_up"]
        else:
            self.epsilon *= MPPI["alpha_down"]
        self.epsilon = float(jnp.clip(
            self.epsilon, MPPI["epsilon_min"], MPPI["epsilon_max"]
        ))

        # 6. Compress entropy bound (re-cycle progress)
        self.H_target *= self.compression_rate

        # 7. Update student-t center (weighted circular mean on T^3)
        self.mu = weighted_circular_mean(phis, weights)

        # 8. Update scale matrix (weighted circular covariance)
        # Shrink Sigma as distribution concentrates
        self.Sigma = jnp.diag(jnp.clip(circ_var, 0.01, 0.5))

        # Record diagnostics
        best_idx = int(jnp.argmin(costs_jnp))
        self.history['holonomy'].append(cost_var)
        self.history['entropy'].append(entropy)
        self.history['epsilon'].append(self.epsilon)
        self.history['ess'].append(ess)
        self.history['cost_mean'].append(float(costs_jnp.mean()))
        self.history['cost_std'].append(float(costs_jnp.std()))
        self.history['cost_best'].append(float(costs_jnp.min()))
        self.history['best_gait'].append(phis[best_idx].tolist())
        self.history['mu'].append(self.mu.tolist())
        self.history['circular_var'].append(circ_var.tolist())

        best_info = {
            'phi': phis[best_idx],
            'cost': float(costs_jnp[best_idx]),
            'idx': best_idx,
        }
        diagnostics = {k: v[-1] for k, v in self.history.items()}
        return best_info, diagnostics

    def converged(self, tol: float = 1e-2) -> bool:
        """Check if cycle has closed.

        Convergence: all sampled gaits give similar cost (holonomy → 0)
        AND entropy is low (distribution concentrated).
        """
        if len(self.history['holonomy']) < 2:
            return False
        return (self.history['holonomy'][-1] < tol and
                self.history['entropy'][-1] < 1.0)

    def run(self, x0: jnp.ndarray, n_iters: int = 100,
            target_velocity: Optional[jnp.ndarray] = None,
            seed: int = 0, verbose: bool = True) -> dict:
        """Run the full MPPI re-cycle loop.

        Args:
            x0: (13,) initial centroidal state
            n_iters: maximum iterations
            target_velocity: (3,) target velocity
            seed: random seed
            verbose: print progress

        Returns:
            history dict with all diagnostics
        """
        key = jax.random.PRNGKey(seed)

        for k in range(n_iters):
            key, subkey = jax.random.split(key)
            best, diag = self.step(x0, subkey, target_velocity)

            if verbose and (k % 10 == 0 or k == n_iters - 1):
                phi_str = np.array(best['phi']).round(3)
                print(
                    f"iter {k:3d}: "
                    f"cost={diag['cost_mean']:.2f}±{diag['cost_std']:.2f}  "
                    f"H={diag['holonomy']:.4f}  "
                    f"S={diag['entropy']:.2f}  "
                    f"ε={diag['epsilon']:.4f}  "
                    f"ESS={diag['ess']:.1f}  "
                    f"φ*={phi_str}  "
                    f"μ={np.array(diag['mu']).round(3)}"
                )

            if self.converged():
                if verbose:
                    print(f"\nConverged at iteration {k}!")
                    print(f"Best gait: φ = {np.array(best['phi']).round(3)}")
                break

        return self.history
