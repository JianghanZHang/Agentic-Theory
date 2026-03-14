"""SQP solver using ADMM (primal PCG) to solve the convex QP each iteration."""
import copy
from functools import partial
from typing import Any, Dict, NamedTuple, Optional, Tuple

import jax
import jax.numpy as jnp

from diffmpc.problems.optimal_control_problem import OptimalControlProblem, SlackProblemAdapter
from diffmpc.solvers.admm import ADMMSolver, ADMMState
from diffmpc.solvers.qp_data import (
    QPData,
    QPCostBlocks,
    QPEqualityBlocks,
    QPInequalityBlocks,
    qpdata_from_ocp_blocks,
    scale_qp_data,
)
from diffmpc.solvers.admm.pcg_primal import (
    PCGPrimalOptimalControl,
)
from diffmpc.solvers.backward_kkt_jax import solve_backward_kkt
from diffmpc.solvers.linesearch import backtracking_linesearch, evaluate_constraints_with_bounds
from diffmpc.solvers.qp_utils import ZShape, pack_z
from diffmpc.utils.jax_utils import (
    project_matrix_onto_positive_semidefinite_cone,
    value_and_jacrev,
)
from diffmpc.utils.load_params import load_solver_params

DEFAULT_SOLVER_PARAMS = load_solver_params("sqp_admm.yaml")


class KKTState(NamedTuple):
    """KKT quantities for differentiability."""

    states: jnp.ndarray          # (N+1, nx)
    controls: jnp.ndarray        # (N+1, nu)
    slack: jnp.ndarray           # (N+1, m)
    y_f: jnp.ndarray             # (N+1, nx)
    y_ineq: jnp.ndarray          # (N+1, m)
    ineq_active_lower_idx: jnp.ndarray    # (N+1, m) bool
    ineq_active_upper_idx: jnp.ndarray    # (N+1, m) bool


class SolverStats(NamedTuple):
    """Solver statistics."""

    admm_num_iters: jnp.ndarray
    eq_constraints_violations: jnp.ndarray
    ineq_constraints_violations: jnp.ndarray
    convergence_errors: jnp.ndarray


class SQPADMMSolution(NamedTuple):
    states: jnp.ndarray  # (N+1, nx)
    controls: jnp.ndarray  # (N+1, nu)
    slack: jnp.ndarray  # (N+1, m)
    status: int  # 0 success, negative failure
    num_iter: jnp.ndarray
    convergence_error: jnp.ndarray
    admm_iters: jnp.ndarray  # (num_iter,)
    linesearch_alphas: Optional[jnp.ndarray] = None
    admm_state: Optional[ADMMState] = None
    solver_stats: Optional[SolverStats] = None
    dual_backward_guess: Optional[jnp.ndarray] = None
    kkt_state: Optional[KKTState] = None



def identify_active_inequalities(
    g: jnp.ndarray,
    l: jnp.ndarray,
    u: jnp.ndarray,
    eps_abs: float,
    eps_rel: float,
) -> Tuple[jnp.ndarray, jnp.ndarray]:
    """Identify active lower/upper inequality constraints.

    Uses the rule:
      min(g-l, u-g) <= eps_abs + eps_rel * |bound|.
    """
    g = jnp.asarray(g)
    l = jnp.asarray(l)
    u = jnp.asarray(u)
    delta_lower = g - l
    delta_upper = u - g
    use_upper = delta_upper < delta_lower
    bound_magnitude = jnp.where(use_upper, jnp.abs(u), jnp.abs(l))
    tol = eps_abs + eps_rel * bound_magnitude
    active = jnp.minimum(delta_lower, delta_upper) <= tol
    active_lower = jnp.logical_and(active, jnp.logical_not(use_upper))
    active_upper = jnp.logical_and(active, use_upper)
    return active_lower, active_upper

class SQPADMMSolver:
    """SQP solver that uses ADMM-PCG for the QP subproblem."""

    STATUS_SUCCESS = 0
    STATUS_FAILED = -1

    _supported_program_types = [
        OptimalControlProblem,
        SlackProblemAdapter
    ]

    def __init__(
        self,
        program: OptimalControlProblem,
        params: Optional[Dict[str, Any]] = None,
        name: str = "SQPADMMSolver",
        backward_backend: str = "pcg",
        forward_backend: str = "pcg",
        use_direct_backward: bool = False,
    ):
        self._program = program
        self._name = name
        self._params = DEFAULT_SOLVER_PARAMS if params is None else params
        self._backward_backend = backward_backend
        self._forward_backend = forward_backend
        self._use_direct_backward = use_direct_backward
        # Store slack params as concrete Python values at construction time
        # to avoid ConcretizationTypeError when traced inside jit/custom_vjp.
        self._use_slack = bool(getattr(program, '_use_slack_variables', False))
        self._slack_weight = float(program.params.get("slack_penalization_weight", 0.0))

        program_is_supported = any(
            isinstance(program, t) for t in self._supported_program_types
        )
        if not program_is_supported:
            # class instances with matching names are also supported
            supported_names = {t.__name__ for t in self._supported_program_types}
            if program.__class__.__name__ in supported_names:
                program_is_supported = True
        if not program_is_supported:
            raise NotImplementedError(str(program.name) + " is not supported.")

        self._zshape = ZShape(
            horizon=self.program.horizon,
            num_states=self.program.num_state_variables,
            num_controls=self.program.num_control_variables,
        )
        self._pcg = PCGPrimalOptimalControl(
            self.program.horizon,
            self.program.num_state_variables,
            self.program.num_control_variables,
            self.params["admm"]["pcg"],
        )
        self.solve = self.get_differentiable_solve_function()

    @property
    def program(self) -> OptimalControlProblem:
        return self._program

    @property
    def params(self) -> Dict:
        return self._params

    @property
    def name(self) -> str:
        return self._name

    @property
    def backward_backend(self) -> str:
        return self._backward_backend

    @property
    def forward_backend(self) -> str:
        return self._forward_backend
    
    @property
    def use_direct_backward(self) -> bool:
        return self._use_direct_backward
    
    def initial_guess(self, params: Optional[Dict[str, Any]] = None) -> SQPADMMSolution:
        """Returns an SQP-ADMM initial guess."""
        if params is None:
            params = self.program.params
        states, controls = self.program.initial_guess(params)
        max_iter = self.params["num_scp_iteration_max"]
        linesearch_alphas = None
        if self.params["linesearch"]:
            linesearch_alphas = jnp.zeros((max_iter,), dtype=states.dtype)
        solver_stats = SolverStats(
            admm_num_iters=jnp.zeros(max_iter, dtype=int),
            eq_constraints_violations=jnp.zeros(max_iter, dtype=float),
            ineq_constraints_violations=jnp.zeros(max_iter, dtype=float),
            convergence_errors=jnp.zeros(max_iter, dtype=float),
        )
        return SQPADMMSolution(
            states=states,
            controls=controls,
            slack=jnp.zeros((states.shape[0], self.program.num_inequality_constraints), dtype=states.dtype),
            status=self.STATUS_SUCCESS,
            num_iter=jnp.array(0),
            convergence_error=jnp.array(0.0, dtype=states.dtype),
            admm_iters=jnp.zeros((max_iter,), dtype=jnp.int32),
            linesearch_alphas=linesearch_alphas,
            admm_state=None,
            solver_stats=solver_stats,
            dual_backward_guess=None,
            kkt_state=None,
        )

    def make_params_with_weights(self, weights, problem_params=None):
        def _deep_merge_dict(dst, src):
            for key, value in src.items():
                if isinstance(value, dict) and isinstance(dst.get(key), dict):
                    _deep_merge_dict(dst[key], value)
                else:
                    dst[key] = value

        if problem_params is None:
            new_params = copy.deepcopy(self.program.params)
        else:
            new_params = copy.deepcopy(problem_params)
        _deep_merge_dict(new_params, weights)
        return new_params

    def get_differentiable_solve_function(self):
        """Create a differentiable solve function with captured solver.

        This wraps the SQP-ADMM solve in a JAX custom_vjp.
        """

        def _solve_impl_entry(
            initial_guess: SQPADMMSolution,
            problem_params: Dict[str, Any],
            weights: Any = {},
        ) -> SQPADMMSolution:
            problem_params = self.make_params_with_weights(weights, problem_params)
            return self._solve_impl(
                initial_guess.states,
                initial_guess.controls,
                problem_params,
                initial_guess.admm_state
            )

        @partial(jax.custom_vjp)
        def solve(
            initial_guess: SQPADMMSolution,
            problem_params: Dict[str, Any],
            weights: Any = {},
        ) -> SQPADMMSolution:
            return _solve_impl_entry(initial_guess, problem_params, weights)

        def _solve_fwd(initial_guess, problem_params, weights):
            solution = _solve_impl_entry(initial_guess, problem_params, weights)
            residual_for_backward_pass = (solution, weights, problem_params)
            return solution, residual_for_backward_pass

        def _compute_mixed_derivatives(
            problem_params,
            weights,
            states,
            controls,
            y_eq,
            y_ineq,
            active_lower,
            active_upper,
        ):
            def _cost_gradient(states, controls, params):
                def cost(states, controls):
                    return self.program.cost(states, controls, params)

                return jax.grad(cost, argnums=(0, 1))(states, controls)

            def _eq_constraints(states, controls, params):
                return self.program.equality_constraints(states, controls, params)

            def _active_ineq(states, controls, params):
                g, l, u = self.program.inequality_constraints(
                    states, controls, params
                )
                g = g.reshape((-1,))
                l = l.reshape((-1,))
                u = u.reshape((-1,))
                lower = active_lower.reshape((-1,)).astype(states.dtype)
                upper = active_upper.reshape((-1,)).astype(states.dtype)
                return lower * (g - l) + upper * (u - g)

            def _constraints_weighted(states, controls, params, lambdas, func):
                return lambdas.flatten() @ func(states, controls, params)

            def _constraints_weighted_dz(states, controls, params, lambdas, func):
                return jax.jacfwd(
                    lambda x, u: _constraints_weighted(x, u, params, lambdas, func),
                    argnums=(0, 1),
                )(states, controls)

            def _bundle(w):
                params = self.make_params_with_weights(w, problem_params)
                f_dx, f_du = _cost_gradient(states, controls, params)
                g_val = _eq_constraints(states, controls, params)
                h_val = _active_ineq(states, controls, params)
                g_dx, g_du = _constraints_weighted_dz(
                    states, controls, params, y_eq, _eq_constraints
                )
                h_dx, h_du = _constraints_weighted_dz(
                    states, controls, params, y_ineq, _active_ineq
                )
                return f_dx, f_du, g_val, h_val, g_dx, g_du, h_dx, h_du

            (
                f_dx_theta,
                f_du_theta,
                g_theta,
                h_theta,
                g_dx_theta_weighted,
                g_du_theta_weighted,
                h_dx_theta_weighted,
                h_du_theta_weighted,
            ) = jax.jacfwd(_bundle)(weights)

            flat_weights, _weights_treedef = jax.tree_util.tree_flatten(weights)

            def _flatten_theta(deriv_leaf, weight_leaf):
                weight_leaf = jnp.asarray(weight_leaf)
                if weight_leaf.ndim == 0:
                    return deriv_leaf[..., jnp.newaxis]
                out_ndim = deriv_leaf.ndim - weight_leaf.ndim
                out_shape = deriv_leaf.shape[:out_ndim]
                return jnp.reshape(deriv_leaf, out_shape + (weight_leaf.size,))

            flat_f_dx_theta, _ = jax.tree_util.tree_flatten(f_dx_theta)
            flat_f_du_theta, _ = jax.tree_util.tree_flatten(f_du_theta)
            flat_g_dx_theta_weighted, _ = jax.tree_util.tree_flatten(
                g_dx_theta_weighted
            )
            flat_g_du_theta_weighted, _ = jax.tree_util.tree_flatten(
                g_du_theta_weighted
            )
            flat_h_dx_theta_weighted, _ = jax.tree_util.tree_flatten(
                h_dx_theta_weighted
            )
            flat_h_du_theta_weighted, _ = jax.tree_util.tree_flatten(
                h_du_theta_weighted
            )
            flat_g_theta, _ = jax.tree_util.tree_flatten(g_theta)
            flat_h_theta, _ = jax.tree_util.tree_flatten(h_theta)

            flat_f_dx_theta = jnp.concatenate(
                [
                    _flatten_theta(deriv, w)
                    for deriv, w in zip(flat_f_dx_theta, flat_weights)
                ],
                axis=-1,
            )
            flat_f_du_theta = jnp.concatenate(
                [
                    _flatten_theta(deriv, w)
                    for deriv, w in zip(flat_f_du_theta, flat_weights)
                ],
                axis=-1,
            )
            flat_g_dx_theta_weighted = jnp.concatenate(
                [
                    _flatten_theta(deriv, w)
                    for deriv, w in zip(flat_g_dx_theta_weighted, flat_weights)
                ],
                axis=-1,
            )
            flat_g_du_theta_weighted = jnp.concatenate(
                [
                    _flatten_theta(deriv, w)
                    for deriv, w in zip(flat_g_du_theta_weighted, flat_weights)
                ],
                axis=-1,
            )
            flat_h_dx_theta_weighted = jnp.concatenate(
                [
                    _flatten_theta(deriv, w)
                    for deriv, w in zip(flat_h_dx_theta_weighted, flat_weights)
                ],
                axis=-1,
            )
            flat_h_du_theta_weighted = jnp.concatenate(
                [
                    _flatten_theta(deriv, w)
                    for deriv, w in zip(flat_h_du_theta_weighted, flat_weights)
                ],
                axis=-1,
            )
            flat_g_theta = jnp.concatenate(
                [
                    _flatten_theta(deriv, w)
                    for deriv, w in zip(flat_g_theta, flat_weights)
                ],
                axis=-1,
            )
            flat_h_theta = jnp.concatenate(
                [
                    _flatten_theta(deriv, w)
                    for deriv, w in zip(flat_h_theta, flat_weights)
                ],
                axis=-1,
            )
            return (
                flat_f_dx_theta,
                flat_f_du_theta,
                flat_g_dx_theta_weighted,
                flat_g_du_theta_weighted,
                flat_h_dx_theta_weighted,
                flat_h_du_theta_weighted,
                flat_g_theta,
                flat_h_theta,
            )

        def _pack_eq_multipliers(admm_state: ADMMState, params: Dict[str, Any]) -> jnp.ndarray:
            nx = self.program.num_state_variables
            y_f0 = admm_state.y_f_0
            if self.program._constrain_initial_control:
                y_f0_state = y_f0[:nx]
                y_u0 = y_f0[nx:]
                return jnp.concatenate(
                    [y_f0_state, admm_state.y_f_dyn.reshape(-1), y_u0], axis=0
                )
            return jnp.concatenate([y_f0, admm_state.y_f_dyn.reshape(-1)], axis=0)

        def _solve_bwd_admm(
            forward_solution: SQPADMMSolution,
            dl_dstates: jnp.ndarray,
            dl_dcontrols: jnp.ndarray,
            dl_dslack: jnp.ndarray,
            problem_params: Dict[str, Any],
            weights: Any,
        ):
            """Backward pass: solve the adjoint system via ADMM (step B1).

            Solves the reduced adjoint QP (cf. Double_envelope.tex, eq. adjoint_qp):
                min  ½ x̃ᵀ [D + γ Gₐᵀ Gₐ] x̃ - (∂L/∂z)ᵀ x̃
                s.t. C x̃ = 0
            Then recovers ỹ_g = γ Gₐ x̃ and computes dL/dθ via eq. dL_dtheta_expanded.

            Key differences from the forward QP:
            - Active inequalities become equalities (l=u=0), inactive rows zeroed.
            - rho_f_factor=1.0 (equal penalty on all constraints).
            - γ Gₐᵀ Gₐ enters via rho_ineq * GtG in compute_S_Phiinv.
            - Loss depends only on (x,u), so ∂L/∂ξ = 0.
            """
            kkt_state = forward_solution.kkt_state
            qp_data = self._build_qp_data(
                kkt_state.states, kkt_state.controls, problem_params
            )
            eq = qp_data.eq
            eq = QPEqualityBlocks(
                A0=eq.A0,
                A_minus=eq.A_minus,
                A_plus=eq.A_plus,
                c0=jnp.zeros_like(eq.c0),
                c=jnp.zeros_like(eq.c),
            )
            # Inequality → equality for active set (cf. Double_envelope.tex §4.4):
            # G_act = sign * G where sign = +1 (lower-active), -1 (upper-active), 0 (inactive).
            # With l=u=0 this enforces G_act x̃ = 0.
            if qp_data.ineq.G.shape[1] == 0:
                G_active = qp_data.ineq.G
            else:
                sign = (
                    kkt_state.ineq_active_lower_idx.astype(qp_data.ineq.G.dtype)
                    - kkt_state.ineq_active_upper_idx.astype(qp_data.ineq.G.dtype)
                )
                # active inequalities become equalities on Δg(x)=0; inactive rows are zeroed.
                G_active = qp_data.ineq.G * sign[..., jnp.newaxis]
            if qp_data.ineq.use_slack_variables and qp_data.ineq.G.shape[1] > 0:
                # slack variables => move active inequalities into the cost
                dl_rhs = jnp.concatenate(
                    [dl_dstates, dl_dcontrols], axis=-1
                )
                gamma = qp_data.ineq.slack_penalization_weight
                g_t = G_active
                dl_dslack = dl_dslack.reshape((dl_rhs.shape[0], -1))
                g_t_t = jnp.swapaxes(g_t, -1, -2)
                D = qp_data.cost.D + gamma * jnp.matmul(g_t_t, g_t)
                rhs_shift = jax.vmap(lambda A, v: A @ v)(g_t_t, dl_dslack)
                q = -(dl_rhs - rhs_shift)
                cost = QPCostBlocks(D=D, E=qp_data.cost.E, q=q)
                n = qp_data.cost.D.shape[-1]
                ineq = QPInequalityBlocks(
                    G=jnp.zeros((G_active.shape[0], 0, n), dtype=G_active.dtype),
                    l=jnp.zeros((G_active.shape[0], 0), dtype=G_active.dtype),
                    u=jnp.zeros((G_active.shape[0], 0), dtype=G_active.dtype),
                    slack_penalization_weight=gamma,
                    use_slack_variables=False,
                )
            else:
                # no slack variables
                q = -jnp.concatenate(
                    [dl_dstates, dl_dcontrols], axis=-1
                )
                cost = QPCostBlocks(D=qp_data.cost.D, E=qp_data.cost.E, q=q)
                ineq = QPInequalityBlocks(
                    G=G_active,
                    l=jnp.zeros_like(qp_data.ineq.l),
                    u=jnp.zeros_like(qp_data.ineq.u),
                    slack_penalization_weight=qp_data.ineq.slack_penalization_weight,
                    use_slack_variables=qp_data.ineq.use_slack_variables,
                )
            qp_back = QPData(cost=cost, eq=eq, ineq=ineq)

            # Backward ADMM uses rho_f_factor=1.0 (equal penalty on eq & ineq)
            # and rho_bar = rho * rho_f_factor_fwd (high rho to enforce equalities tightly).
            # The γ G_act^T G_act augmentation enters via rho_ineq * GtG in compute_S_Phiinv.
            admm_params = self.params["admm"]
            rho_active = admm_params["rho"] * admm_params.get(
                "rho_f_factor", admm_params.get("active_constraint_rho_factor", 1000.0)
            )
            admm_solver = ADMMSolver(
                pcg=self._pcg,
                sigma=admm_params["sigma"],
                max_iter=admm_params["max_iter"],
                eps_abs=admm_params.get("eps_abs", 1.0e-6),
                eps_rel=admm_params.get("eps_rel", 1.0e-6),
                rho_min=admm_params.get("rho_min", 1.0e-6),
                rho_max=admm_params.get("rho_max", 1.0e6),
                check_termination_every=admm_params.get("check_termination_every", 1),
                adapt_rho_every=admm_params.get("adapt_rho_every", 5),
                adaptive_rho_tolerance=admm_params.get("adaptive_rho_tolerance", 5.0),
                rho_f_factor=1.0,
                backend=self._backward_backend,
                use_slack=self._use_slack,
                slack_weight=self._slack_weight,
            )
            admm_state0 = admm_solver.initial_state(
                qp_data=qp_back,
                rho_bar=rho_active,
            )
            (dx_states, dx_controls), _, admm_state = admm_solver.solve(
                qp_data=qp_back,
                admm_state0=admm_state0,
                rho_bar=rho_active,
            )

            # ── Step B1': recover adjoint multipliers ──
            # ỹ_eq = λ̃ from backward ADMM dual variables
            y_eq_lin = _pack_eq_multipliers(admm_state, problem_params)
            if qp_data.ineq.use_slack_variables and qp_data.ineq.G.shape[1] > 0:
                # reconstruct y_g,active and xi_active from the reduced system
                active_mask = (
                    kkt_state.ineq_active_lower_idx | kkt_state.ineq_active_upper_idx
                ).astype(dl_dslack.dtype)
                dl_dslack_active = dl_dslack * active_mask
                dx = jnp.concatenate([dx_states, dx_controls], axis=-1)
                g_dx = jnp.matmul(G_active, dx[..., jnp.newaxis])[..., 0]
                gamma = qp_data.ineq.slack_penalization_weight
                y_ineq_lin = (dl_dslack_active + gamma * g_dx).reshape(-1)
                xi_lin = (dl_dslack_active - y_ineq_lin.reshape(dl_dslack_active.shape)) / gamma
                xi_active = kkt_state.slack * active_mask
                dL_dgamma = -jnp.sum(xi_active * xi_lin)
            else:
                y_ineq_lin = admm_state.y_g.reshape(-1)
                dL_dgamma = jnp.array(0.0, dtype=dl_dslack.dtype)

            # Forward multipliers (y_f*, y_g*) for the cross-derivative terms.
            # NOTE: `kkt_state.y_f` drops the initial-control multipliers when
            # `_constrain_initial_control` is enabled (it is stored as (N+1, nx)).
            # Use the ADMM state's packed multipliers instead to match the exact
            # equality constraint vector shape.
            if forward_solution.admm_state is not None:
                y_eq_star = _pack_eq_multipliers(
                    forward_solution.admm_state, problem_params
                )
                y_ineq_star = forward_solution.admm_state.y_g.reshape(-1)
            else:
                y_eq_star = kkt_state.y_f.reshape(-1)
                y_ineq_star = kkt_state.y_ineq.reshape(-1)

            if "slack_penalization_weight" in weights:
                # the gradient w.r.t. slack_penalization_weight is handled via dL_dgamma
                weights_for_mixed = {
                    k: v for k, v in weights.items() if k != "slack_penalization_weight"
                }
            else:
                weights_for_mixed = weights
            (
                f_dx_theta,
                f_du_theta,
                g_dx_theta_weighted,
                g_du_theta_weighted,
                h_dx_theta_weighted,
                h_du_theta_weighted,
                g_theta,
                h_theta,
            ) = _compute_mixed_derivatives(
                problem_params,
                weights_for_mixed,
                kkt_state.states,
                kkt_state.controls,
                y_eq_star,
                y_ineq_star,
                kkt_state.ineq_active_lower_idx,
                kkt_state.ineq_active_upper_idx,
            )

            # ── Step B2: parameter gradient (eq. dL_dtheta_expanded) ──
            # dL/dθ = -( ∇²_{xθ}L · x̃  +  [∂f/∂θ]ᵀ λ̃  +  [∂Δg/∂θ]ᵀ ỹ_g )
            # where ∇²_{xθ}L includes cross-terms from Lagrangian with forward multipliers.
            dL_dtheta = -(
                jnp.sum(
                    jnp.moveaxis(
                        f_dx_theta + g_dx_theta_weighted + h_dx_theta_weighted, -1, 0
                    )
                    * dx_states,
                    axis=(-2, -1),
                )
                + jnp.sum(
                    jnp.moveaxis(
                        f_du_theta + g_du_theta_weighted + h_du_theta_weighted, -1, 0
                    )
                    * dx_controls,
                    axis=(-2, -1),
                )
                + jnp.sum(
                    jnp.moveaxis(g_theta, -1, 0) * y_eq_lin,
                    axis=(-1),
                )
                + jnp.sum(
                    jnp.moveaxis(h_theta, -1, 0) * y_ineq_lin,
                    axis=(-1),
                )
            )
            return dL_dtheta, dL_dgamma

        def _solve_bwd_direct(
            forward_solution: SQPADMMSolution,
            dl_dstates: jnp.ndarray,
            dl_dcontrols: jnp.ndarray,
            dl_dslack: jnp.ndarray,
            problem_params: Dict[str, Any],
            weights: Any,
        ):
            """Backward pass: solve the adjoint system via direct KKT solver.
            """
            kkt_state = forward_solution.kkt_state
            qp_data = self._build_qp_data(
                kkt_state.states, kkt_state.controls, problem_params
            )
            eq = qp_data.eq
            eq = QPEqualityBlocks(
                A0=eq.A0,
                A_minus=eq.A_minus,
                A_plus=eq.A_plus,
                c0=jnp.zeros_like(eq.c0),
                c=jnp.zeros_like(eq.c),
            )
            # Inequality → equality for active set:
            # G_act = sign * G where sign = +1 (lower-active), -1 (upper-active), 0 (inactive).
            # With l=u=0 this enforces G_act x̃ = 0.
            if qp_data.ineq.G.shape[1] == 0:
                G_active = qp_data.ineq.G
            else:
                sign = (
                    kkt_state.ineq_active_lower_idx.astype(qp_data.ineq.G.dtype)
                    - kkt_state.ineq_active_upper_idx.astype(qp_data.ineq.G.dtype)
                )
                # active inequalities become equalities on Δg(x)=0; inactive rows are zeroed.
                G_active = qp_data.ineq.G * sign[..., jnp.newaxis]
            if qp_data.ineq.use_slack_variables and qp_data.ineq.G.shape[1] > 0:
                # slack variables => move active inequalities into the cost
                dl_rhs = jnp.concatenate(
                    [dl_dstates, dl_dcontrols], axis=-1
                )
                gamma = qp_data.ineq.slack_penalization_weight
                g_t = G_active
                dl_dslack = dl_dslack.reshape((dl_rhs.shape[0], -1))
                g_t_t = jnp.swapaxes(g_t, -1, -2)
                D = qp_data.cost.D + gamma * jnp.matmul(g_t_t, g_t)
                rhs_shift = jax.vmap(lambda A, v: A @ v)(g_t_t, dl_dslack)
                q = -(dl_rhs - rhs_shift)
                cost = QPCostBlocks(D=D, E=qp_data.cost.E, q=q)
                n = qp_data.cost.D.shape[-1]
                ineq = QPInequalityBlocks(
                    G=jnp.zeros((G_active.shape[0], 0, n), dtype=G_active.dtype),
                    l=jnp.zeros((G_active.shape[0], 0), dtype=G_active.dtype),
                    u=jnp.zeros((G_active.shape[0], 0), dtype=G_active.dtype),
                    slack_penalization_weight=gamma,
                    use_slack_variables=False,
                )
            else:
                # no slack variables
                q = -jnp.concatenate(
                    [dl_dstates, dl_dcontrols], axis=-1
                )
                cost = QPCostBlocks(D=qp_data.cost.D, E=qp_data.cost.E, q=q)
                ineq = QPInequalityBlocks(
                    G=G_active,
                    l=jnp.zeros_like(qp_data.ineq.l),
                    u=jnp.zeros_like(qp_data.ineq.u),
                    slack_penalization_weight=qp_data.ineq.slack_penalization_weight,
                    use_slack_variables=qp_data.ineq.use_slack_variables,
                )
            qp_back = QPData(cost=cost, eq=eq, ineq=ineq)

            # Calling direct KKT solver to solve the adjoint system.
            # Select solver based on backend configuration
            # JAX-pure dense solver (CUDA backends stripped for Apple Silicon)
            (dx_states, dx_controls), multipliers = solve_backward_kkt(
                qp_data=qp_back,
                zshape=self._zshape,
            )

            # ── Step B1': recover adjoint multipliers from KKT solve ──
            # Multipliers vector: [y_eq_lin; y_ineq_lin_active]
            
            # Extract equality constraint dimensions from backward QP
            nx = self.program.num_state_variables
            m0_back = qp_back.eq.A0.shape[0]   # initial constraint rows
            N_back = qp_back.eq.A_minus.shape[0]  # number of dynamics steps
            m_eq_dyn = qp_back.eq.A_minus.shape[1]  # dynamics constraint rows per step
            m_eq_total = m0_back + N_back * m_eq_dyn

            # Extract equality multipliers (always present)
            multipliers_eq_flat = (
                multipliers[:m_eq_total] if m_eq_total > 0
                else jnp.array([], dtype=multipliers.dtype)
            )

            # Reconstruct y_eq_lin to match _pack_eq_multipliers format
            y_f_0 = multipliers_eq_flat[:m0_back]
            y_f_dyn_flat = multipliers_eq_flat[m0_back:m0_back + N_back * m_eq_dyn]
            
            if self.program._constrain_initial_control:
                y_f0_state = y_f_0[:nx]
                y_u0 = y_f_0[nx:]
                y_eq_lin = jnp.concatenate([y_f0_state, y_f_dyn_flat, y_u0], axis=0)
            else:
                y_eq_lin = jnp.concatenate([y_f_0, y_f_dyn_flat], axis=0)

            if qp_data.ineq.use_slack_variables and qp_data.ineq.G.shape[1] > 0:
                # Ineq constraints are included in the cost.
                # Ineq multipliers determined from the augmented Lagrangian conditions.
                # dl_dslack was reshaped to (N+1, m_g) above.
                active_mask = (
                    kkt_state.ineq_active_lower_idx | kkt_state.ineq_active_upper_idx
                ).astype(dl_dslack.dtype)
                dl_dslack_active = dl_dslack * active_mask
                dx = jnp.concatenate([dx_states, dx_controls], axis=-1)
                g_dx = jnp.matmul(G_active, dx[..., jnp.newaxis])[..., 0]
                gamma = qp_data.ineq.slack_penalization_weight
                y_ineq_lin = (dl_dslack_active + gamma * g_dx).reshape(-1)
                xi_lin = (
                    (dl_dslack_active - y_ineq_lin.reshape(dl_dslack_active.shape))
                    / gamma
                )
                xi_active = kkt_state.slack * active_mask
                dL_dgamma = -jnp.sum(xi_active * xi_lin)
            else:
                # Standard: expand ineq multipliers from the active-set KKT solution.
                m_ineq_total = qp_back.ineq.G.shape[0] * qp_back.ineq.G.shape[1]  # (N+1)*m_g
                multipliers_ineq_active_flat = (
                    multipliers[m_eq_total:m_eq_total + m_ineq_total] if m_ineq_total > 0
                    else jnp.array([], dtype=multipliers.dtype)
                )
                active_flat = (
                    kkt_state.ineq_active_lower_idx | kkt_state.ineq_active_upper_idx
                ).reshape(-1).astype(bool)
                if m_ineq_total > 0:
                    cumsum_idx = jnp.cumsum(active_flat.astype(jnp.int32)) - 1
                    safe_idx = jnp.clip(cumsum_idx, 0, m_ineq_total - 1)
                    y_ineq_lin = jnp.where(
                        active_flat,
                        multipliers_ineq_active_flat[safe_idx],
                        0.0,
                    )
                else:
                    y_ineq_lin = jnp.array([], dtype=multipliers.dtype)
                dL_dgamma = jnp.array(0.0, dtype=dl_dslack.dtype)

            # Forward multipliers (y_f*, y_g*) for the cross-derivative terms.
            if forward_solution.admm_state is not None:
                y_eq_star = _pack_eq_multipliers(
                    forward_solution.admm_state, problem_params
                )
                y_ineq_star = forward_solution.admm_state.y_g.reshape(-1)
            else:
                y_eq_star = kkt_state.y_f.reshape(-1)
                y_ineq_star = kkt_state.y_ineq.reshape(-1)

            if "slack_penalization_weight" in weights:
                # Gradient w.r.t. slack_penalization_weight is handled via dL_dgamma
                weights_for_mixed = {
                    k: v for k, v in weights.items() if k != "slack_penalization_weight"
                }
            else:
                weights_for_mixed = weights
            (
                f_dx_theta,
                f_du_theta,
                g_dx_theta_weighted,
                g_du_theta_weighted,
                h_dx_theta_weighted,
                h_du_theta_weighted,
                g_theta,
                h_theta,
            ) = _compute_mixed_derivatives(
                problem_params,
                weights_for_mixed,
                kkt_state.states,
                kkt_state.controls,
                y_eq_star,
                y_ineq_star,
                kkt_state.ineq_active_lower_idx,
                kkt_state.ineq_active_upper_idx,
            )

            # ── Step B2: parameter gradient (eq. dL_dtheta_expanded) ──
            # dL/dθ = -( ∇²_{xθ}L · x̃  +  [∂f/∂θ]ᵀ λ̃  +  [∂Δg/∂θ]ᵀ ỹ_g )
            # where ∇²_{xθ}L includes cross-terms from Lagrangian with forward multipliers.
            dL_dtheta = -(
                jnp.sum(
                    jnp.moveaxis(
                        f_dx_theta + g_dx_theta_weighted + h_dx_theta_weighted, -1, 0
                    )
                    * dx_states,
                    axis=(-2, -1),
                )
                + jnp.sum(
                    jnp.moveaxis(
                        f_du_theta + g_du_theta_weighted + h_du_theta_weighted, -1, 0
                    )
                    * dx_controls,
                    axis=(-2, -1),
                )
                + jnp.sum(
                    jnp.moveaxis(g_theta, -1, 0) * y_eq_lin,
                    axis=(-1),
                )
                + jnp.sum(
                    jnp.moveaxis(h_theta, -1, 0) * y_ineq_lin,
                    axis=(-1),
                )
            )
            return dL_dtheta, dL_dgamma

        def _solve_bwd(residual_for_backward_pass, cotangents: SQPADMMSolution):
            """VJP backward pass with captured self."""
            solution, weights, problem_params = residual_for_backward_pass
            dl_dstates = cotangents.states
            dl_dcontrols = cotangents.controls
            dl_dslack = cotangents.slack
            problem_params = self.make_params_with_weights(weights, problem_params)

            # Conditionally use direct KKT solver or ADMM-based backward
            if self._use_direct_backward:
                dL_dtheta_flat, dL_dgamma = _solve_bwd_direct(
                    solution,
                    dl_dstates,
                    dl_dcontrols,
                    dl_dslack,
                    problem_params,
                    weights,
                )
            else:
                dL_dtheta_flat, dL_dgamma = _solve_bwd_admm(
                    solution,
                    dl_dstates,
                    dl_dcontrols,
                    dl_dslack,
                    problem_params,
                    weights,
                )
            if "slack_penalization_weight" in weights:
                # the gradient w.r.t. slack_penalization_weight is handled explicitly via dL_dgamma
                weights_no_slacks = {
                    k: v for k, v in weights.items() if k != "slack_penalization_weight"
                }
            else:
                weights_no_slacks = weights
            flat_weights, tree_def = jax.tree_util.tree_flatten(weights_no_slacks)
            flat_weights = [jnp.asarray(arr) for arr in flat_weights]
            flat_weight_lens = [arr.size for arr in flat_weights]
            start_idx = 0
            dL_dtheta_chunks = []
            for weight_leaf, length in zip(flat_weights, flat_weight_lens):
                chunk = dL_dtheta_flat[start_idx : start_idx + length]
                # Ensure the gradient leaf matches the primal leaf shape.
                # Scalars must be returned as 0-d arrays, not shape (1,).
                chunk = jnp.reshape(chunk, weight_leaf.shape)
                dL_dtheta_chunks.append(chunk)
                start_idx += length
            dL_dtheta_unflattened = jax.tree_util.tree_unflatten(
                tree_def, dL_dtheta_chunks
            )
            if "slack_penalization_weight" in weights:
                dL_dtheta_unflattened["slack_penalization_weight"] = dL_dgamma
            return (None, None, dL_dtheta_unflattened)

        solve.defvjp(_solve_fwd, _solve_bwd)
        return solve

    def _build_qp_data(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        problem_params: Dict[str, Any],
    ) -> QPData:
        D, E, q = self.program.get_cost_linearized_blocks(
            states, controls, problem_params
        )
        #D = jax.vmap(
        #    project_matrix_onto_positive_semidefinite_cone, in_axes=(0, None)
        #)(D, 1e-12)

        As_next, Bs_next, As, Bs, Cs = (
            self.program.get_dynamics_linearized_matrices(
                states, controls, problem_params
            )
        )

        ineq_blocks, ineq_l, ineq_u = self.program.get_inequalities_linearized_matrices(
            states, controls, problem_params
        )
        use_slack_variables = self.program._use_slack_variables
        slack_penalization_weight = jnp.asarray(
            problem_params.get("slack_penalization_weight", 0.0), dtype=states.dtype
        )

        initial_control = None
        if self.program._constrain_initial_control:
            if "initial_control" not in problem_params:
                raise ValueError(
                    "initial_control must be provided when constrain_initial_control "
                    "is True."
                )
            initial_control = problem_params["initial_control"]
            if initial_control.shape != (self.program.num_control_variables,):
                raise ValueError(
                    "initial_control has shape "
                    f"{initial_control.shape}, expected "
                    f"({self.program.num_control_variables},)"
                )
        qp_data = qpdata_from_ocp_blocks(
            D=D,
            E=E,
            q=q,
            As_next=As_next,
            Bs_next=Bs_next,
            As=As,
            Bs=Bs,
            Cs=Cs,
            ineq_blocks=ineq_blocks,
            ineq_l=ineq_l,
            ineq_u=ineq_u,
            use_slack_variables=use_slack_variables,
            slack_penalization_weight=slack_penalization_weight,
            initial_control=initial_control
        )
        if self.program._rescale_optimization_variables:
            _, _, _, _, state_diff, control_diff = self.program._get_rescaling_params(
                problem_params
            )
            qp_data = scale_qp_data(qp_data, state_diff, control_diff)
        return qp_data

    def _build_kkt_state(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        admm_state: ADMMState,
        ineq_values: jnp.ndarray,
        ineq_lower: jnp.ndarray,
        ineq_upper: jnp.ndarray,
    ) -> KKTState:
        if admm_state is None:
            y_f = jnp.zeros_like(states)
            y_ineq = jnp.zeros((states.shape[0], 0), dtype=states.dtype)
            slack = jnp.zeros_like(y_ineq)
        else:
            nx = self.program.num_state_variables
            y_f0 = admm_state.y_f_0
            if self.program._constrain_initial_control:
                y_f0 = y_f0[:nx]
            y_f = jnp.concatenate([y_f0[jnp.newaxis], admm_state.y_f_dyn], axis=0)
            y_ineq = admm_state.y_g
            slack = admm_state.xi_g

        g, l, u = ineq_values, ineq_lower, ineq_upper
        g = g.reshape((states.shape[0], -1))
        l = l.reshape((states.shape[0], -1))
        u = u.reshape((states.shape[0], -1))
        active_lower, active_upper = identify_active_inequalities(
            g, l, u, self.params["admm"]["eps_abs"], self.params["admm"]["eps_rel"]
        )
        return KKTState(
            states=states,
            controls=controls,
            slack=slack,
            y_f=y_f,
            y_ineq=y_ineq,
            ineq_active_lower_idx=active_lower,
            ineq_active_upper_idx=active_upper,
        )

    def _init_kkt_state(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        admm_state: ADMMState,
        num_ineq: int,
    ) -> KKTState:
        if admm_state is None:
            y_f = jnp.zeros_like(states)
            slack = jnp.zeros((states.shape[0], num_ineq), dtype=states.dtype)
        else:
            nx = self.program.num_state_variables
            y_f0 = admm_state.y_f_0
            if self.program._constrain_initial_control:
                y_f0 = y_f0[:nx]
            y_f = jnp.concatenate([y_f0[jnp.newaxis], admm_state.y_f_dyn], axis=0)
            slack = admm_state.xi_g
        empty = jnp.zeros((states.shape[0], num_ineq), dtype=states.dtype)
        return KKTState(
            states=states,
            controls=controls,
            slack=slack,
            y_f=y_f,
            y_ineq=empty,
            ineq_active_lower_idx=empty.astype(bool),
            ineq_active_upper_idx=empty.astype(bool),
        )

    def _evaluate_constraints_with_bounds(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        slacks: jnp.ndarray,
        problem_params: Dict[str, Any],
    ) -> Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray, jnp.ndarray, jnp.ndarray]:
        return evaluate_constraints_with_bounds(
            self.program, states, controls, slacks, problem_params
        )

    def linesearch(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        slacks: jnp.ndarray,
        states_new: jnp.ndarray,
        controls_new: jnp.ndarray,
        slacks_new: jnp.ndarray,
        problem_params: Dict[str, Any],
    ) -> Tuple[Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray], jnp.ndarray]:
        """Applies a linesearch along the SQP step direction via shared helper."""
        return backtracking_linesearch(
            self.program,
            problem_params,
            self.params,
            states,
            controls,
            slacks,
            states_new,
            controls_new,
            slacks_new,
        )

    def solve(
        self,
        initial_guess: SQPADMMSolution,
        problem_params: Dict[str, Any],
        weights: Any = {},
    ) -> SQPADMMSolution:
        problem_params = jax.lax.stop_gradient(problem_params)
        problem_params = self.make_params_with_weights(weights, problem_params)

        return self._solve_impl(
            initial_guess.states,
            initial_guess.controls,
            problem_params,
            initial_guess.admm_state
        )

    def _solve_impl(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        problem_params: Dict[str, Any],
        admm_state0: Optional[ADMMState] = None,
    ) -> SQPADMMSolution:
        max_iter = self.params["num_scp_iteration_max"]
        admm_iters = jnp.zeros((max_iter,), dtype=jnp.int32)
        linesearch_alphas = None
        if self.params["linesearch"]:
            linesearch_alphas = jnp.zeros((max_iter,), dtype=states.dtype)

        z_prev = pack_z(states, controls)
        convergence_error = jnp.array(jnp.inf, dtype=states.dtype)

        # Initialize stat arrays
        admm_num_iters = jnp.zeros(max_iter, dtype=int)
        eq_constraints_violations = jnp.zeros(max_iter, dtype=float)
        ineq_constraints_violations = jnp.zeros(max_iter, dtype=float)
        convergence_errors = jnp.zeros(max_iter, dtype=float)

        admm_params = self.params["admm"]
        admm_solver = ADMMSolver(
            pcg=self._pcg,
            sigma=admm_params["sigma"],
            max_iter=admm_params["max_iter"],
            eps_abs=admm_params.get("eps_abs", 1.0e-4),
            eps_rel=admm_params.get("eps_rel", 1.0e-3),
            rho_min=admm_params.get("rho_min", 1.0e-6),
            rho_max=admm_params.get("rho_max", 1.0e6),
            check_termination_every=admm_params.get("check_termination_every", 1),
            adapt_rho_every=admm_params.get("adapt_rho_every", 5),
            adaptive_rho_tolerance=admm_params.get("adaptive_rho_tolerance", 5.0),
            rho_f_factor=admm_params.get(
                "rho_f_factor", admm_params.get("active_constraint_rho_factor", 1000.0)
            ),
            backend=self._forward_backend,
            use_slack=self._use_slack,
            slack_weight=self._slack_weight,
        )

        if admm_state0 is None:
            admm_state0 = admm_solver.initial_state(
                qp_data=self._build_qp_data(states, controls, problem_params),
                rho_bar=admm_params["rho"],
                states0=jnp.zeros_like(states),
                controls0=jnp.zeros_like(controls),
            )

        class _SQPState(NamedTuple):
            it: jnp.ndarray
            states: jnp.ndarray
            controls: jnp.ndarray
            slacks: jnp.ndarray
            z_prev: jnp.ndarray
            conv: jnp.ndarray
            admm_iters: jnp.ndarray
            linesearch_alphas: Optional[jnp.ndarray]
            admm_state: ADMMState
            admm_num_iters: jnp.ndarray
            eq_constraints_violations: jnp.ndarray
            ineq_constraints_violations: jnp.ndarray
            convergence_errors: jnp.ndarray
            kkt_state: KKTState

        def body_fun(state: _SQPState) -> _SQPState:
            """Body function for SQP iteration."""
            # Setup QP problem
            qp_data = self._build_qp_data(
                state.states, state.controls, problem_params
            )
            
            # Solve QP via ADMM
            (states_new, controls_new), admm_stats, admm_state_new = admm_solver.solve(
                qp_data=qp_data,
                admm_state0=state.admm_state,
                rho_bar=admm_params["rho"],
                alpha=self.params["admm"].get("relaxation_parameter", 1.0),
            )
            if self.program._rescale_optimization_variables:
                states_new, controls_new = self.program.unscale_states_controls(
                    states_new, controls_new, problem_params
                )
            slacks_new = admm_state_new.xi_g
            admm_iters_next = state.admm_iters.at[state.it].set(admm_stats.num_iter)

            linesearch_alphas_next = state.linesearch_alphas
            if self.params["linesearch"]:
                (states_new, controls_new, slacks_new), alpha = self.linesearch(
                    state.states,
                    state.controls,
                    state.slacks,
                    states_new,
                    controls_new,
                    slacks_new,
                    problem_params,
                )
                linesearch_alphas_next = linesearch_alphas_next.at[state.it].set(alpha)

            z_new = pack_z(states_new, controls_new)
            conv = jnp.max(jnp.abs(z_new - state.z_prev))
            if slacks_new.shape[1] > 0:
                # non-empty inequality constraints
                conv += jnp.max(jnp.abs(slacks_new - state.slacks))

            (
                eq_constraints_l1_norm,
                ineq_constraints_l1_norm,
                ineq_values,
                ineq_lower,
                ineq_upper,
            ) = self._evaluate_constraints_with_bounds(
                states_new, controls_new, slacks_new, problem_params
            )
            
            # Store solver stat data
            admm_num_iters_next = state.admm_num_iters.at[state.it].set(admm_stats.num_iter)
            eq_constraints_violations_next = state.eq_constraints_violations.at[state.it].set(eq_constraints_l1_norm)
            ineq_constraints_violations_next = state.ineq_constraints_violations.at[state.it].set(ineq_constraints_l1_norm)
            convergence_errors_next = state.convergence_errors.at[state.it].set(conv)
            kkt_state_next = self._build_kkt_state(
                states_new,
                controls_new,
                admm_state_new,
                ineq_values=ineq_values,
                ineq_lower=ineq_lower,
                ineq_upper=ineq_upper,
            )

            return _SQPState(
                it=state.it + 1,
                states=states_new,
                controls=controls_new,
                slacks=slacks_new,
                z_prev=z_new,
                conv=conv,
                admm_iters=admm_iters_next,
                linesearch_alphas=linesearch_alphas_next,
                admm_state=admm_state_new,
                admm_num_iters=admm_num_iters_next,
                eq_constraints_violations=eq_constraints_violations_next,
                ineq_constraints_violations=ineq_constraints_violations_next,
                convergence_errors=convergence_errors_next,
                kkt_state=kkt_state_next,
            )

        def cond_fun(state: _SQPState) -> jnp.ndarray:
            _continue = jnp.logical_and(
                state.it < max_iter, state.conv > self.params["tol_convergence"]
            )
            _continue = jnp.logical_or(_continue, state.it < 1)
            return _continue

        num_ineq = int(admm_state0.y_g.shape[-1])
        init_kkt_state = self._init_kkt_state(
            states, controls, admm_state0, num_ineq
        )
        init_state = _SQPState(
            it=jnp.array(0),
            states=states,
            controls=controls,
            slacks=admm_state0.xi_g,
            z_prev=z_prev,
            conv=convergence_error,
            admm_iters=admm_iters,
            linesearch_alphas=linesearch_alphas,
            admm_state=admm_state0,
            admm_num_iters=admm_num_iters,
            eq_constraints_violations=eq_constraints_violations,
            ineq_constraints_violations=ineq_constraints_violations,
            convergence_errors=convergence_errors,
            kkt_state=init_kkt_state,
        )
        
        out = jax.lax.while_loop(cond_fun, body_fun, init_state)
        
        solver_stats = SolverStats(
            admm_num_iters=out.admm_num_iters,
            eq_constraints_violations=out.eq_constraints_violations,
            ineq_constraints_violations=out.ineq_constraints_violations,
            convergence_errors=out.convergence_errors,
        )
        return SQPADMMSolution(
            states=out.states,
            controls=out.controls,
            slack=out.admm_state.xi_g,
            status=self.STATUS_SUCCESS,
            num_iter=out.it,
            convergence_error=out.conv,
            admm_iters=out.admm_iters,
            linesearch_alphas=out.linesearch_alphas,
            admm_state=out.admm_state,
            solver_stats=solver_stats,
            kkt_state=out.kkt_state,
        )
