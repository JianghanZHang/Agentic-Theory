"""
Pontryagin Maximum Principle Solver with ρ-weighted Laplacian — GRJL 2.0

Replaces discrete contact mode weights with smooth w(ρ).
The costate chain rule flows through dw/dρ · dρ/dx, giving
analytical sensitivity of the Hamiltonian to the order parameter.

State: x = (q, qdot) ∈ R^{6n}   (n = 4 for three bodies + damper)
Control: u ∈ R^3                  (thrust on damper only)
Optimal: u*(t) = sat_{ū}(−p_{qdot*} / (α m*))

Reference: threebody.tex eqs 3b-ustar, 3b-costate.
"""

import numpy as np
from numpy.linalg import eigvalsh, eigh, norm

from order_parameter import (smooth_edge_weight, d_smooth_edge_weight_d_rho,
                              tidal_rho, build_laplacian_from_rho)


# ── Physics ────────────────────────────────────────────────

def gravitational_force(qi, qj, mi, mj, G=0.5, softening=0.05):
    """Gravitational force on body i due to body j."""
    r = qj - qi
    d = max(norm(r), softening)
    return G * mi * mj / d**2 * r / d


def tidal_weight(qi, qj, mi, mj, G=0.5, softening=0.05):
    """Tidal coupling weight w_ij = G m_i m_j / |q_i - q_j|^3."""
    d = max(norm(qi - qj), softening)
    return G * mi * mj / d**3


def saturate(v, u_max):
    """Componentwise saturation."""
    return np.clip(v, -u_max, u_max)


# ── Solver ─────────────────────────────────────────────────

class PmpRhoSolver:
    """Forward-backward sweep PMP solver with ρ-weighted Laplacian.

    Parameters
    ----------
    masses : list of float
        Masses [m1, m2, m3, m_star].
    G : float
        Gravitational constant.
    alpha : float
        Control cost weight.
    epsilon : float
        Spectral gap threshold.
    u_max : float
        Box constraint.
    dt : float
        Time step.
    k_n, k_t, mu_friction, beta_sigmoid : float
        Parameters for smooth_edge_weight.
    """

    def __init__(self, masses, G=0.5, alpha=0.05, epsilon=0.02,
                 u_max=5.0, dt=0.002,
                 k_n=1.0, k_t=1.0, mu_friction=0.5, beta_sigmoid=20.0):
        self.masses = list(masses)
        self.n_bodies = len(masses)
        self.G = G
        self.alpha = alpha
        self.epsilon = epsilon
        self.u_max = u_max
        self.dt = dt
        self.damper_idx = self.n_bodies - 1

        # Smooth weight parameters
        self.k_n = k_n
        self.k_t = k_t
        self.mu_friction = mu_friction
        self.beta_sigmoid = beta_sigmoid

    # ── State packing ──────────────────────────────────────

    def state_from_pos_vel(self, positions, velocities):
        """Pack positions and velocities into state vector x ∈ R^{6n}."""
        n = self.n_bodies
        x = np.zeros(6 * n)
        for i in range(n):
            x[3*i:3*i+3] = positions[i]
            x[3*n + 3*i:3*n + 3*i+3] = velocities[i]
        return x

    def pos_vel_from_state(self, x):
        """Unpack state vector to positions and velocities."""
        n = self.n_bodies
        positions = [x[3*i:3*i+3].copy() for i in range(n)]
        velocities = [x[3*n + 3*i:3*n + 3*i+3].copy() for i in range(n)]
        return positions, velocities

    # ── ρ computation from state ───────────────────────────

    def compute_rho_pairs(self, positions):
        """Compute pairwise ρ between damper and each body.

        Returns dict mapping (i, j) -> ρ, with i < j.
        """
        rho_pairs = {}
        d_idx = self.damper_idx
        for j in range(self.n_bodies):
            if j == d_idx:
                continue
            i_pair = min(d_idx, j)
            j_pair = max(d_idx, j)
            rho_pairs[(i_pair, j_pair)] = tidal_rho(
                positions, self.masses, d_idx, j,
                self.G, softening=0.05)
        return rho_pairs

    def rho_weighted_laplacian(self, positions):
        """Build Laplacian with ρ-based edge weights.

        Returns L, lambda1, rho_pairs, weights.
        """
        rho_pairs = self.compute_rho_pairs(positions)
        L, lambda1, weights = build_laplacian_from_rho(
            rho_pairs, self.n_bodies,
            self.k_n, self.k_t, self.mu_friction, self.beta_sigmoid)
        return L, lambda1, rho_pairs, weights

    # ── Dynamics ───────────────────────────────────────────

    def dynamics(self, x, u):
        """Compute dx/dt given state x and control u."""
        positions, velocities = self.pos_vel_from_state(x)
        n = self.n_bodies
        dx = np.zeros_like(x)

        # qdot = v
        for i in range(n):
            dx[3*i:3*i+3] = velocities[i]

        # vdot = forces / mass
        for i in range(n):
            force = np.zeros(3)
            for j in range(n):
                if i != j:
                    force += gravitational_force(
                        positions[i], positions[j],
                        self.masses[i], self.masses[j], self.G)
            if i == self.damper_idx:
                force += u
            dx[3*n + 3*i:3*n + 3*i+3] = force / self.masses[i]

        return dx

    # ── Cost ───────────────────────────────────────────────

    def lagrangian(self, x, u):
        """Running cost: L(x) + (α/2)||u||²."""
        positions, velocities = self.pos_vel_from_state(x)
        n = self.n_bodies

        # Kinetic energy
        T = sum(0.5 * self.masses[i] * np.dot(velocities[i], velocities[i])
                for i in range(n))

        # Potential energy
        V = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                d = max(norm(positions[i] - positions[j]), 0.05)
                V -= self.G * self.masses[i] * self.masses[j] / d

        # Control cost
        control_cost = 0.5 * self.alpha * np.dot(u, u)

        return (T - V) + control_cost

    # ── Multiplier ─────────────────────────────────────────

    def compute_multiplier(self, lambda1):
        """Complementary slackness: μ(ε − λ₁) = 0.

        When λ₁ < ε, μ > 0 proportional to violation.
        """
        if lambda1 >= self.epsilon:
            return 0.0
        return max(0.0, (self.epsilon - lambda1) / self.epsilon) * 100.0

    # ── Optimal control ────────────────────────────────────

    def optimal_control(self, p, x):
        """u*(t) = sat_{ū}(−p_{qdot*} / (α m*))."""
        n = self.n_bodies
        idx = self.damper_idx
        p_qdot_star = p[3*n + 3*idx:3*n + 3*idx + 3]
        m_star = self.masses[idx]
        u_raw = -p_qdot_star / (self.alpha * m_star)
        return saturate(u_raw, self.u_max)

    # ── Hamiltonian ────────────────────────────────────────

    def _hamiltonian(self, x, p, u, mu):
        """Control Hamiltonian with ρ-weighted spectral constraint.

        H = L + p·f(x,u) + μ(ε − λ₁)

        where λ₁ is computed from ρ-weighted Laplacian.
        """
        positions, _ = self.pos_vel_from_state(x)
        _, lambda1, _, _ = self.rho_weighted_laplacian(positions)

        L = self.lagrangian(x, u)
        f = self.dynamics(x, u)
        H = L + np.dot(p, f) + mu * (self.epsilon - lambda1)
        return H

    # ── Costate dynamics ───────────────────────────────────

    def costate_dynamics(self, p, x, u, mu):
        """Compute dp/dt via finite-difference on the Hamiltonian.

        The chain rule dH/dx flows through:
          dH/dρ · dρ/dx,  where dH/dρ = μ · dλ₁/dw · dw/dρ

        We use numerical dH/dx for robustness (analytical available
        via spectral_analytical.py if needed).
        """
        dp = np.zeros_like(p)
        delta = 1e-5

        for k in range(len(x)):
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[k] += delta
            x_minus[k] -= delta

            H_plus = self._hamiltonian(x_plus, p, u, mu)
            H_minus = self._hamiltonian(x_minus, p, u, mu)
            dp[k] = -(H_plus - H_minus) / (2 * delta)

        return dp

    # ── Forward sweep ──────────────────────────────────────

    def forward_sweep(self, x0, controls, N):
        """Integrate state forward.

        Returns
        -------
        states : (N+1, state_dim) array
        lambda1s : (N,) array
        rho_histories : list of N dicts
        weight_histories : list of N dicts
        """
        dim = len(x0)
        states = np.zeros((N + 1, dim))
        states[0] = x0
        lambda1s = np.zeros(N)
        rho_histories = []
        weight_histories = []

        for t in range(N):
            x = states[t]
            u = controls[t]
            positions, _ = self.pos_vel_from_state(x)

            # ρ-weighted Laplacian
            _, lambda1, rho_pairs, weights = \
                self.rho_weighted_laplacian(positions)
            lambda1s[t] = lambda1
            rho_histories.append(rho_pairs)
            weight_histories.append(weights)

            # Symplectic Euler
            dx = self.dynamics(x, u)
            states[t + 1] = x + dx * self.dt

        return states, lambda1s, rho_histories, weight_histories

    # ── Backward sweep ─────────────────────────────────────

    def backward_sweep(self, states, controls, lambda1s, N):
        """Integrate costate backward.

        Returns
        -------
        costates : (N+1, state_dim) array
        multipliers : (N,) array
        """
        dim = states.shape[1]
        costates = np.zeros((N + 1, dim))
        multipliers = np.zeros(N)

        # Terminal condition: p(T) = 0
        costates[N] = np.zeros(dim)

        for t in range(N - 1, -1, -1):
            x = states[t]
            u = controls[t]
            mu = self.compute_multiplier(lambda1s[t])
            multipliers[t] = mu

            dp = self.costate_dynamics(costates[t + 1], x, u, mu)
            costates[t] = costates[t + 1] - dp * self.dt

        return costates, multipliers

    # ── Full solve ─────────────────────────────────────────

    def solve(self, x0, N, max_iter=20, tol=1e-4, verbose=False):
        """Solve the OCP via forward-backward sweep.

        Returns
        -------
        result : dict with states, controls, costates, lambda1s,
                 rho_histories, weight_histories, arc_types, cost_history.
        """
        dim = len(x0)
        controls = np.zeros((N, 3))
        cost_history = []
        du = float('inf')

        for iteration in range(max_iter):
            # Forward sweep
            states, lambda1s, rho_hists, weight_hists = \
                self.forward_sweep(x0, controls, N)

            # Backward sweep
            costates, multipliers = self.backward_sweep(
                states, controls, lambda1s, N)

            # Update controls
            controls_new = np.zeros_like(controls)
            for t in range(N):
                controls_new[t] = self.optimal_control(
                    costates[t], states[t])

            # Convergence check
            du = norm(controls_new - controls) / max(norm(controls), 1e-10)

            # Damped update
            step = min(0.3, 1.0 / (iteration + 1) + 0.1)
            controls = (1 - step) * controls + step * controls_new

            # Total cost
            total_cost = sum(
                self.lagrangian(states[t], controls[t]) * self.dt
                for t in range(N))
            cost_history.append(total_cost)

            if verbose:
                l1_min = np.min(lambda1s)
                bang_frac = np.mean(
                    np.max(np.abs(controls), axis=1) > 0.95 * self.u_max)
                # Min ρ across all pairs and timesteps
                all_rhos = [r for d in rho_hists for r in d.values()]
                rho_min = min(all_rhos) if all_rhos else 0.0
                rho_max = max(all_rhos) if all_rhos else 0.0
                print(f"  iter {iteration:3d}: J={total_cost:.4f}  "
                      f"du={du:.2e}  λ₁_min={l1_min:.4f}  "
                      f"ρ∈[{rho_min:.2f},{rho_max:.2f}]  "
                      f"bang={100*bang_frac:.1f}%")

            if du < tol and iteration > 2:
                if verbose:
                    print(f"  Converged at iteration {iteration}")
                break

        # Final forward sweep
        states, lambda1s, rho_hists, weight_hists = \
            self.forward_sweep(x0, controls, N)

        # Classify arc types
        arc_types = np.zeros(N, dtype=int)
        for t in range(N):
            u_norm = norm(controls[t])
            if u_norm > 0.95 * self.u_max:
                arc_types[t] = 1   # bang
            else:
                arc_types[t] = 0   # singular

        return {
            'states': states,
            'controls': controls,
            'costates': costates,
            'lambda1s': lambda1s,
            'multipliers': multipliers,
            'rho_histories': rho_hists,
            'weight_histories': weight_hists,
            'arc_types': arc_types,
            'cost_history': cost_history,
            'converged': du < tol if max_iter > 2 else True,
        }
