"""
Pontryagin Maximum Principle Solver (Step 2c)

Forward-backward sweep for the gravity damper OCP.
State x = (q, qdot) in R^24, costate p in R^24.
Optimal control: u*(t) = sat_{u_bar}(-p_qdot_star / (alpha * m_star)).
Complementary slackness: mu(t)(epsilon - lambda_1) = 0.

Reference: threebody.tex eqs 3b-ustar (line 173), 3b-costate (line 176),
           thm:3b-damper (line 142).
"""

import numpy as np
from numpy.linalg import eigvalsh, eigh, norm


def gravitational_force(qi, qj, mi, mj, G=0.5, softening=0.05):
    """Gravitational force on body i due to body j."""
    r = qj - qi
    d = max(norm(r), softening)
    return G * mi * mj / d**2 * r / d


def tidal_weight(qi, qj, mi, mj, G=0.5, softening=0.05):
    """Tidal coupling weight w_ij = G m_i m_j / |q_i - q_j|^3."""
    d = max(norm(qi - qj), softening)
    return G * mi * mj / d**3


def graph_laplacian(positions, masses, G=0.5):
    """Compute weighted graph Laplacian and its Fiedler eigenvalue."""
    n = len(masses)
    L = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            w = tidal_weight(positions[i], positions[j],
                             masses[i], masses[j], G)
            L[i, i] += w
            L[j, j] += w
            L[i, j] -= w
            L[j, i] -= w
    evals = eigvalsh(L)
    return L, evals[1]  # Fiedler eigenvalue


def spectral_gradient_analytical(positions, masses, damper_idx=3, G=0.5):
    """Analytical gradient of lambda_1 w.r.t. damper position.

    Uses eigenvector perturbation: d lambda_1 / d q*_k = v1^T (dL/dq*_k) v1.
    """
    n = len(masses)
    L = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            w = tidal_weight(positions[i], positions[j],
                             masses[i], masses[j], G)
            L[i, i] += w
            L[j, j] += w
            L[i, j] -= w
            L[j, i] -= w

    evals, evecs = eigh(L)
    v1 = evecs[:, 1]  # Fiedler eigenvector

    grad = np.zeros(3)
    q_star = positions[damper_idx]
    m_star = masses[damper_idx]

    for j in range(n):
        if j == damper_idx:
            continue
        r = positions[j] - q_star
        d = max(norm(r), 0.05)
        # dw/dq*_k = -3 G m_* m_j / d^5 * (q_j - q*)_k ... but we need
        # the full derivative of L w.r.t. q*_k
        dw_dqstar = 3.0 * G * m_star * masses[j] / d**5 * r

        for k in range(3):
            # dL/dq*_k: update diagonal and off-diagonal entries
            dL = np.zeros((n, n))
            dL[damper_idx, damper_idx] += dw_dqstar[k]
            dL[j, j] += dw_dqstar[k]
            dL[damper_idx, j] -= dw_dqstar[k]
            dL[j, damper_idx] -= dw_dqstar[k]
            grad[k] += v1 @ dL @ v1

    return grad


def saturate(v, u_max):
    """Componentwise saturation."""
    return np.clip(v, -u_max, u_max)


class PontryaginSolver:
    """Forward-backward sweep PMP solver for the gravity damper OCP.

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
    """

    def __init__(self, masses, G=0.5, alpha=0.05, epsilon=0.02,
                 u_max=5.0, dt=0.002):
        self.masses = list(masses)
        self.n_bodies = len(masses)
        self.G = G
        self.alpha = alpha
        self.epsilon = epsilon
        self.u_max = u_max
        self.dt = dt
        self.damper_idx = self.n_bodies - 1

    def state_from_pos_vel(self, positions, velocities):
        """Pack positions and velocities into state vector x in R^{6n}."""
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

    def dynamics(self, x, u):
        """Compute dx/dt given state x and control u (on damper only)."""
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

    def lagrangian(self, x, u):
        """Compute L(x) + (alpha/2)||u||^2."""
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

    def compute_multiplier(self, positions, lambda1):
        """Compute spectral constraint multiplier mu(t).

        Complementary slackness: mu(epsilon - lambda1) = 0.
        When lambda1 <= epsilon, mu > 0 proportional to violation.
        """
        if lambda1 >= self.epsilon:
            return 0.0
        # Penalty for constraint violation
        return max(0.0, (self.epsilon - lambda1) / self.epsilon) * 100.0

    def optimal_control(self, p, x):
        """Compute u*(t) = sat_{u_bar}(-p_qdot_star / (alpha * m_star)).

        Reference: eq 3b-ustar.
        """
        n = self.n_bodies
        idx = self.damper_idx
        p_qdot_star = p[3*n + 3*idx:3*n + 3*idx + 3]
        m_star = self.masses[idx]
        u_raw = -p_qdot_star / (self.alpha * m_star)
        return saturate(u_raw, self.u_max)

    def costate_dynamics(self, p, x, u, mu):
        """Compute dp/dt (backward costate equation).

        dp/dt = -dH/dx = -dL/dx + mu * d(lambda1)/dx - A^T p
        We compute numerically via finite differences on the Hamiltonian.
        """
        n = self.n_bodies
        dp = np.zeros_like(p)
        delta = 1e-5

        for k in range(len(x)):
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[k] += delta
            x_minus[k] -= delta

            # dH/dx_k via finite difference
            H_plus = self._hamiltonian(x_plus, p, u, mu)
            H_minus = self._hamiltonian(x_minus, p, u, mu)
            dp[k] = -(H_plus - H_minus) / (2 * delta)

        return dp

    def _hamiltonian(self, x, p, u, mu):
        """Control Hamiltonian H = L + (alpha/2)||u||^2 + p.f(x,u)
           + mu(epsilon - lambda1)."""
        positions, _ = self.pos_vel_from_state(x)
        _, lambda1 = graph_laplacian(positions, self.masses, self.G)

        L = self.lagrangian(x, u)
        f = self.dynamics(x, u)
        H = L + np.dot(p, f) + mu * (self.epsilon - lambda1)
        return H

    def forward_sweep(self, x0, controls, N):
        """Integrate state forward in time.

        Returns
        -------
        states : (N+1, state_dim) array
        lambda1s : (N,) array of Fiedler eigenvalues
        """
        dim = len(x0)
        states = np.zeros((N + 1, dim))
        states[0] = x0
        lambda1s = np.zeros(N)

        for t in range(N):
            x = states[t]
            u = controls[t]
            positions, _ = self.pos_vel_from_state(x)
            _, lambda1s[t] = graph_laplacian(
                positions, self.masses, self.G)

            # Symplectic Euler
            dx = self.dynamics(x, u)
            states[t + 1] = x + dx * self.dt

        return states, lambda1s

    def backward_sweep(self, states, controls, lambda1s, N):
        """Integrate costate backward in time.

        Returns
        -------
        costates : (N+1, state_dim) array
        multipliers : (N,) array of mu(t)
        """
        dim = states.shape[1]
        costates = np.zeros((N + 1, dim))
        multipliers = np.zeros(N)
        # Terminal condition: p(T) = 0
        costates[N] = np.zeros(dim)

        for t in range(N - 1, -1, -1):
            x = states[t]
            u = controls[t]
            positions, _ = self.pos_vel_from_state(x)
            mu = self.compute_multiplier(positions, lambda1s[t])
            multipliers[t] = mu

            dp = self.costate_dynamics(costates[t + 1], x, u, mu)
            costates[t] = costates[t + 1] - dp * self.dt

        return costates, multipliers

    def solve(self, x0, N, max_iter=20, tol=1e-4, verbose=False):
        """Solve the OCP via forward-backward sweep.

        Parameters
        ----------
        x0 : initial state
        N : number of time steps
        max_iter : maximum iterations
        tol : convergence tolerance on control change
        verbose : print convergence info

        Returns
        -------
        result : dict with states, controls, costates, lambda1s, costs
        """
        dim = len(x0)
        controls = np.zeros((N, 3))
        cost_history = []

        for iteration in range(max_iter):
            # Forward sweep
            states, lambda1s = self.forward_sweep(x0, controls, N)

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

            # Damped update (step size 0.3 for stability)
            step = min(0.3, 1.0 / (iteration + 1) + 0.1)
            controls = (1 - step) * controls + step * controls_new

            # Compute total cost
            total_cost = sum(
                self.lagrangian(states[t], controls[t]) * self.dt
                for t in range(N))
            cost_history.append(total_cost)

            if verbose:
                l1_min = np.min(lambda1s)
                bang_frac = np.mean(
                    np.max(np.abs(controls), axis=1) > 0.95 * self.u_max)
                print(f"  iter {iteration:3d}: J={total_cost:.4f}  "
                      f"du={du:.2e}  l1_min={l1_min:.4f}  "
                      f"bang={100*bang_frac:.1f}%")

            if du < tol and iteration > 2:
                if verbose:
                    print(f"  Converged at iteration {iteration}")
                break

        # Final forward sweep with converged controls
        states, lambda1s = self.forward_sweep(x0, controls, N)

        # Classify arc types
        arc_types = np.zeros(N, dtype=int)
        for t in range(N):
            u_norm = norm(controls[t])
            if u_norm > 0.95 * self.u_max:
                arc_types[t] = 1   # bang
            elif u_norm < 0.05 * self.u_max:
                arc_types[t] = 0   # singular
            else:
                arc_types[t] = 0   # transition (still singular-ish)

        return {
            'states': states,
            'controls': controls,
            'costates': costates,
            'lambda1s': lambda1s,
            'multipliers': multipliers,
            'arc_types': arc_types,
            'cost_history': cost_history,
            'converged': du < tol if max_iter > 2 else True,
        }
