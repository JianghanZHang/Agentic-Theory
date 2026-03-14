"""PCG method tailored for optimal control QPs (ported from optimalgpu)."""
import math
from typing import Any, Dict, NamedTuple, Tuple

import jax.numpy as jnp
from jax import vmap
from jax.lax import while_loop

import jax

from diffmpc.solvers.linear_solve import solve_block_tridi_system
from diffmpc.utils.load_params import load_solver_params

DEFAULT_PCG_SOLVER_PARAMS = (
    load_solver_params("sqp_osqp.yaml")
    .get("admm", {})
    .get("pcg", {"max_iter": 200, "tol_epsilon": 1.0e-8})
)


class PCGDebugOutput(NamedTuple):
    """Debug output after running PCG."""

    num_iterations: int
    convergence_eta: float


class SchurComplementMatrices(NamedTuple):
    """Schur complement matrix parameters of the QP."""

    S: jnp.ndarray  # (N+1, nx+nu, 3*(nx+nu))
    preconditioner_Phiinv: jnp.ndarray  # (N+1, nx+nu, 3*(nx+nu))


class PCGPrimalOptimalControl:
    """
    Preconditioned conjugate gradient solver over primal state-control variables.

    The Schur system is represented in block-tridiagonal form so matvecs are O(N).
    """

    def __init__(
        self,
        problem_horizon: int,
        problem_num_states: int,
        problem_num_controls: int,
        solver_params: Dict[str, Any] = DEFAULT_PCG_SOLVER_PARAMS,
    ):
        self._params = solver_params
        self._name = "PCGPrimalOptimalControl"
        self._problem_horizon = problem_horizon
        self._problem_num_states = problem_num_states
        self._problem_num_controls = problem_num_controls

    @property
    def name(self) -> str:
        return self._name

    @property
    def params(self) -> Dict:
        return self._params

    @property
    def horizon(self) -> int:
        return self._problem_horizon

    @property
    def num_states(self) -> int:
        return self._problem_num_states

    @property
    def num_controls(self) -> int:
        return self._problem_num_controls

    def solve_linear_system(
        self,
        schur_complement_matrices: SchurComplementMatrices,
        schur_complement_gammas: jnp.ndarray,
        zs_guess: jnp.ndarray,
        backend: str = "pcg",
    ) -> Tuple[jnp.ndarray, PCGDebugOutput]:
        """Solve Schur system.

        - "pcg": iterative PCG, fully JAX-traceable.
        - "cudss": direct solve via jax.pure_callback, JAX-traceable.
        - "scipy": direct solve, NOT JAX-traceable (requires Python for-loop).
        """
        S = schur_complement_matrices.S
        Phiinv = schur_complement_matrices.preconditioner_Phiinv
        gammas = schur_complement_gammas
        if backend == "thomas":
            zs = self._solve_thomas(S, gammas)
            return zs, PCGDebugOutput(num_iterations=jnp.array(0), convergence_eta=0.0)
        if backend == "pcr":
            zs = self._solve_pcr(S, gammas)
            return zs, PCGDebugOutput(num_iterations=jnp.array(0), convergence_eta=0.0)
        if backend == "scipy":
            if isinstance(S, jax.core.Tracer) or isinstance(gammas, jax.core.Tracer):
                raise RuntimeError(
                    "SciPy backend is not supported under JAX tracing. "
                    "Use _solve_direct (Python for-loop) or switch to cuDSS."
                )
            return self.solve_linear_system_external(
                schur_complement_matrices,
                schur_complement_gammas,
                backend=backend,
            )
        pcg_max_iter = self.params["max_iter"]
        pcg_epsilon = self.params["tol_epsilon"]
        nx = self.num_states
        nu = self.num_controls
        nz = nx + nu

        def pcg_get_r_init(gammas, S, zs):
            def get_r_block(gamma, S_block, z_prev, z, z_next):
                return gamma - S_block @ jnp.concatenate([z_prev, z, z_next])

            zs_padded = jnp.concatenate(
                [jnp.zeros((1, nz)), zs, jnp.zeros((1, nz))], axis=0
            )
            return vmap(get_r_block)(
                gammas, S, zs_padded[:-2], zs_padded[1:-1], zs_padded[2:]
            )

        r = pcg_get_r_init(gammas, S, zs_guess)
        rs = jnp.concatenate(
            [
                jnp.concatenate([jnp.zeros_like(r[0])[jnp.newaxis], r[:-1]], axis=0),
                r,
                jnp.concatenate([r[1:], jnp.zeros_like(r[0])[jnp.newaxis]], axis=0),
            ],
            axis=-1,
        )
        rtilde = vmap(lambda A, v: A @ v)(Phiinv, rs)
        p = rtilde.copy()
        eta = jnp.sum(r * rtilde)

        def cond_fun(val: Tuple):
            it, _, _, eta_val, _ = val
            _continue = jnp.logical_and(
                jnp.abs(eta_val) > pcg_epsilon, it <= pcg_max_iter - 1
            )
            _continue = jnp.logical_or(_continue, it < 1)
            return _continue

        def pcg_iterate_fun(val):
            it, r, p, eta_val, zs = val
            ps = jnp.concatenate(
                [
                    jnp.concatenate(
                        [jnp.zeros_like(p[0])[jnp.newaxis], p[:-1]], axis=0
                    ),
                    p,
                    jnp.concatenate([p[1:], jnp.zeros_like(p[0])[jnp.newaxis]], axis=0),
                ],
                axis=-1,
            )
            Upsilon = vmap(lambda A, v: A @ v)(S, ps)
            v = jnp.sum(p * Upsilon)
            alpha = eta_val / v
            zs = zs + alpha * p
            r = r - alpha * Upsilon
            rs = jnp.concatenate(
                [
                    jnp.concatenate(
                        [jnp.zeros_like(r[0])[jnp.newaxis], r[:-1]], axis=0
                    ),
                    r,
                    jnp.concatenate([r[1:], jnp.zeros_like(r[0])[jnp.newaxis]], axis=0),
                ],
                axis=-1,
            )
            rtilde = vmap(lambda A, v: A @ v)(Phiinv, rs)
            etaprime = jnp.sum(r * rtilde)
            beta = etaprime / eta_val
            p = rtilde + beta * p
            eta_val = etaprime
            return (it + 1, r, p, eta_val, zs)

        val = while_loop(cond_fun, pcg_iterate_fun, init_val=(0, r, p, eta, zs_guess))

        zs = val[-1]
        pcg_debug_output = PCGDebugOutput(
            num_iterations=val[0], convergence_eta=val[-2]
        )
        return zs, pcg_debug_output

    @staticmethod
    def _solve_thomas(
        S: jnp.ndarray,
        gammas: jnp.ndarray,
    ) -> jnp.ndarray:
        """Solve block-tridiagonal system S λ = γ via Thomas algorithm (Riccati).

        Pure JAX implementation using jax.lax.scan. No callbacks, no host
        roundtrips. O(T n³) with two sequential scans (forward elimination,
        backward substitution).

        Reference: Jordana et al., "Structure-Exploiting SQP for MPC",
        Algorithm 1 (Thomas algorithm) / Proposition 2 (Riccati equivalence).

        Args:
            S: (T, n, 3n) block-tridiagonal storage [sub | diag | super].
            gammas: (T, n) right-hand side.

        Returns:
            lambdas: (T, n) solution.
        """
        T, n, _ = S.shape
        # Extract blocks
        A = S[:, :, :n]       # (T, n, n) sub-diagonal  (A[0] = 0)
        B = S[:, :, n:2*n]    # (T, n, n) diagonal
        C = S[:, :, 2*n:]     # (T, n, n) super-diagonal (C[T-1] = 0)

        # ── Forward elimination (t = 1 … T-1) ──────────────────────
        # Recurrence: W_t = A_t @ B̃_{t-1}^{-1}
        #             B̃_t = B_t - W_t @ C_{t-1}
        #             d̃_t = d_t - W_t @ d̃_{t-1}
        # We batch the solve: B̃_{t-1} @ [X_C | x_d] = [C_{t-1} | d̃_{t-1}]
        def _forward_step(carry, inputs):
            B_tilde, d_tilde = carry
            A_t, B_t, C_prev, d_t = inputs
            # Solve B̃ @ X = [C_prev | d̃] in one shot
            rhs = jnp.concatenate([C_prev, d_tilde[:, None]], axis=1)  # (n, n+1)
            X = jnp.linalg.solve(B_tilde, rhs)                        # (n, n+1)
            AX = A_t @ X                                               # (n, n+1)
            B_tilde_new = B_t - AX[:, :n]
            d_tilde_new = d_t - AX[:, n]
            return (B_tilde_new, d_tilde_new), (B_tilde_new, d_tilde_new)

        init = (B[0], gammas[0])
        (B_tilde_last, d_tilde_last), (B_tildes_mid, d_tildes_mid) = jax.lax.scan(
            _forward_step, init,
            (A[1:], B[1:], C[:-1], gammas[1:]),
        )
        # Stack all modified diagonals / rhs
        B_tildes = jnp.concatenate([B[0][None], B_tildes_mid], axis=0)       # (T, n, n)
        d_tildes = jnp.concatenate([gammas[0][None], d_tildes_mid], axis=0)  # (T, n)

        # ── Backward substitution (t = T-2 … 0) ───────────────────
        # λ_{T-1} = B̃_{T-1}^{-1} d̃_{T-1}
        # λ_t     = B̃_t^{-1} (d̃_t - C_t @ λ_{t+1})
        lambda_last = jnp.linalg.solve(B_tildes[-1], d_tildes[-1])  # (n,)

        def _backward_step(lambda_next, inputs):
            B_tilde_t, d_tilde_t, C_t = inputs
            lambda_t = jnp.linalg.solve(B_tilde_t, d_tilde_t - C_t @ lambda_next)
            return lambda_t, lambda_t

        _, lambdas_rev = jax.lax.scan(
            _backward_step, lambda_last,
            (B_tildes[:-1][::-1], d_tildes[:-1][::-1], C[:-1][::-1]),
        )
        # lambdas_rev is (T-1,n) in reverse time order
        lambdas = jnp.concatenate([lambdas_rev[::-1], lambda_last[None]], axis=0)
        return lambdas

    @staticmethod
    def _solve_pcr(S: jnp.ndarray, gammas: jnp.ndarray) -> jnp.ndarray:
        """Solve block-tridiagonal system S λ = γ via Parallel Cyclic Reduction.

        Pure JAX implementation using jax.lax.fori_loop. O(log₂ T) sequential
        depth with T parallel block operations at each level. GPU-friendly
        direct solver.

        At each of ⌈log₂ T⌉ levels, every equation i is updated in parallel
        by eliminating its left/right neighbors at stride s = 2^level.

        Args:
            S: (T, n, 3n) block-tridiagonal storage [sub | diag | super].
            gammas: (T, n) right-hand side.

        Returns:
            lambdas: (T, n) solution.
        """
        T, n, _ = S.shape
        num_levels = int(math.ceil(math.log2(max(T, 2))))

        A = S[:, :, :n]       # (T, n, n) sub-diagonal
        B = S[:, :, n:2*n]    # (T, n, n) diagonal
        C = S[:, :, 2*n:]     # (T, n, n) super-diagonal
        d = gammas             # (T, n)

        indices = jnp.arange(T)

        def _pcr_level(level, carry):
            A, B, C, d, stride = carry

            left_idx = jnp.clip(indices - stride, 0, T - 1)
            right_idx = jnp.clip(indices + stride, 0, T - 1)
            left_valid = (indices >= stride)[:, None, None]    # (T, 1, 1)
            right_valid = (indices + stride < T)[:, None, None]  # (T, 1, 1)

            # Gather neighbor blocks
            A_left = A[left_idx]    # (T, n, n)
            B_left = B[left_idx]    # (T, n, n)
            C_left = C[left_idx]    # (T, n, n)
            d_left = d[left_idx]    # (T, n)

            A_right = A[right_idx]  # (T, n, n)
            B_right = B[right_idx]  # (T, n, n)
            C_right = C[right_idx]  # (T, n, n)
            d_right = d[right_idx]  # (T, n)

            # Batched solve for left: B_left @ X_left = [A_left | C_left | d_left]
            rhs_left = jnp.concatenate(
                [A_left, C_left, d_left[:, :, None]], axis=2
            )  # (T, n, 2n+1)
            X_left = jnp.linalg.solve(B_left, rhs_left)  # (T, n, 2n+1)

            # Batched solve for right: B_right @ X_right = [A_right | C_right | d_right]
            rhs_right = jnp.concatenate(
                [A_right, C_right, d_right[:, :, None]], axis=2
            )  # (T, n, 2n+1)
            X_right = jnp.linalg.solve(B_right, rhs_right)  # (T, n, 2n+1)

            # α_i = -A_i @ B_{i-s}^{-1}  =>  α_i @ [cols] = -A_i @ X_left
            AX = A[:, :, :] @ X_left   # (T, n, 2n+1)
            # β_i = -C_i @ B_{i+s}^{-1}  =>  β_i @ [cols] = -C_i @ X_right
            CX = C[:, :, :] @ X_right  # (T, n, 2n+1)

            # Mask invalid contributions (boundary)
            AX = AX * left_valid
            CX = CX * right_valid

            # Extract contributions:
            # AX = A_i @ B_{i-s}^{-1} @ [A_{i-s} | C_{i-s} | d_{i-s}]
            # CX = C_i @ B_{i+s}^{-1} @ [A_{i+s} | C_{i+s} | d_{i+s}]
            # α_i = -A_i B_{i-s}^{-1}, β_i = -C_i B_{i+s}^{-1}
            A_new = -AX[:, :, :n]                          # α_i @ A_{i-s}
            C_new = -CX[:, :, n:2*n]                       # β_i @ C_{i+s}
            B_new = B - AX[:, :, n:2*n] - CX[:, :, :n]    # B_i + α_i @ C_{i-s} + β_i @ A_{i+s}
            d_new = d - AX[:, :, 2*n] - CX[:, :, 2*n]     # d_i + α_i @ d_{i-s} + β_i @ d_{i+s}

            return (A_new, B_new, C_new, d_new, stride * 2)

        init = (A, B, C, d, jnp.int32(1))
        _, B_final, _, d_final, _ = jax.lax.fori_loop(
            0, num_levels, _pcr_level, init
        )

        # After all levels, system is diagonal: λ_i = B_i^{-1} d_i
        return jax.vmap(jnp.linalg.solve)(B_final, d_final)

    def solve_linear_system_external(
        self,
        schur_complement_matrices: SchurComplementMatrices,
        schur_complement_gammas: jnp.ndarray,
        backend: str = "scipy",
    ) -> Tuple[jnp.ndarray, PCGDebugOutput]:
        """Solve the Schur system with a non-JAX backend (SciPy/cuDSS)."""
        S = schur_complement_matrices.S
        gammas = schur_complement_gammas
        zs = solve_block_tridi_system(S, gammas, backend=backend)
        zs = jnp.asarray(zs)
        pcg_debug_output = PCGDebugOutput(num_iterations=0, convergence_eta=0.0)
        return zs, pcg_debug_output
