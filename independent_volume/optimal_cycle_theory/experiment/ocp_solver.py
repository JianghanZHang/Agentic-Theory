"""Differentiable OCP solver wrapper.

Forward:  solve(x0, weights) -> Solution(controls, states)
Backward: jax.grad flows through `weights` via implicit differentiation (KKT adjoint)

The `weights` dict is the ONLY differentiable input. Put cost weights and
reference trajectories there. Everything else (x0, dynamics params, bounds,
horizon) goes in problem_params and is NOT differentiated.

Differentiable keys (via weights):
    weights_penalization_reference_state_trajectory   Q diagonal  (nx,)
    weights_penalization_control_squared              R diagonal  (nu,)
    weights_penalization_final_state                  Q_f diagonal (nx,)
    weights_penalization_control_rate                 R_d diagonal (nu,)
    reference_state_trajectory                        x_ref (H+1, nx)
    reference_control_trajectory                      u_ref (H+1, nu)
    slack_penalization_weight                          scalar
"""

import copy
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional

import jax
import jax.numpy as jnp

from diffmpc.dynamics.base_dynamics import Dynamics
from diffmpc.problems.optimal_control_problem import OptimalControlProblem
from diffmpc.solvers.sqp_admm import SQPADMMSolver
from diffmpc.utils.load_params import load_params, load_problem_params, load_solver_params


class Solution(NamedTuple):
    """Solver output (vmappable)."""
    controls: jnp.ndarray       # (H+1, nu)
    states: jnp.ndarray         # (H+1, nx)
    convergence_error: float


DIFFERENTIABLE_KEYS = [
    "weights_penalization_reference_state_trajectory",
    "weights_penalization_control_squared",
    "weights_penalization_final_state",
    "weights_penalization_control_rate",
    "reference_state_trajectory",
    "reference_control_trajectory",
    "slack_penalization_weight",
]


def _broadcast_dynamics_params(params: dict, horizon: int) -> dict:
    """Broadcast 1-D dynamics params to (H+1, ...) if needed."""
    params = copy.deepcopy(params)
    dyn = params.get("dynamics_state_dot_params")
    if dyn is None:
        return params
    for k, v in dyn.items():
        v = jnp.asarray(v)
        if v.ndim == 1:
            dyn[k] = jnp.repeat(v[None, :], repeats=horizon + 1, axis=0)
    return params


class OCPSolver:
    """Differentiable OCP solver for MPC training.

    Args:
        dynamics: a Dynamics subclass instance (e.g. SpacecraftDynamics())
        problem_params: full OCP parameter dict (from YAML or manual).
            Must contain: horizon, discretization_resolution, initial_state,
            final_state, bounds, cost weights, dynamics_state_dot_params.
        solver_params: SQP-ADMM config dict. If None, uses default sqp_admm.yaml.
        backend: linear solver backend.
            "pcg"      — pure JAX (works everywhere, supports backward)
            "pcg_ffi"  — CUDA FFI, fast (requires built FFI libs, supports backward)
            "cudss_ffi"— cuDSS FFI (requires built FFI libs, supports backward)
    """

    def __init__(
        self,
        dynamics: Dynamics,
        problem_params: Dict[str, Any],
        solver_params: Optional[Dict[str, Any]] = None,
        backend: str = "pcg",
    ):
        horizon = problem_params["horizon"]
        self._problem_params = _broadcast_dynamics_params(problem_params, horizon)
        self._dynamics = dynamics

        if solver_params is None:
            solver_params = load_solver_params("sqp_admm.yaml")
            # Override defaults that prevent ADMM convergence:
            # sqp_admm.yaml has eps_abs/rel=1e-9 with max_iter=100,
            # which is too tight to converge. Use proven defaults
            # from compare_models.py that converge reliably.
            solver_params["num_scp_iteration_max"] = 5
            solver_params["linesearch"] = True
            solver_params["admm"]["eps_abs"] = 1e-4
            solver_params["admm"]["eps_rel"] = 1e-3
            solver_params["admm"]["pcg"]["tol_epsilon"] = 1e-12

        ocp = OptimalControlProblem(dynamics=dynamics, params=self._problem_params)
        self._solver = SQPADMMSolver(
            ocp,
            params=solver_params,
            forward_backend=backend,
            backward_backend=backend,
        )

    @classmethod
    def from_yaml(
        cls,
        dynamics: Dynamics,
        problem_yaml: str,
        solver_yaml: Optional[str] = None,
        horizon: Optional[int] = None,
        backend: str = "pcg",
    ) -> "OCPSolver":
        """Construct from YAML config files.

        Args:
            dynamics: Dynamics subclass instance
            problem_yaml: path to problem YAML (absolute, or name in diffmpc/problems/params/)
            solver_yaml: path to solver YAML (absolute, or name in diffmpc/solvers/params/).
                         Defaults to sqp_admm.yaml.
            horizon: override horizon from YAML
            backend: linear solver backend
        """
        p = Path(problem_yaml)
        if p.is_absolute() or p.exists():
            problem_params = load_params(str(p))
            # Replicate the jaxification that load_problem_params does
            entries_to_not_jaxify = [
                "horizon", "discretization_scheme", "penalize_control_reference",
                "rescale_optimization_variables", "constrain_initial_control",
                "dynamics_state_dot_params",
            ]
            for key in problem_params:
                if key not in entries_to_not_jaxify:
                    problem_params[key] = jnp.array(problem_params[key])
            dyn_params = problem_params.get("dynamics_state_dot_params")
            if dyn_params is not None:
                problem_params["dynamics_state_dot_params"] = {
                    k: jnp.array(v) for k, v in dyn_params.items()
                }
            h = horizon if horizon is not None else problem_params["horizon"]
            problem_params["reference_state_trajectory"] = jnp.repeat(
                problem_params["reference_state_trajectory"][None],
                repeats=h + 1, axis=0,
            )
            problem_params["reference_control_trajectory"] = jnp.repeat(
                problem_params["reference_control_trajectory"][None],
                repeats=h + 1, axis=0,
            )
        else:
            problem_params = load_problem_params(str(p))

        if horizon is not None and horizon != problem_params["horizon"]:
            problem_params["horizon"] = horizon
            # Re-broadcast reference trajectories to new horizon
            nx = dynamics.num_states
            nu = dynamics.num_controls
            ref_x = problem_params["reference_state_trajectory"]
            ref_u = problem_params["reference_control_trajectory"]
            # Take one row (they're all identical) and re-broadcast
            problem_params["reference_state_trajectory"] = jnp.repeat(
                ref_x[0:1], repeats=horizon + 1, axis=0,
            )
            problem_params["reference_control_trajectory"] = jnp.repeat(
                ref_u[0:1], repeats=horizon + 1, axis=0,
            )

        solver_params = None
        if solver_yaml is not None:
            sp = Path(solver_yaml)
            if sp.is_absolute() or sp.exists():
                solver_params = load_params(str(sp))
            else:
                solver_params = load_solver_params(str(sp))

        return cls(dynamics, problem_params, solver_params=solver_params, backend=backend)

    def solve(self, x0: jnp.ndarray, weights: Optional[Dict[str, Any]] = None) -> Solution:
        """Solve OCP for a single initial condition.

        Args:
            x0: (nx,) initial state — NOT differentiated
            weights: dict of differentiable cost parameters.
                     jax.grad(loss)(weights) gives you dL/d(weights).
                     See DIFFERENTIABLE_KEYS for valid entries.

        Returns:
            Solution(controls=(H+1, nu), states=(H+1, nx), convergence_error=scalar)
        """
        params = {**self._problem_params, "initial_state": x0}
        guess = self._solver.initial_guess(params)
        raw = self._solver.solve(guess, problem_params=params, weights=weights or {})
        return Solution(
            controls=raw.controls,
            states=raw.states,
            convergence_error=raw.convergence_error,
        )

    def solve_batch(self, x0s: jnp.ndarray, weights: Optional[Dict[str, Any]] = None) -> Solution:
        """Batched solve via jax.vmap. JIT-compiled on first call.

        Args:
            x0s: (batch, nx) initial states
            weights: shared across batch (same cost weights for all problems)

        Returns:
            Solution with batch dimension prepended:
                controls (batch, H+1, nu), states (batch, H+1, nx)
        """
        return jax.jit(jax.vmap(lambda x0: self.solve(x0, weights)))(x0s)

    def warmup(self, batch_size: int = 1):
        """Trigger JIT compilation with zero inputs.

        Call this once before timing to exclude compilation overhead.
        """
        nx = self._dynamics.num_states
        dummy = jnp.zeros((batch_size, nx))
        sol = self.solve_batch(dummy)
        jax.block_until_ready(sol.controls)

    @property
    def problem_params(self) -> Dict[str, Any]:
        """Current problem parameters (read-only view)."""
        return self._problem_params

    @property
    def horizon(self) -> int:
        return self._problem_params["horizon"]

    @property
    def nx(self) -> int:
        return self._dynamics.num_states

    @property
    def nu(self) -> int:
        return self._dynamics.num_controls

    @staticmethod
    def differentiable_keys() -> list:
        """Parameter keys that can be passed in weights for gradient computation."""
        return list(DIFFERENTIABLE_KEYS)
