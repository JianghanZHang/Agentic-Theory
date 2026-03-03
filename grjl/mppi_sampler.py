"""
MPPI Sampler — Model Predictive Path Integral (Step 2b)

Samples K trajectories, weights by Boltzmann factor exp(-J_k/alpha)/Z,
and fuses into a single optimal trajectory.  Contact mode tracking
(separating/sliding/sticking) with SDF barrier penalty.

Reference: threebody.tex thm:3b-mppi (lines 395-430),
           calculus.tex (lines 1153-1203) path integral interpretation.
"""

import numpy as np
from numpy.linalg import norm


# Contact mode enumeration
MODE_SEPARATING = 0
MODE_SLIDING = 1
MODE_STICKING = 2


class MPPISampler:
    """MPPI trajectory sampler with contact mode selection.

    Parameters
    ----------
    dynamics_fn : callable(state, control, dt) -> next_state
        Forward dynamics simulator.
    cost_fn : callable(state, control) -> scalar
        Running cost L(x, u).
    state_dim : int
        Dimension of state vector.
    control_dim : int
        Dimension of control vector.
    alpha : float
        Temperature parameter for Boltzmann weighting.
    u_max : float
        Box constraint on control.
    beta : float
        SDF barrier coefficient.
    """

    def __init__(self, dynamics_fn, cost_fn, state_dim, control_dim,
                 alpha=0.05, u_max=5.0, beta=10.0):
        self.dynamics_fn = dynamics_fn
        self.cost_fn = cost_fn
        self.state_dim = state_dim
        self.control_dim = control_dim
        self.alpha = alpha
        self.u_max = u_max
        self.beta = beta

    def sample(self, x0, K, horizon, dt, noise_std=1.0, u_nominal=None):
        """Sample K trajectories from current state.

        Parameters
        ----------
        x0 : (state_dim,) array
            Current state.
        K : int
            Number of trajectory samples.
        horizon : int
            Number of time steps to roll out.
        dt : float
            Time step.
        noise_std : float
            Standard deviation of control noise.
        u_nominal : (horizon, control_dim) array or None
            Nominal control sequence to perturb around.

        Returns
        -------
        trajectories : (K, horizon+1, state_dim) array
        controls : (K, horizon, control_dim) array
        costs : (K,) array
        """
        if u_nominal is None:
            u_nominal = np.zeros((horizon, self.control_dim))

        trajectories = np.zeros((K, horizon + 1, self.state_dim))
        controls = np.zeros((K, horizon, self.control_dim))
        costs = np.zeros(K)

        for k in range(K):
            # Perturb nominal control with Gaussian noise
            noise = noise_std * np.random.randn(horizon, self.control_dim)
            u_k = np.clip(u_nominal + noise, -self.u_max, self.u_max)

            x = x0.copy()
            trajectories[k, 0] = x
            J = 0.0

            for t in range(horizon):
                # Running cost
                J += self.cost_fn(x, u_k[t]) * dt

                # Forward dynamics
                x = self.dynamics_fn(x, u_k[t], dt)
                trajectories[k, t + 1] = x
                controls[k, t] = u_k[t]

            costs[k] = J

        return trajectories, controls, costs

    def reweight(self, costs):
        """Compute Boltzmann weights: w_k = exp(-J_k / alpha) / Z.

        Parameters
        ----------
        costs : (K,) array

        Returns
        -------
        weights : (K,) array summing to 1.
        """
        # Shift for numerical stability
        c_min = np.min(costs)
        log_weights = -(costs - c_min) / self.alpha
        # Softmax
        max_lw = np.max(log_weights)
        weights = np.exp(log_weights - max_lw)
        Z = np.sum(weights)
        if Z < 1e-30:
            return np.ones(len(costs)) / len(costs)
        return weights / Z

    def fuse(self, controls, weights):
        """Weighted mean control trajectory.

        Parameters
        ----------
        controls : (K, horizon, control_dim) array
        weights : (K,) array

        Returns
        -------
        u_fused : (horizon, control_dim) array
        """
        # weights[:, None, None] broadcasts over (horizon, control_dim)
        u_fused = np.sum(
            controls * weights[:, None, None], axis=0)
        return np.clip(u_fused, -self.u_max, self.u_max)

    def solve(self, x0, horizon, dt, K=64, noise_std=1.0,
              n_iters=5, u_init=None):
        """Run MPPI for n_iters, refining the nominal trajectory.

        Parameters
        ----------
        x0 : initial state
        horizon : planning horizon (steps)
        dt : time step
        K : number of samples per iteration
        noise_std : control noise
        n_iters : number of refinement iterations
        u_init : initial nominal control sequence

        Returns
        -------
        u_opt : (horizon, control_dim) optimal control sequence
        cost_history : list of mean costs per iteration
        """
        u_nominal = (u_init.copy() if u_init is not None
                     else np.zeros((horizon, self.control_dim)))
        cost_history = []

        for it in range(n_iters):
            trajs, ctrls, costs = self.sample(
                x0, K, horizon, dt, noise_std, u_nominal)
            weights = self.reweight(costs)
            u_nominal = self.fuse(ctrls, weights)
            cost_history.append(float(np.mean(costs)))

        return u_nominal, cost_history


def contact_weight(mode, k_n=1.0, k_t=1.0, mu_friction=0.5):
    """Compute edge weight for a contact point given its mode.

    Reference: threebody.tex lines 374-387.

    Parameters
    ----------
    mode : int
        MODE_SEPARATING, MODE_SLIDING, or MODE_STICKING.
    k_n : float
        Normal stiffness.
    k_t : float
        Tangential stiffness.
    mu_friction : float
        Friction coefficient.

    Returns
    -------
    w : float
        Edge weight for the grasp graph Laplacian.
    """
    if mode == MODE_SEPARATING:
        return 0.0
    elif mode == MODE_SLIDING:
        return k_n + mu_friction * k_n
    elif mode == MODE_STICKING:
        return k_n + k_t
    else:
        raise ValueError(f"Unknown contact mode: {mode}")


def sdf_barrier_cost(sdf_values, beta=10.0):
    """SDF barrier penalty: sum of beta/phi_i for phi_i > 0 (penetration).

    Parameters
    ----------
    sdf_values : array
        Signed distance values (positive = separated, negative = penetrating).
    beta : float
        Barrier coefficient.

    Returns
    -------
    cost : float
    """
    cost = 0.0
    for phi in sdf_values:
        if phi < 1e-4:
            # Penetrating or near-contact: large penalty
            cost += beta / max(phi, 1e-6)
        else:
            cost += beta / phi
    return cost
