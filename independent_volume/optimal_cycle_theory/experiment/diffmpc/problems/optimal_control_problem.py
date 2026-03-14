"""Implements optimization problems."""

import copy
from typing import Any, Dict, Tuple

import jax
import jax.numpy as jnp
import numpy as np
from jax import vmap

from diffmpc.dynamics.base_dynamics import Dynamics
from diffmpc.dynamics.integrators import DiscretizationScheme, predict_next_state
from diffmpc.solvers.qp_utils import ZShape
from diffmpc.utils.jax_utils import value_and_jacfwd
from diffmpc.utils.load_params import check_parameters_dictionary_or_raise_errors


class OptimalControlProblem:
    """
    Optimal control problem class.

    Supports optional box constraints on states and controls:
        state_min_bound <= x_t <= state_max_bound
        control_min_bound <= u_t <= control_max_bound
    for t = 0..N.

    Bounds are treated as problem data only; solvers may or may not
    enforce them depending on backend.
    """

    def __init__(
        self,
        dynamics: Dynamics,
        params: Dict[str, Any] = None,
        check_parameters_are_valid: bool = True,
    ):
        """Initializes the class."""
        self._dynamics = dynamics
        self._name = "OptimalControlProblem"
        if check_parameters_are_valid:
            check_parameters_dictionary_or_raise_errors(params)
        params = copy.deepcopy(params)
        self._params = params
        self._num_variables = (
            self.num_control_variables + self.num_state_variables
        ) * (self.horizon + 1)
        self._active_state_bounds = None
        
        # Store boolean flags for JIT compatibility with if/else checks.
        # This allows using regular if statements instead of lax.cond
        self._rescale_optimization_variables = params.get("rescale_optimization_variables", False)
        self._constrain_initial_control = params.get("constrain_initial_control", False)
        self._penalize_control_reference = params.get("penalize_control_reference", False)
        self._use_slack_variables = params.get("use_slack_variables", False)
        self._discretization_scheme = DiscretizationScheme(
            params["discretization_scheme"]
        )
        self._active_control_bounds = None
        self._set_active_bounds(params)

        g = self.inequality_constraints(
            states=jnp.zeros((self.horizon + 1, self.num_state_variables)),
            controls=jnp.zeros((self.horizon + 1, self.num_control_variables)),
            params=params,
        )[0].reshape((self.horizon + 1, -1))
        self._num_inequality_constraints = g.shape[1]

    def _set_active_bounds(self, params: Dict[str, Any]) -> None:
        """Compute masks for active box bounds (finite entries)."""
        x_min, x_max, u_min, u_max = self.get_box_bounds(params)
        self._active_state_bounds = jnp.any(
            jnp.logical_or(x_min < -1e+6, x_max > 1e+6), axis=0
        )
        self._active_control_bounds = jnp.any(
            jnp.logical_or(u_min < -1e+6, u_max > 1e+6), axis=0
        )
        self._active_state_bounds = jnp.logical_not(self._active_state_bounds)
        self._active_control_bounds = jnp.logical_not(self._active_control_bounds)

    @property
    def dynamics(self) -> Dynamics:
        """Returns the dynamics of the class."""
        return self._dynamics

    @property
    def name(self) -> str:
        """Returns the program name (for solver compatibility)."""
        return self._name

    @property
    def params(self) -> Dict:
        """Returns a dictionary of parameters of the program."""
        return self._params

    @property
    def horizon(self) -> int:
        """Returns the problem horizon."""
        return int(self.params["horizon"])

    @property
    def discretization_scheme(self) -> DiscretizationScheme:
        """Returns the discretization scheme."""
        return self._discretization_scheme

    @property
    def num_variables(self) -> int:
        """Returns the number of optimization variables."""
        return self._num_variables

    @property
    def num_inequality_constraints(self) -> int:
        """Returns the number of inequality constraints."""
        num = self._num_inequality_constraints
        return num

    @property
    def num_state_variables(self) -> int:
        """Returns the number of state variables."""
        return self.dynamics.num_states

    @property
    def num_control_variables(self) -> int:
        """Returns the number of control variables."""
        return self.dynamics.num_controls

    def _get_default_bounds(self):
        """
        Return unconstrained bounds for states and controls.

        Returns:
            x_min, x_max: (N+1, nx)
            u_min, u_max: (N+1, nu)
        """
        N = self.horizon
        nx = self.num_state_variables
        nu = self.num_control_variables
        x_min = -jnp.inf * jnp.ones((N + 1, nx))
        x_max = jnp.inf * jnp.ones((N + 1, nx))
        u_min = -jnp.inf * jnp.ones((N + 1, nu))
        u_max = jnp.inf * jnp.ones((N + 1, nu))
        return x_min, x_max, u_min, u_max

    def _get_rescaling_params(self, params: Dict[str, Any]):
        """
        Return rescaling bounds and scale factors.

        Scaling convention (no offset):
            x_scaled = x_true / state_diff
            u_scaled = u_true / control_diff
        where state_diff = (state_max - state_min) / 2 (same for control).
        """
        # Use instance variable instead of params.get() for JIT compatibility
        if not self._rescale_optimization_variables:
            state_diff = jnp.ones((self.num_state_variables,))
            control_diff = jnp.ones((self.num_control_variables,))
            return None, None, None, None, state_diff, control_diff

        state_min = params["state_rescaling_min"]
        state_max = params["state_rescaling_max"]
        control_min = params["control_rescaling_min"]
        control_max = params["control_rescaling_max"]
        if state_min.shape != (self.num_state_variables,):
            raise ValueError(
                "state_rescaling_min must have shape "
                f"({self.num_state_variables},), got {state_min.shape}"
            )
        if state_max.shape != (self.num_state_variables,):
            raise ValueError(
                "state_rescaling_max must have shape "
                f"({self.num_state_variables},), got {state_max.shape}"
            )
        if control_min.shape != (self.num_control_variables,):
            raise ValueError(
                "control_rescaling_min must have shape "
                f"({self.num_control_variables},), got {control_min.shape}"
            )
        if control_max.shape != (self.num_control_variables,):
            raise ValueError(
                "control_rescaling_max must have shape "
                f"({self.num_control_variables},), got {control_max.shape}"
            )
        state_diff = (state_max - state_min) / 2.0
        control_diff = (control_max - control_min) / 2.0
        return state_min, state_max, control_min, control_max, state_diff, control_diff

    def scale_states_controls(
        self, states: jnp.ndarray, controls: jnp.ndarray, params: Dict[str, Any]
    ) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """
        Scale states and controls when rescaling is enabled.

        Inputs/outputs are trajectories in the same units, but scaled in magnitude.
        This applies only a multiplicative scale (no centering).
        """
        if self._rescale_optimization_variables:
            _, _, _, _, state_diff, control_diff = self._get_rescaling_params(params)
            return states / state_diff, controls / control_diff
        return states, controls

    def unscale_states_controls(
        self, states: jnp.ndarray, controls: jnp.ndarray, params: Dict[str, Any]
    ) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """
        Unscale states and controls when rescaling is enabled.

        This is the exact inverse of scale_states_controls.
        """
        if self._rescale_optimization_variables:
            _, _, _, _, state_diff, control_diff = self._get_rescaling_params(params)
            return states * state_diff, controls * control_diff
        return states, controls

    def get_box_bounds(self, params=None):
        """
        Return box bounds on states and controls.

        Bounds are optional. If not provided in params, they default
        to unconstrained.

        Accepted shapes:
            - state_min_bounds:   (nx,) or (N+1, nx)
            - state_max_bounds:   (nx,) or (N+1, nx)
            - control_min_bounds: (nu,) or (N+1, nu)
            - control_max_bounds: (nu,) or (N+1, nu)

        Returns:
            x_lower, x_upper, u_lower, u_upper
        """
        if params is None:
            params = self.params

        x_min, x_max, u_min, u_max = self._get_default_bounds()
        if "state_min_bounds" in params:
            x_min = params["state_min_bounds"]
        if "state_max_bounds" in params:
            x_max = params["state_max_bounds"]
        if "control_min_bounds" in params:
            u_min = params["control_min_bounds"]
        if "control_max_bounds" in params:
            u_max = params["control_max_bounds"]

        N = self.horizon
        nx = self.num_state_variables
        nu = self.num_control_variables

        def _reshape_bounds(name, arr, dim):
            """Reshape bounds to shape (N+1, dim), potentially duplicating over 1st axis."""
            if arr.ndim == 1:
                if arr.shape != (dim,):
                    raise ValueError(
                        f"{name} has shape {arr.shape}, expected ({dim},) or ({N+1},"
                        f" {dim})"
                    )
                return jnp.repeat(arr[None, :], repeats=(N + 1), axis=0)

            if arr.ndim == 2:
                if arr.shape != (N + 1, dim):
                    raise ValueError(
                        f"{name} has shape {arr.shape}, expected ({dim},) or ({N+1},"
                        f" {dim})"
                    )
                return arr

            raise ValueError(
                f"{name} must be rank-1 or rank-2 array, got ndim={arr.ndim}"
            )

        x_min = _reshape_bounds("state_min_bounds", x_min, nx)
        x_max = _reshape_bounds("state_max_bounds", x_max, nx)
        u_min = _reshape_bounds("control_min_bounds", u_min, nu)
        u_max = _reshape_bounds("control_max_bounds", u_max, nu)

        return x_min, x_max, u_min, u_max

    def step_inequality_constraints(
        self,
        state: jnp.ndarray,
        control: jnp.ndarray,
        params: Dict[str, Any],
    ) -> Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]:
        """
        Return per-timestep inequality constraints g(x,u), scaled if enabled.

        This method can be overridden in subclasses to implement nonlinear
        inequality constraints. By default it returns no constraints.

        Args:
            state: (nx,) state at time t.
            control: (nu,) control at time t.
            params: problem parameters. If box bounds are enabled, the base
                implementation expects per-step bounds in params under
                state_min_bounds/state_max_bounds/control_min_bounds/control_max_bounds,
                each of shape (nx,) or (nu,). If provided, masks under
                _state_bound_mask/_control_bound_mask select the constrained subset.
                The default masks are computed once at initialization; if the set
                of active bounds changes, re-instantiate the problem to avoid
                JAX shape changes.

        Returns:
            g: (m,) constraint values.
            l: (m,) lower bounds.
            u: (m,) upper bounds.
        """
        if (
            "state_min_bounds" not in params
            or "state_max_bounds" not in params
            or "control_min_bounds" not in params
            or "control_max_bounds" not in params
        ):
            return jnp.zeros((0,)), jnp.zeros((0,)), jnp.zeros((0,))

        x_min = jnp.asarray(params["state_min_bounds"])
        x_max = jnp.asarray(params["state_max_bounds"])
        u_min = jnp.asarray(params["control_min_bounds"])
        u_max = jnp.asarray(params["control_max_bounds"])

        state_mask = params.get("_state_bound_mask", self._active_state_bounds)
        control_mask = params.get("_control_bound_mask", self._active_control_bounds)
        if state_mask is not None:
            state = state[state_mask]
            x_min = x_min[state_mask]
            x_max = x_max[state_mask]
        if control_mask is not None:
            control = control[control_mask]
            u_min = u_min[control_mask]
            u_max = u_max[control_mask]

        g = jnp.concatenate([state, control], axis=0)
        l = jnp.concatenate([x_min, u_min], axis=0)
        u = jnp.concatenate([x_max, u_max], axis=0)

        if self._rescale_optimization_variables:
            _, _, _, _, state_diff, control_diff = self._get_rescaling_params(params)
            if state_mask is not None:
                state_diff = state_diff[state_mask]
            if control_mask is not None:
                control_diff = control_diff[control_mask]
            scale_vec = jnp.concatenate([state_diff, control_diff], axis=0)
            g = g / scale_vec
            l = l / scale_vec
            u = u / scale_vec

        return g, l, u

    def inequality_constraints(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        params: Dict[str, Any],
    ) -> Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]:
        """
        Return per-timestep inequality constraints l <= g(x,u) <= u.

        Returns arrays with shape (N+1, m), where m is the per-step number of
        inequality constraints returned by step_inequality_constraints.
        """
        x_min, x_max, u_min, u_max = self.get_box_bounds(params)
        state_mask = self._active_state_bounds
        control_mask = self._active_control_bounds

        step_params = dict(params)
        step_params["_state_bound_mask"] = state_mask
        step_params["_control_bound_mask"] = control_mask
        step_params["state_min_bounds"] = x_min[0]
        step_params["state_max_bounds"] = x_max[0]
        step_params["control_min_bounds"] = u_min[0]
        step_params["control_max_bounds"] = u_max[0]
        g0, l0, u0 = self.step_inequality_constraints(
            states[0], controls[0], step_params
        )
        if g0.size == 0:
            return jnp.zeros((0,)), jnp.zeros((0,)), jnp.zeros((0,))

        def _step_vals(state, control, x_min_t, x_max_t, u_min_t, u_max_t):
            step_params = dict(params)
            step_params["_state_bound_mask"] = state_mask
            step_params["_control_bound_mask"] = control_mask
            step_params["state_min_bounds"] = x_min_t
            step_params["state_max_bounds"] = x_max_t
            step_params["control_min_bounds"] = u_min_t
            step_params["control_max_bounds"] = u_max_t
            return self.step_inequality_constraints(state, control, step_params)

        g_all, l_all, u_all = vmap(_step_vals)(
            states, controls, x_min, x_max, u_min, u_max
        )
        return g_all, l_all, u_all

    def get_inequalities_linearized_matrices(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        params: Dict[str, Any],
    ) -> Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]:
        """
        Linearize nonlinear inequality constraints and return l <= A z <= u.

        This combines linearizations of step_inequality_constraints around
        (states, controls), including box bounds when enabled.

        Returns:
            A_ineq_blocks: (N+1, m, nx+nu) local blocks per timestep.
                If no constraints are active, returns shape (0, 0, nx+nu).
            l_ineq: (N+1, m)
            u_ineq: (N+1, m)
        """
        x_min, x_max, u_min, u_max = self.get_box_bounds(params)
        state_mask = self._active_state_bounds
        control_mask = self._active_control_bounds
        step_params = dict(params)
        step_params["_state_bound_mask"] = state_mask
        step_params["_control_bound_mask"] = control_mask
        def _linearize_step(state_t, control_t, x_min_t, x_max_t, u_min_t, u_max_t):
            step_params = dict(params)
            step_params["_state_bound_mask"] = state_mask
            step_params["_control_bound_mask"] = control_mask
            step_params["state_min_bounds"] = x_min_t
            step_params["state_max_bounds"] = x_max_t
            step_params["control_min_bounds"] = u_min_t
            step_params["control_max_bounds"] = u_max_t
            g_t, l_t, u_t = self.step_inequality_constraints(
                state_t, control_t, step_params
            )
            state_control = jnp.concatenate([state_t, control_t], axis=0)

            def _g_only(sc):
                s = sc[: self.num_state_variables]
                c = sc[self.num_state_variables :]
                g_val, _, _ = self.step_inequality_constraints(s, c, step_params)
                return g_val

            g_val, jac = value_and_jacfwd(_g_only, state_control)
            Jx = jac[:, : self.num_state_variables]
            Ju = jac[:, self.num_state_variables :]
            offset = g_val - (Jx @ state_t + Ju @ control_t)
            l_lin = l_t - offset
            u_lin = u_t - offset
            return Jx, Ju, l_lin, u_lin

        Jx_all, Ju_all, l_all, u_all = vmap(_linearize_step)(
            states, controls, x_min, x_max, u_min, u_max
        )
        A_nl_blocks = jnp.concatenate([Jx_all, Ju_all], axis=-1)
        return A_nl_blocks, l_all, u_all

    def _get_dynamics_params_sequence(
        self, params: Dict[str, Any], num_steps: int
    ) -> Dict[str, jnp.ndarray]:
        """
        Build per-step dynamics params for dynamics.state_dot.

        If "dynamics_state_dot_params" is missing, returns {}.
        Scalars are broadcast to (num_steps,).
        1D arrays whose length matches num_steps or num_steps+1 are ambiguous and raise a value error.
        2D+ arrays with leading dimension num_steps/num_steps+1 are sliced to num_steps.
        Other arrays are broadcast across time.

        Warning: A constant matrix of size (dim1, dim2) with dim1=num_steps is assumed
        to be a time-varying vector, causing a (potentially silent) error downstream. 
        In this case, pass it as a tensor of size (num_steps, dim1, dim2).
        """
        dyn_params = params.get("dynamics_state_dot_params")
        if dyn_params is None:
            return {}
        out: Dict[str, jnp.ndarray] = {}
        for key, value in dyn_params.items():
            if isinstance(value, jnp.ndarray):
                if value.ndim == 0:
                    out[key] = jnp.broadcast_to(value, (num_steps,))
                elif value.ndim == 1:
                    if value.shape[0] in (num_steps, num_steps + 1):
                        # length matches time axis => potential bug (can't distinguish between
                        # a vector of length horizon and scalar changing over the horizon)
                        raise ValueError(
                            f"Ambiguous 1D dynamics param '{key}': length {value.shape[0]} "
                            f"matches horizon ({num_steps}). Use 2D shape (num_steps, dim) for "
                            "time-varying vectors to avoid ambiguities / potential bugs."
                        )
                    else:
                        # Treat 1D vectors as constants; time-varying vectors should be 2D.
                        out[key] = jnp.broadcast_to(value, (num_steps,) + value.shape)
                elif value.shape[0] == num_steps + 1:
                    out[key] = value[:num_steps]
                elif value.shape[0] == num_steps:
                    out[key] = value
                else:
                    out[key] = jnp.broadcast_to(value, (num_steps,) + value.shape)
            else:
                value_arr = jnp.asarray(value)
                if value_arr.ndim == 0:
                    out[key] = jnp.broadcast_to(value_arr, (num_steps,))
                else:
                    out[key] = jnp.broadcast_to(
                        value_arr, (num_steps,) + value_arr.shape
                    )
        # collapse scalar time-series encoded as (N, 1) into (N,)
        for key, value in out.items():
            if isinstance(value, jnp.ndarray) and value.ndim == 2 and value.shape[1] == 1:
                out[key] = value[:, 0]
        return out

    def _get_control_rate_weights(
        self, params: Dict[str, Any], apply_rescaling: bool = True
    ) -> jnp.ndarray:
        """
        Return control-rate penalty weights Rd as (N, nu, nu).

        Accepted shapes:
            - (nu,)
            - (nu, nu)
            - (N, nu)
            - (N, nu, nu)
        Returns:
            Rd - (N, nu, nu), in scaled units if apply_rescaling=True.
        """
        N = self.horizon
        nu = self.num_control_variables
        rd = jnp.array(params["weights_penalization_control_rate"])

        if rd.ndim == 1 and rd.shape == (nu,):
            rd = jnp.diag(rd)
            rd = jnp.repeat(rd[None], repeats=N, axis=0)
        elif rd.ndim == 2 and rd.shape == (nu, nu):
            rd = jnp.repeat(rd[None], repeats=N, axis=0)
        elif rd.ndim == 2 and rd.shape == (N, nu):
            rd = vmap(jnp.diag)(rd)
        elif rd.ndim == 3 and rd.shape == (N, nu, nu):
            rd = rd
        else:
            raise ValueError(
                "weights_penalization_control_rate shape must be (nu,), (nu, nu), (N, nu),"
                " or (N, nu, nu)."
            )

        if apply_rescaling and self._rescale_optimization_variables:
            _, _, _, _, _, control_diff = self._get_rescaling_params(params)
            rd = control_diff**2 * rd
        return rd

    def initial_guess(
        self, params: Dict[str, Any] = None
    ) -> Tuple[jnp.array, jnp.array]:
        """Returns an initial guess for the solution."""
        if params is None:
            params = self.params
        x_initial = params["initial_state"]
        x_final = params["final_state"]
        horizon = self.horizon

        # straight-line initial guess
        state_matrix = jnp.zeros((horizon + 1, self.num_state_variables))
        for t in range(horizon + 1):
            alpha1 = (horizon - t) / horizon
            alpha2 = t / horizon
            state_matrix = state_matrix.at[t].set(
                x_initial * alpha1 + x_final * alpha2 + 1e-6
            )
        # zero initial guess
        control_matrix = jnp.zeros((horizon + 1, self.num_control_variables)) + 1e-6
        return state_matrix, control_matrix

    def equality_constraints(
        self, states: jnp.array, controls: jnp.array, params: Dict[str, Any]
    ) -> jnp.array:
        """Returns equality constraints.

        Returns h(x) corresponding to the
        equality constraints h(x) = 0.

        Args:
            states: state trajectory,
                (N + 1, nx) array
            controls: control trajectory,
                (N + 1, nu) array
            params: dictionary of parameters of the optimal control problem,
                (key=string, value=Any)

        Returns:
            h_value: value of h(x),
                (_num_equality_constraints, ) array
        """
        horizon = self.horizon
        # initial state is fixed
        initial_state_constraints = states[0] - params["initial_state"]

        # dynamics constraints
        if self.discretization_scheme == DiscretizationScheme.IMPLICIT:
            controls_next = controls[1:]
        else:
            controls_next = controls[:horizon]
        dynamics_params = self._get_dynamics_params_sequence(params, horizon)
        next_states = vmap(
            predict_next_state,
            in_axes=(None, None, None, 0, 0, 0, 0),
        )(
            self.dynamics,
            params["discretization_resolution"],
            self.discretization_scheme,
            dynamics_params,
            states[:horizon],
            controls[:horizon],
            controls_next,
        )
        dynamics_constraints = next_states - states[1:]

        # all equality constraints
        constraints = jnp.concatenate([initial_state_constraints[jnp.newaxis], dynamics_constraints], axis=0)

        if self._rescale_optimization_variables:
            _, _, _, _, state_diff, control_diff = self._get_rescaling_params(params)
            constraints = constraints / state_diff

        constraints = constraints.flatten()

        # initial control constraints
        u0_constraint = None
        if self._constrain_initial_control:
            init_control = params["initial_control"]
            if init_control.shape != (self.num_control_variables,):
                raise ValueError(
                    "initial_control has shape "
                    f"{init_control.shape}, expected ({self.num_control_variables},)"
                )
            u0_constraint = controls[0] - init_control
            if self._rescale_optimization_variables:
                u0_constraint = u0_constraint / control_diff
            constraints = jnp.concatenate([constraints, u0_constraint])

        return constraints

    def step_cost(
        self, state: jnp.array, control: jnp.array, params: Dict[str, Any]
    ) -> float:
        """Returns step cost to minimize."""
        nu = self.num_control_variables
        reference_state = params["reference_state_trajectory"]
        reference_control = params["reference_control_trajectory"]
        weights_x_ref = params["weights_penalization_reference_state_trajectory"]
        weights_u_norm = params["weights_penalization_control_squared"]

        if self._penalize_control_reference:
            reference = jnp.concatenate([reference_state, reference_control], axis=-1)
        else:
            reference = jnp.concatenate([reference_state, jnp.zeros(nu)], axis=-1)
        weights_ref = jnp.concatenate([weights_x_ref, weights_u_norm], axis=-1)

        state_control = jnp.concatenate([state, control], axis=-1)
        total_cost = weights_ref * (state_control - reference) ** 2
        total_cost = jnp.sum(total_cost)
        return total_cost

    def control_rate_cost(
        self, control: jnp.array, params: Dict[str, Any]
    ) -> float:
        """Control-only cost evaluated in true (unscaled) coordinates."""
        weights_u_norm = params["weights_penalization_control_squared"]
        reference_control = params["reference_control_trajectory"]
        if self._penalize_control_reference:
            ref = reference_control
        else:
            ref = jnp.zeros_like(control)
        total_cost = jnp.sum(weights_u_norm * (control - ref) ** 2)
        return total_cost

    def final_cost(self, state: jnp.array, params: Dict[str, Any]) -> float:
        """Final cost evaluated in true (unscaled) coordinates."""
        weights_x_ref = params["weights_penalization_reference_state_trajectory"]
        weights_x_final = params["weights_penalization_final_state"]
        weights_x_final_linear = params.get(
            "weights_linear_penalization_final_state", jnp.zeros_like(state)
        )
        weights_ref = weights_x_ref + weights_x_final
        total_cost = weights_ref * (state - params["final_state"]) ** 2
        total_cost = jnp.sum(total_cost)
        total_cost = total_cost + jnp.sum(weights_x_final_linear * state)
        return total_cost

    def cost(
        self, states: jnp.array, controls: jnp.array, params: Dict[str, Any]
    ) -> float:
        """Returns total cost to minimize.

        Args:
            states: state trajectory,
                (N + 1, nx) array
            controls: control trajectory,
                (N + 1, nu) array
            params: dictionary of parameters of the optimal control problem,
                (key=string, value=Any)

        Returns:
            cost: value of the cost in true (unscaled) units,
                (float)
        """
        keys_reference = ["reference_state_trajectory", "reference_control_trajectory"]
        keys_weights = [
            "weights_penalization_reference_state_trajectory",
            "weights_penalization_control_squared",
            "weights_penalization_final_state",
            "final_state",
        ]
        step_cost_params = {
            **{key: params[key][:-1] for key in keys_reference},
            **{
                key: jnp.repeat(params[key][None], repeats=self.horizon, axis=0)
                for key in keys_weights
            },
        }
        final_cost_params = {
            **{key: params[key][-1] for key in keys_reference},
            **{key: params[key] for key in keys_weights},
            "weights_linear_penalization_final_state": params.get(
                "weights_linear_penalization_final_state",
                jnp.zeros((self.num_state_variables,), dtype=states.dtype),
            ),
        }
        step_costs = vmap(self.step_cost)(states[:-1], controls[:-1], step_cost_params)
        total_cost = jnp.sum(step_costs) + self.final_cost(
            states[-1], final_cost_params
        )
        # control rate cost
        rd = self._get_control_rate_weights(params, apply_rescaling=False)
        du = controls[1:] - controls[:-1]
        rd_du = jnp.matmul(rd, du[..., None])[..., 0]
        rate_cost = 0.5 * jnp.sum(jnp.sum(du * rd_du, axis=1))
        total_cost = total_cost + rate_cost
        return total_cost

    def get_cost_linearized_matrices(
        self,
        states: jnp.array,
        controls: jnp.array,
        params: Dict[str, Any],
    ) -> Tuple[jnp.ndarray]:
        """
        Returns cost terms (QN, qN, Q, q, R, r) corresponding to the cost
        cost = 0.5 x_N^T Q_N x_N + q_N x_N
               + sum_{t=0}^N 0.5 x_t^T Q_t x_t + q_t x_t
               + sum_{t=0}^{N-1} 0.5 u_t^T R_t u_t + r_t u_t.

        Args:
            states: state trajectory,
                (N + 1, nx) array
            controls: control trajectory,
                (N + 1, nu) array
            problem_params: dictionary of parameters of the optimal control problem,
                (key=string, value=Any)

        Returns:
            (in true/unscaled units)
            QN: terminal quadratic state cost matrices,
                (num_states, num_states) array
            qN: terminal vector state cost matrices,
                (num_states) array
            Q: quadratic state cost matrices,
                (horizon, num_states, num_states) array
            q: state cost vectors,
                (horizon, num_states) array
            R: quadratic control cost matrices,
                (horizon, num_controls, num_controls) array
            r: control cost vectors,
                (horizon, num_controls) array
        """
        keys_reference = ["reference_state_trajectory", "reference_control_trajectory"]
        keys_weights = [
            "weights_penalization_reference_state_trajectory",
            "weights_penalization_control_squared",
            "weights_penalization_final_state",
            "final_state",
        ]
        step_cost_params = {
            **{key: params[key][:-1] for key in keys_reference},
            **{
                key: jnp.repeat(params[key][None], repeats=self.horizon, axis=0)
                for key in keys_weights
            },
        }
        final_cost_params = {
            **{key: params[key][-1] for key in keys_reference},
            **{key: params[key] for key in keys_weights},
            "weights_linear_penalization_final_state": params.get(
                "weights_linear_penalization_final_state",
                jnp.zeros((self.num_state_variables,), dtype=states.dtype),
            ),
        }

        Jt_dx, Jt_du = vmap(jax.grad(self.step_cost, argnums=(0, 1)))(
            states[:-1], controls[:-1], step_cost_params
        )
        Ht_dxx = vmap(jax.hessian(self.step_cost, argnums=(0)))(
            states[:-1], controls[:-1], step_cost_params
        )
        Ht_duu = vmap(jax.hessian(self.step_cost, argnums=(1)))(
            states[:-1], controls[:-1], step_cost_params
        )
        JT_dx = jax.grad(self.final_cost, argnums=(0))(states[-1], final_cost_params)
        HT_dxx = jax.hessian(self.final_cost, argnums=(0))(
            states[-1], final_cost_params
        )

        # c(x) = c(xbar) + J(xbar) (x-xbar) + 1/2 (x-xbar)^T H(xbar) (x-xbar)
        #      = constants(xbar) + (J(xbar) - xbar^T H(xbar)) x + 1/2 x^T H(xbar) x
        QN = HT_dxx
        qN = JT_dx - jnp.dot(states[-1], HT_dxx)
        Q = Ht_dxx
        q = vmap(lambda H, J, x: J - jnp.dot(x, H))(Ht_dxx, Jt_dx, states[:-1])
        R = Ht_duu
        r = vmap(lambda H, J, u: J - jnp.dot(u, H))(Ht_duu, Jt_du, controls[:-1])
        return QN, qN, Q, q, R, r

    def get_cost_linearized_blocks(
        self,
        states: jnp.array,
        controls: jnp.array,
        params: Dict[str, Any],
    ) -> Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]:
        """
        Returns cost blocks (D, E, q) for the block-tridiagonal QP Hessian P
        in true (unscaled) units.

        This follows the stage-coupled formulation where each step cost
        depends on (x_t, u_t, x_{t+1}, u_{t+1}) via control-rate penalties.
        """
        N = self.horizon
        nx = self.num_state_variables
        nu = self.num_control_variables
        n = nx + nu

        step_cost_params = {
            "reference_state_trajectory": params["reference_state_trajectory"][:-1],
            "reference_control_trajectory": params["reference_control_trajectory"][:-1],
            "weights_penalization_reference_state_trajectory": jnp.repeat(
                params["weights_penalization_reference_state_trajectory"][None],
                repeats=N,
                axis=0,
            ),
            "weights_penalization_control_squared": jnp.repeat(
                params["weights_penalization_control_squared"][None],
                repeats=N,
                axis=0,
            ),
        }
        final_cost_params = {
            "reference_state_trajectory": params["reference_state_trajectory"][-1],
            "reference_control_trajectory": params["reference_control_trajectory"][-1],
            "weights_penalization_reference_state_trajectory": params[
                "weights_penalization_reference_state_trajectory"
            ],
            "weights_penalization_control_squared": params[
                "weights_penalization_control_squared"
            ],
            "weights_penalization_final_state": params[
                "weights_penalization_final_state"
            ],
            "weights_linear_penalization_final_state": params.get(
                "weights_linear_penalization_final_state",
                jnp.zeros((self.num_state_variables,), dtype=states.dtype),
            ),
            "final_state": params["final_state"],
        }
        rd = self._get_control_rate_weights(params, apply_rescaling=False)

        x_blocks = jnp.concatenate([states, controls], axis=-1)
        x_pairs = jnp.concatenate([x_blocks[:-1], x_blocks[1:]], axis=-1)

        def stage_cost(x_pair, step_params_t, rd_t):
            x_t = x_pair[:n]
            x_tp1 = x_pair[n:]
            state_t = x_t[:nx]
            control_t = x_t[nx:]
            state_tp1 = x_tp1[:nx]
            control_tp1 = x_tp1[nx:]
            cost = self.step_cost(state_t, control_t, step_params_t)
            du = control_tp1 - control_t
            cost = cost + 0.5 * (du @ (rd_t @ du))
            return cost

        def terminal_cost(x_t):
            state_t = x_t[:nx]
            control_t = x_t[nx:]
            cost = self.final_cost(state_t, final_cost_params)
            cost = cost + self.control_rate_cost(control_t, final_cost_params)
            return cost

        stage_grad = jax.grad(stage_cost)
        stage_hess = jax.hessian(stage_cost)
        grads = vmap(stage_grad)(x_pairs, step_cost_params, rd)
        hessians = vmap(stage_hess)(x_pairs, step_cost_params, rd)

        H_minus = hessians[:, :n, :n]
        H_plus = hessians[:, n:, n:]
        H_pm = hessians[:, :n, n:]
        g_minus = grads[:, :n]
        g_plus = grads[:, n:]

        x_t = x_blocks[:-1]
        x_tp1 = x_blocks[1:]
        q_minus = g_minus - vmap(lambda Hm, Hpm, xt, xtp1: Hm @ xt + Hpm @ xtp1)(
            H_minus, H_pm, x_t, x_tp1
        )
        q_plus = g_plus - vmap(
            lambda Hp, Hpm, xt, xtp1: Hpm.T @ xt + Hp @ xtp1
        )(H_plus, H_pm, x_t, x_tp1)

        term_grad = jax.grad(terminal_cost)(x_blocks[-1])
        term_hess = jax.hessian(terminal_cost)(x_blocks[-1])
        qN_minus = term_grad - term_hess @ x_blocks[-1]

        D = jnp.zeros((N + 1, n, n), dtype=states.dtype)
        E = jnp.zeros((N, n, n), dtype=states.dtype)
        q = jnp.zeros((N + 1, n), dtype=states.dtype)

        D = D.at[0].set(H_minus[0])
        if N > 1:
            D = D.at[1:N].set(H_plus[:-1] + H_minus[1:])
        D = D.at[N].set(H_plus[-1] + term_hess)
        E = H_pm

        q = q.at[0].set(q_minus[0])
        if N > 1:
            q = q.at[1:N].set(q_plus[:-1] + q_minus[1:])
        q = q.at[N].set(q_plus[-1] + qN_minus)

        return D, E, q

    def get_dynamics_linearized_matrices(
        self, states: jnp.array, controls: jnp.array, params: Dict[str, Any]
    ) -> Tuple[jnp.ndarray]:
        """
        Returns terms for the initial state and dynamics equality constraints
        states[0] = Cs[0]
        As_next[t]@states[t+1] + As[t]@states[t] + Bs_next[t]@controls[t+1]
            + Bs[t]@controls[t] = Fs[t]
        where Cs = [Cs[0], Fs] and t = 0, ..., N-1
        corresponding to the linearization of dynamics constraints
            f_t(x_{t+1}, x_t, u_{t+1}, u_t) = 0
        around a (states, controls) trajectory.

        Dimensions: (N, nx, nu) = (horizon, num_states, num_controls)

        Args:
            states: state trajectory,
                (N + 1, nx) array
            controls: control trajectory,
                (N + 1, nu) array
            params: dictionary of parameters of the optimal control problem,
                (key=string, value=Any)

        Returns:
            (in scaled units if rescaling is enabled)

            As_next: dynamics matrices multiplying next states
                (N, nx, nx) array
            As: dynamics matrices multiplying states
                (N, nx, nx) array
            Bs_next: dynamics matrices multiplying next controls
                (N, nx, nu) array
            Bs: dynamics matrices multiplying controls
                (N, nx, nu) array
            Cs: initial state and dynamics vectors, Cs = (x0, Fs)
                (N+1, nx) array (initial state, dynamics) constraints

        """
        # Time-varying dynamics parameters should be shaped (horizon, ...)
        # for explicit schemes and (horizon+1, ...) for implicit schemes.
        def linearize_explicit_integrator(
            states: jnp.ndarray, controls: jnp.ndarray
        ) -> Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray, jnp.ndarray]:
            # x+ = f(x,u) ~= f(y,v) + ∇f(y,v) (x-y, u-v)
            # => -I x+ + ∇f(y,v)(x, u) = -(f(y,v) - ∇f(y,v) (y, v))
            dynamics_params = self._get_dynamics_params_sequence(params, self.horizon)

            def next_state(state_control, step_params):
                state = state_control[: self.num_state_variables]
                control = state_control[self.num_state_variables :]
                return predict_next_state(
                    self.dynamics,
                    params["discretization_resolution"],
                    self.discretization_scheme,
                    step_params,
                    state,
                    control,
                    control,
                )

            def next_state_and_gradient_dstate_dcontrol(state, control, step_params):
                state_control = jnp.concatenate([state, control])
                next_state_fn = lambda sc: next_state(sc, step_params)
                next_state_val = next_state_fn(state_control)
                next_state_grad = jax.jacfwd(next_state_fn)(state_control)
                return next_state_val, next_state_grad

            next_states, next_states_dstate_dcontrol = vmap(
                next_state_and_gradient_dstate_dcontrol
            )(
                states[: self.horizon],
                controls[: self.horizon],
                dynamics_params,
            )
            As = next_states_dstate_dcontrol[:, :, : self.num_state_variables]
            Bs = next_states_dstate_dcontrol[:, :, self.num_state_variables :]
            Cs = jnp.concatenate(
                [
                    params["initial_state"][jnp.newaxis],
                    -next_states
                    + vmap(lambda A, x: A @ x)(As, states[: self.horizon])
                    + vmap(lambda A, x: A @ x)(Bs, controls[: self.horizon]),
                ],
                axis=0,
            )
            As_next = jnp.repeat(
                -jnp.eye(self.num_state_variables)[jnp.newaxis],
                repeats=self.horizon,
                axis=0,
            )
            return As_next, As, Bs, Cs

        def linearize_implicit_integrator(
            states: jnp.ndarray, controls: jnp.ndarray
        ) -> Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray, jnp.ndarray, jnp.ndarray]:
            nx = self.num_state_variables
            dt = params["discretization_resolution"]
            dynamics_params = self._get_dynamics_params_sequence(params, self.horizon + 1)

            def state_base_dot(state, control, step_params):
                return 0.5 * dt * self.dynamics.state_dot(state, control, step_params)

            def state_base_dot_and_gradient(state, control, step_params):
                state_control = jnp.concatenate([state, control])
                return value_and_jacfwd(
                    lambda sc: state_base_dot(sc[:nx], sc[nx:], step_params),
                    state_control,
                )
            # Debug state and control shapes
            # print(f"states shape: {states.shape}, controls shape: {controls.shape}")
            states_base_dots, gradients = vmap(state_base_dot_and_gradient, in_axes=(0, 0, 0))(
                states, controls, dynamics_params
            )
            dxddx = gradients[:, :, :nx]
            dxddu = gradients[:, :, nx:]
            I = jnp.eye(nx)
            As = I + dxddx[:-1]
            As_next = -I + dxddx[1:]
            Bs = dxddu[:-1]
            Bs_next = dxddu[1:]

            Fs = (
                vmap(lambda A, x: A @ x)(As, states[:-1])
                + vmap(lambda A, x: A @ x)(As_next, states[1:])
                + vmap(lambda B, u: B @ u)(Bs, controls[:-1])
                + vmap(lambda B, u: B @ u)(Bs_next, controls[1:])
                - states[:-1]
                - states_base_dots[:-1]
                - states_base_dots[1:]
                + states[1:]
            )
            Cs = jnp.concatenate([params["initial_state"][jnp.newaxis], Fs], axis=0)
            return As_next, Bs_next, As, Bs, Cs

        if self.discretization_scheme == DiscretizationScheme.IMPLICIT:
            As_next, Bs_next, As, Bs, Cs = linearize_implicit_integrator(
                states, controls
            )
        else:
            As_next, As, Bs, Cs = linearize_explicit_integrator(states, controls)
            Bs_next = jnp.zeros_like(Bs)
        if self._rescale_optimization_variables:
            _, _, _, _, state_diff, _ = self._get_rescaling_params(params)
            row_scale = 1.0 / state_diff
            As_next = As_next * row_scale[jnp.newaxis, :, jnp.newaxis]
            Bs_next = Bs_next * row_scale[jnp.newaxis, :, jnp.newaxis]
            As = As * row_scale[jnp.newaxis, :, jnp.newaxis]
            Bs = Bs * row_scale[jnp.newaxis, :, jnp.newaxis]
            Cs = Cs * row_scale[jnp.newaxis, :]
        return As_next, Bs_next, As, Bs, Cs

class OptimalControlProblemObstacle(OptimalControlProblem):
    """Optimal control problem with obstacles class."""

    def inequality_constraints(
        self, 
        states: jnp.array, 
        controls: jnp.array,
        params: Dict[str, Any]
    ) -> Tuple[jnp.array, jnp.array, jnp.array]:
        """Returns inequality constraints.

        Returns g(x), g_l, g_u corresponding to the
        inequality constraints g_l <= g(x) <= g_u.

        Args:
            states: state variables,
                (_horizon + 1, _num_state_variables) array
            controls: control variables,
                (_horizon + 1, _num_control_variables) array
            params: dictionary of parameters of the optimal control problem,
                (key=string, value=Any)

        Returns:
            g_value: value of g(x),
                (_num_inequality_constraints, ) array
            g_l: value of g_l,
                (_num_inequality_constraints, ) array
            g_u: value of g_u,
                (_num_inequality_constraints, ) array
        """
        # per-timestep inequality constraints
        g, g_l, g_u = super().inequality_constraints(states, controls, params)

        positions = states[:, : self.params["obstacles_dimension"]]
        def obstacle_constraint(position, obs_center, obs_radius):
            # inequality constraint is:
            # (position - obs_center)**2 >= obs_radius**2
            # <=> 1 - (position - obs_center)**2 / obs_radius**2 <= 0
            constraint = 1.0 - jnp.linalg.norm(position - obs_center) / (obs_radius + 0.001)
            return constraint
        obs_constraints = vmap(
            vmap(obstacle_constraint, in_axes=(None, 0, 0)),  # over obstacles
            in_axes=(0, None, None),  # over time
        )(positions, params["obstacles_centers"], params["obstacles_radii"])
        
        # obs_constraints has shape (horizon+1, num_obstacles)
        g_obs = obs_constraints
        g_obs_l = -1e9 * jnp.ones_like(g_obs)
        g_obs_u = jnp.zeros_like(g_obs)
        if self._rescale_optimization_variables:
            _, _, _, _, state_diff, _ = self._get_rescaling_params(params)
            row_scale = 1.0 / jnp.mean(state_diff[: self.params["obstacles_dimension"]])
            g_obs = g_obs * row_scale
            g_obs_l = g_obs_l * row_scale
            g_obs_u = g_obs_u * row_scale

        # all inequality constraints - concatenate along constraint dimension (axis 1)
        g = jnp.concatenate([g, g_obs], axis=1)
        g_l = jnp.concatenate([g_l, g_obs_l], axis=1)
        g_u = jnp.concatenate([g_u, g_obs_u], axis=1)
        return (g, g_l, g_u)

    def get_inequalities_linearized_matrices(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        params: Dict[str, Any],
    ) -> Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]:
        """
        Linearize nonlinear inequality constraints including obstacles.

        Returns:
            A_ineq_blocks: (N+1, m, nx+nu) local blocks per timestep.
                If no constraints are active, returns shape (0, 0, nx+nu).
            l_ineq: (N+1, m)
            u_ineq: (N+1, m)
        """
        # Get linearized box constraint matrices from parent
        A_box, l_box, u_box = super().get_inequalities_linearized_matrices(
            states, controls, params
        )
        
        # Linearize obstacle constraints
        positions = states[:, : self.params["obstacles_dimension"]]
        if self._rescale_optimization_variables:
            _, _, _, _, state_diff, _ = self._get_rescaling_params(params)
            obs_scale = 1.0 / jnp.mean(state_diff[: self.params["obstacles_dimension"]])
        else:
            obs_scale = None
        
        def obstacle_constraint(position, obs_center, obs_radius):
            constraint = 1.0 - jnp.linalg.norm(position - obs_center) / (obs_radius + 0.001)
            if self._rescale_optimization_variables:
                constraint = constraint * obs_scale
            return constraint
        
        def linearize_obstacle_step(position, obs_centers, obs_radii):
            """Linearize obstacle constraints at a single timestep."""
            # Compute constraint values
            g_obs = vmap(lambda oc, or_: obstacle_constraint(position, oc, or_))(
                obs_centers, obs_radii
            )
            
            # Compute jacobian w.r.t. position (gradient)
            def g_obs_fn(pos):
                return vmap(lambda oc, or_: obstacle_constraint(pos, oc, or_))(
                    obs_centers, obs_radii
                )
            jac_pos = jax.jacfwd(g_obs_fn)(position)  # (num_obstacles, obstacles_dimension)
            
            # Create full jacobian for state-control: only position part is nonzero
            jac_full = jnp.zeros((jac_pos.shape[0], self.num_state_variables + self.num_control_variables))
            jac_full = jac_full.at[:, :self.params["obstacles_dimension"]].set(jac_pos)
            
            # Compute offset: g_val - J @ [state; control]
            offset = g_obs - jnp.dot(jac_pos, position)
            
            l_lin = -1e9 * jnp.ones_like(g_obs) - offset
            u_lin = jnp.zeros_like(g_obs) - offset
            
            return jac_full, l_lin, u_lin
        
        # Vectorize over timesteps
        A_obs, l_obs, u_obs = vmap(linearize_obstacle_step, in_axes=(0, None, None))(
            positions,
            params["obstacles_centers"],
            params["obstacles_radii"],
        )
        
        # Concatenate with box constraints
        if A_box.shape[0] > 0:
            A_all = jnp.concatenate([A_box, A_obs], axis=1)
            l_all = jnp.concatenate([l_box, l_obs], axis=1)
            u_all = jnp.concatenate([u_box, u_obs], axis=1)
        else:
            A_all = A_obs
            l_all = l_obs
            u_all = u_obs
        
        return A_all, l_all, u_all


class SlackProblemAdapter:
    """Adapter that augments a problem to support slack variables.

    Expects params to include:
      - use_slack_variables: True
      - slack_penalization_weight: scalar penalty (gamma)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        params = self.params
        if "use_slack_variables" not in params:
            raise KeyError("use_slack_variables should be in params.")
        if "slack_penalization_weight" not in params:
            raise KeyError("slack_penalization_weight should be in slack_penalization_weight.")
        self._use_slack_variables = bool(params["use_slack_variables"])
        if not self._use_slack_variables:
            raise ValueError("SlackProblemAdapter requires use_slack_variables=True.")

    def cost_with_slack(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        slack: jnp.ndarray,
        params: Dict[str, Any],
    ) -> jnp.ndarray:
        """Return cost with 0.5 * gamma * ||slack||^2 added."""
        base_cost = self.cost(states, controls, params)
        return base_cost + 0.5 * params["slack_penalization_weight"] * jnp.sum(slack**2)

    def inequality_constraints_with_slack(
        self,
        states: jnp.ndarray,
        controls: jnp.ndarray,
        slack: jnp.ndarray,
        params: Dict[str, Any],
    ) -> Tuple[jnp.ndarray, jnp.ndarray, jnp.ndarray]:
        """Return inequality constraints evaluated at g(x,u)+slack."""
        g, l, u = self.inequality_constraints(states, controls, params)
        return g + slack, l, u

    def optimal_slack(
        self,
        g: jnp.ndarray,
        l: jnp.ndarray,
        u: jnp.ndarray,
    ) -> jnp.ndarray:
        """Return slack variables projecting g into [l,u]: proj(g) - g."""
        proj = jnp.minimum(jnp.maximum(g, l), u)
        return proj - g


def make_slack_problem(base_cls):
    class SlackProblem(SlackProblemAdapter, base_cls):
        pass
    SlackProblem.__name__ = f"{base_cls.__name__}Slack"
    return SlackProblem


OptimalControlProblemSlack = make_slack_problem(OptimalControlProblem)
OptimalControlProblemObstacleSlack = make_slack_problem(OptimalControlProblemObstacle)
# Usage: Instantiate as usual, e.g., 
# problem = OptimalControlProblemSlack(dynamics=dynamics, params=problem_params)
