"""Paper-level QP containers and adapters."""

from __future__ import annotations

from dataclasses import dataclass, field

import jax
import jax.numpy as jnp


@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class QPCostBlocks:
    """Block-tridiagonal cost P and linear term q in stage coordinates."""

    D: jnp.ndarray  # (N+1, n, n) diagonal blocks
    E: jnp.ndarray  # (N, n, n) lower off-diagonal blocks
    q: jnp.ndarray  # (N+1, n)

    def tree_flatten(self):
        return (self.D, self.E, self.q), None

    @classmethod
    def tree_unflatten(cls, aux_data, children):
        D, E, q = children
        return cls(D=D, E=E, q=q)


@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class QPEqualityBlocks:
    """Block-bidiagonal equality operator Cx = c in stage coordinates."""

    A0: jnp.ndarray      # (n0, n)
    A_minus: jnp.ndarray  # (N, nx, n) coefficients for x_t
    A_plus: jnp.ndarray   # (N, nx, n) coefficients for x_{t+1}
    c0: jnp.ndarray       # (n0,)
    c: jnp.ndarray       # (N, nx)

    def tree_flatten(self):
        return (self.A0, self.A_minus, self.A_plus, self.c0, self.c), None

    @classmethod
    def tree_unflatten(cls, aux_data, children):
        A0, A_minus, A_plus, c0, c = children
        return cls(A0=A0, A_minus=A_minus, A_plus=A_plus, c0=c0, c=c)

@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class QPInequalityBlocks:
    """Block-diagonal inequality operator and bounds."""

    G: jnp.ndarray  # (N+1, m, n)
    l: jnp.ndarray  # (N+1, m)
    u: jnp.ndarray  # (N+1, m)
    slack_penalization_weight: jnp.ndarray = field(default_factory=lambda: jnp.array(0.0))
    use_slack_variables: bool = False

    def tree_flatten(self):
        children = (
            self.G,
            self.l,
            self.u,
            self.slack_penalization_weight,
        )
        aux_data = (self.use_slack_variables,)
        return children, aux_data

    @classmethod
    def tree_unflatten(cls, aux_data, children):
        G, l, u, slack_penalization_weight = children
        (use_slack_variables,) = aux_data
        return cls(
            G=G,
            l=l,
            u=u,
            slack_penalization_weight=slack_penalization_weight,
            use_slack_variables=use_slack_variables,
        )


@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class QPData:
    """Structured QP data for the paper formulation."""

    cost: QPCostBlocks
    eq: QPEqualityBlocks
    ineq: QPInequalityBlocks

    def tree_flatten(self):
        return (self.cost, self.eq, self.ineq), None

    @classmethod
    def tree_unflatten(cls, aux_data, children):
        cost, eq, ineq = children
        return cls(cost=cost, eq=eq, ineq=ineq)


def _equality_blocks_from_ocp_mats(
    As: jnp.ndarray,
    Bs: jnp.ndarray,
    As_next: jnp.ndarray,
    Bs_next: jnp.ndarray,
    Cs: jnp.ndarray,
) -> QPEqualityBlocks:
    N = As.shape[0]
    nx = As.shape[1]
    nu = Bs.shape[2]

    A0 = jnp.concatenate(
        [jnp.eye(nx, dtype=As.dtype), jnp.zeros((nx, nu), dtype=As.dtype)], axis=1
    )
    A_minus = jnp.concatenate([As, Bs], axis=2)
    A_plus = jnp.concatenate([As_next, Bs_next], axis=2)

    return QPEqualityBlocks(
        A0=A0,
        A_minus=A_minus,
        A_plus=A_plus,
        c0=Cs[0],
        c=Cs[1:],
    )


def _inequality_blocks_from_ocp_mats(
    ineq_blocks: jnp.ndarray,
    ineq_l: jnp.ndarray,
    ineq_u: jnp.ndarray,
    use_slack_variables: bool = False,
    slack_penalization_weight: jnp.ndarray = jnp.array(0.0),
) -> QPInequalityBlocks:
    return QPInequalityBlocks(
        G=ineq_blocks,
        l=ineq_l,
        u=ineq_u,
        slack_penalization_weight=slack_penalization_weight,
        use_slack_variables=use_slack_variables,
    )


def qpdata_from_ocp_blocks(
    D: jnp.ndarray,
    E: jnp.ndarray,
    q: jnp.ndarray,
    As_next: jnp.ndarray,
    Bs_next: jnp.ndarray,
    As: jnp.ndarray,
    Bs: jnp.ndarray,
    Cs: jnp.ndarray,
    ineq_blocks: jnp.ndarray,
    ineq_l: jnp.ndarray,
    ineq_u: jnp.ndarray,
    use_slack_variables: bool = False,
    slack_penalization_weight: jnp.ndarray = jnp.array(0.0),
    initial_control: jnp.ndarray | None = None,
) -> QPData:
    """Build QPData from OCP linearization blocks."""
    cost = QPCostBlocks(D=D, E=E, q=q)
    eq = _equality_blocks_from_ocp_mats(
        As=As, Bs=Bs, As_next=As_next, Bs_next=Bs_next, Cs=Cs
    )
    if initial_control is not None:
        eq = _augment_eq_with_initial_control(eq, initial_control)
    ineq = _inequality_blocks_from_ocp_mats(
        ineq_blocks=ineq_blocks,
        ineq_l=ineq_l,
        ineq_u=ineq_u,
        use_slack_variables=use_slack_variables,
        slack_penalization_weight=slack_penalization_weight,
    )
    return QPData(cost=cost, eq=eq, ineq=ineq)


def scale_qp_data(
    qp_data: QPData, state_scale: jnp.ndarray, control_scale: jnp.ndarray
) -> QPData:
    """Scale QP variables by per-component factors.

    This applies the change of variables x = S x_hat (S = diag(state_scale, control_scale)).
    """
    scale = jnp.concatenate([state_scale, control_scale], axis=0)
    cost = qp_data.cost
    eq = qp_data.eq
    ineq = qp_data.ineq

    D = cost.D * scale[jnp.newaxis, :, jnp.newaxis] * scale[jnp.newaxis, jnp.newaxis, :]
    E = cost.E * scale[jnp.newaxis, :, jnp.newaxis] * scale[jnp.newaxis, jnp.newaxis, :]
    q = cost.q * scale[jnp.newaxis, :]

    A0 = eq.A0 * scale[jnp.newaxis, :]
    A_minus = eq.A_minus * scale[jnp.newaxis, jnp.newaxis, :]
    A_plus = eq.A_plus * scale[jnp.newaxis, jnp.newaxis, :]
    c0 = eq.c0
    c = eq.c

    nx = state_scale.shape[0]
    n0 = A0.shape[0]
    if n0 >= nx:
        row_scale_state = 1.0 / state_scale
        A0 = A0.at[:nx, :].set(A0[:nx, :] * row_scale_state[:, jnp.newaxis])
    if n0 > nx:
        row_scale_control = 1.0 / control_scale
        A0 = A0.at[nx:, :].set(A0[nx:, :] * row_scale_control[:, jnp.newaxis])
        c0 = c0.at[nx:].set(c0[nx:] * row_scale_control)

    G = ineq.G * scale[jnp.newaxis, jnp.newaxis, :]
    ineq_scaled = QPInequalityBlocks(
        G=G,
        l=ineq.l,
        u=ineq.u,
        slack_penalization_weight=ineq.slack_penalization_weight,
        use_slack_variables=ineq.use_slack_variables,
    )
    eq_scaled = QPEqualityBlocks(A0=A0, A_minus=A_minus, A_plus=A_plus, c0=c0, c=c)
    cost_scaled = QPCostBlocks(D=D, E=E, q=q)
    return QPData(cost=cost_scaled, eq=eq_scaled, ineq=ineq_scaled)


def _augment_eq_with_initial_control(
    eq: QPEqualityBlocks, initial_control: jnp.ndarray
) -> QPEqualityBlocks:
    """Append an initial-control equality constraint to the stage-0 block."""
    n0 = eq.A0.shape[0]
    n = eq.A0.shape[1]
    nu = initial_control.shape[0]
    if n0 + nu != n:
        raise ValueError(
            "initial_control dimension does not match control size in eq blocks."
        )
    A0 = jnp.concatenate(
        [eq.A0, jnp.concatenate([jnp.zeros((nu, n0)), jnp.eye(nu)], axis=1)],
        axis=0,
    )
    c0 = jnp.concatenate([eq.c0, initial_control], axis=0)
    return QPEqualityBlocks(
        A0=A0,
        A_minus=eq.A_minus,
        A_plus=eq.A_plus,
        c0=c0,
        c=eq.c,
    )
