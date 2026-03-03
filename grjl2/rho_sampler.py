"""
MPPI Sampler with continuous ρ — GRJL 2.0

Replaces discrete MODE_* enumeration with continuous order parameter ρ.
The ρ value is *derived* from state+control at each timestep (not sampled
directly).  A phase-transition penalty discourages lingering at ρ ≈ 1.

Reference: threebody.tex thm:3b-mppi, calculus.tex path integral.
"""

import numpy as np
from numpy.linalg import norm

from order_parameter import (compute_rho, smooth_edge_weight,
                              build_laplacian_from_rho, tidal_rho)


class RhoMPPISampler:
    """MPPI trajectory sampler with continuous ρ.

    Parameters
    ----------
    dynamics_fn : callable(state, control, dt) -> next_state
    cost_fn : callable(state, control, rho_info) -> scalar
        Running cost.  rho_info is a dict with per-pair ρ values.
    rho_fn : callable(state, control) -> dict
        Computes pairwise ρ values from state and control.
        Returns dict mapping (i, j) -> ρ.
    state_dim : int
    control_dim : int
    alpha : float
        Temperature for Boltzmann weighting.
    u_max : float
        Box constraint on control.
    gamma : float
        Phase-transition penalty coefficient.
    delta_rho : float
        Width of the phase-transition penalty Gaussian.
    """

    def __init__(self, dynamics_fn, cost_fn, rho_fn,
                 state_dim, control_dim,
                 alpha=0.05, u_max=5.0, gamma=5.0, delta_rho=0.1):
        self.dynamics_fn = dynamics_fn
        self.cost_fn = cost_fn
        self.rho_fn = rho_fn
        self.state_dim = state_dim
        self.control_dim = control_dim
        self.alpha = alpha
        self.u_max = u_max
        self.gamma = gamma
        self.delta_rho = delta_rho

    def _phase_transition_penalty(self, rho_dict):
        """Penalty for lingering near ρ ≈ 1.

        cost += γ · Σ_{(i,j)} exp(−(ρ_{ij}−1)² / δ²)
        """
        penalty = 0.0
        for rho in rho_dict.values():
            penalty += np.exp(-(rho - 1.0)**2 / self.delta_rho**2)
        return self.gamma * penalty

    def sample(self, x0, K, horizon, dt, noise_std=1.0, u_nominal=None):
        """Sample K trajectories from current state.

        Returns
        -------
        trajectories : (K, horizon+1, state_dim) array
        controls : (K, horizon, control_dim) array
        costs : (K,) array
        rho_histories : list of K lists of dicts
        """
        if u_nominal is None:
            u_nominal = np.zeros((horizon, self.control_dim))

        trajectories = np.zeros((K, horizon + 1, self.state_dim))
        controls = np.zeros((K, horizon, self.control_dim))
        costs = np.zeros(K)
        rho_histories = []

        for k in range(K):
            noise = noise_std * np.random.randn(horizon, self.control_dim)
            u_k = np.clip(u_nominal + noise, -self.u_max, self.u_max)

            x = x0.copy()
            trajectories[k, 0] = x
            J = 0.0
            rho_hist_k = []

            for t in range(horizon):
                # Derive ρ from current state and control
                rho_dict = self.rho_fn(x, u_k[t])
                rho_hist_k.append(rho_dict)

                # Running cost + phase-transition penalty
                J += self.cost_fn(x, u_k[t], rho_dict) * dt
                J += self._phase_transition_penalty(rho_dict) * dt

                # Forward dynamics
                x = self.dynamics_fn(x, u_k[t], dt)
                trajectories[k, t + 1] = x
                controls[k, t] = u_k[t]

            costs[k] = J
            rho_histories.append(rho_hist_k)

        return trajectories, controls, costs, rho_histories

    def reweight(self, costs):
        """Boltzmann weights: w_k = exp(−J_k / α) / Z."""
        c_min = np.min(costs)
        log_w = -(costs - c_min) / self.alpha
        max_lw = np.max(log_w)
        w = np.exp(log_w - max_lw)
        Z = np.sum(w)
        if Z < 1e-30:
            return np.ones(len(costs)) / len(costs)
        return w / Z

    def fuse(self, controls, weights):
        """Weighted mean control trajectory."""
        u_fused = np.sum(controls * weights[:, None, None], axis=0)
        return np.clip(u_fused, -self.u_max, self.u_max)

    def solve(self, x0, horizon, dt, K=64, noise_std=1.0,
              n_iters=5, u_init=None):
        """Iterative MPPI refinement.

        Returns
        -------
        u_opt : (horizon, control_dim) array
        cost_history : list of mean costs per iteration
        rho_history : list of ρ dicts from final iteration
        """
        u_nominal = (u_init.copy() if u_init is not None
                     else np.zeros((horizon, self.control_dim)))
        cost_history = []
        rho_history = []

        for it in range(n_iters):
            trajs, ctrls, costs, rho_hists = self.sample(
                x0, K, horizon, dt, noise_std, u_nominal)
            weights = self.reweight(costs)
            u_nominal = self.fuse(ctrls, weights)
            cost_history.append(float(np.mean(costs)))

            # Keep best trajectory's ρ history from last iteration
            if it == n_iters - 1:
                best_k = np.argmin(costs)
                rho_history = rho_hists[best_k]

        return u_nominal, cost_history, rho_history


# ── Helper: build rho_fn for the gravitational three-body ──

def make_gravity_rho_fn(masses, damper_idx=3, G=0.5, softening=0.05):
    """Create a rho_fn for the gravity three-body system.

    The returned function extracts positions from the state vector
    and computes pairwise ρ between the damper and each body.
    """
    n = len(masses)

    def rho_fn(state, control):
        positions = [state[3*i:3*i+3] for i in range(n)]
        rho_dict = {}
        for j in range(n):
            if j == damper_idx:
                continue
            i_pair = min(damper_idx, j)
            j_pair = max(damper_idx, j)
            rho_dict[(i_pair, j_pair)] = tidal_rho(
                positions, masses, damper_idx, j, G, softening)
        return rho_dict

    return rho_fn


def make_gravity_cost_fn(masses, alpha=0.05, epsilon=0.02, G=0.5):
    """Create a cost function using ρ-based spectral gap."""
    n = len(masses)

    def cost_fn(state, control, rho_dict):
        # Control cost
        cost = 0.5 * alpha * np.dot(control, control)

        # Spectral gap barrier via ρ-weighted Laplacian
        _, lambda1, _ = build_laplacian_from_rho(rho_dict, n)
        if lambda1 < epsilon:
            cost += 100.0 * (epsilon - lambda1) / epsilon

        return cost

    return cost_fn
