from typing import Tuple

import jax.numpy as jnp
from jax import vmap

from diffmpc.solvers.qp_data import QPData
from diffmpc.solvers.qp_utils import ZShape, unpack_x

def assemble_backward_kkt_system(
    qp_data: QPData,
) -> Tuple[jnp.ndarray, jnp.ndarray]:
    """Assemble the KKT matrix and RHS for the backward pass.

    Constructs the full saddle-point KKT system for sensitivity computation
    in the adjoint/backward pass of differentiable MPC. The system is:

        [ P    C.T ] [ x ]     [ -q ]
        [ C    0   ] [ y ]  =  [ 0  ]

    Args:
        qp_data: QPData containing cost matrices (D, E, q), equality constraints
                 (A0, A_minus, A_plus), and inequality constraints (G).

    Returns:
        KKT: Full saddle-point KKT matrix ((n_total + m_total) x (n_total + m_total)).
        rhs: Right-hand side vector (n_total + m_total,) = [-q; 0].
    """
    D = qp_data.cost.D
    E = qp_data.cost.E
    A0 = qp_data.eq.A0
    A_minus = qp_data.eq.A_minus
    A_plus = qp_data.eq.A_plus
    G = qp_data.ineq.G

    N = D.shape[0] - 1
    n = D.shape[1]

    dtype = D.dtype

    # ===== Assemble A matrix (equality constraints) =====
    # A is a sparse block matrix:
    # [A0          0       0   ...  0    ]
    # [A_minus[0]  A_plus[0]  0   ...  0  ]
    # [0  A_minus[1]  A_plus[1]  ...  0   ]
    # ...
    # [0  ...  A_minus[N-1]  A_plus[N-1] ]
    #
    # Build A matrix row by row using Python loops (N is static)
    # A is (m0 + N*m) x n*(N+1)

    # First row: [A0  0  0  ...  0]
    A0_padded = jnp.pad(A0, ((0, 0), (0, n * N)), mode="constant", constant_values=0)

    # Dynamics rows: for each i (Python int, not traced), build row with padding
    A_rows = [A0_padded]
    for i in range(N):
        block = jnp.hstack([A_minus[i], A_plus[i]])
        left_pad_width = i * n
        right_pad_width = (N - i - 1) * n
        row = jnp.pad(
            block,
            ((0, 0), (left_pad_width, right_pad_width)),
            mode="constant",
            constant_values=0,
        )
        A_rows.append(row)

    A = jnp.vstack(A_rows)  # shape ((m0 + N*m), n*(N+1))

    # ===== Assemble G matrix (inequality constraints) =====
    # G is block diagonal:
    # [G[0]   0    ...  0   ]
    # [0    G[1]  ...  0   ]
    # ...
    # [0    ...     G[N]   ]
    #
    # Build G matrix row by row using Python loops (N is static)
    # G is ((N+1)*m) x n*(N+1)

    G_rows = []
    for i in range(N + 1):
        left_pad_width = i * n
        right_pad_width = (N - i) * n
        block = jnp.pad(
            G[i],
            ((0, 0), (left_pad_width, right_pad_width)),
            mode="constant",
            constant_values=0,
        )
        G_rows.append(block)

    G_assembled = jnp.vstack(G_rows)  # shape ((N+1)*m, n*(N+1))

    # ===== Assemble C matrix =====
    # C = [A; G] (stack A and G vertically)
    C = jnp.vstack([A, G_assembled])  # shape ((m0 + N*m + (N+1)*m), n*(N+1))

    # ===== Assemble full KKT matrix =====
    # KKT = [S    C.T]
    #       [C    0  ]

    m_total = A.shape[0] + G_assembled.shape[0]  # total constraint count
    n_total = n * (N + 1)  # total primal dimension

    # Top-left block: 
    # ===== Assemble P matrix (Hessian Matrix) =====
    # P has a block-tridiagonal structure of the form:
    # P = [D[0]  E[0].T  0     ...    0   
    #      E[0]  D[1]  E[1].T  ...    0
    #      0     E[1]  D[2]   ...    
    #      ...   ...   ...     ...    E[N-1].T
    #      0     0     ...    E[N-1]  D[N] ]
    # P has blocks: D[i] on diagonal, E[i] on super-diagonal, E[i].T on sub-diagonal
    
    P = jnp.zeros((n_total, n_total), dtype=dtype)

    # Place block-tridiagonal structure
    for i in range(N + 1):
        row_start = i * n
        row_end = (i + 1) * n
        col_start = i * n
        col_end = (i + 1) * n

        # Place D[i] on diagonal
        P = P.at[row_start:row_end, col_start:col_end].set(D[i])

        # Place E[i] on super-diagonal (below main diagonal in block-row i)
        if i < N:
            col_start_next = (i + 1) * n
            col_end_next = (i + 2) * n
            P = P.at[row_start:row_end, col_start_next:col_end_next].set(E[i].T)

        # Place E[i].T on sub-diagonal (above main diagonal in block-row i)
        if i > 0:
            col_start_prev = (i - 1) * n
            col_end_prev = i * n
            P = P.at[row_start:row_end, col_start_prev:col_end_prev].set(E[i - 1])

    # Top-right block: C.T
    CT = C.T  # shape (n_total, m_total)

    # Bottom-left block: C
    # Bottom-right block: zero matrix
    zero_block = jnp.zeros((m_total, m_total), dtype=dtype)

    # Construct full KKT matrix
    top = jnp.hstack([P, CT])  # shape (n_total, n_total + m_total)
    bottom = jnp.hstack([C, zero_block])  # shape (m_total, n_total + m_total)
    KKT = jnp.vstack([top, bottom])  # shape ((n_total + m_total), (n_total + m_total))

    # ===== Assemble full RHS =====
    # For backward pass: KKT RHS is [-q; 0] where constraints are Cx = 0 (homogeneous)
    # In the backward pass, C represents gradients w.r.t. state variables
    q_flat = qp_data.cost.q.reshape(-1)  # (N+1, n) → (n_total,)

    # For backward/adjoint analysis with homogeneous constraints Cx = 0,
    # the constraint RHS is zero (sensitivities driven by cost gradient only)
    constraint_rhs = jnp.zeros(m_total, dtype=dtype)

    # Full KKT RHS: [-q; 0] for backward pass
    rhs = jnp.concatenate([-q_flat, constraint_rhs])  # shape (n_total + m_total)

    return KKT, rhs

def solve_backward_kkt(
    qp_data: QPData,
    zshape: ZShape,
) -> Tuple[Tuple[jnp.ndarray, jnp.ndarray], jnp.ndarray]:
    """Solve the backward-pass KKT system using direct JAX linear algebra.

    Args:
        qp_data: QPData with costs and constraints for the backward QP
                 (typically constructed with active constraint set only).
        zshape: ZShape defining problem dimensions
                (horizon, num_states, num_controls).

    Returns:
        ((states_sensitivity, controls_sensitivity), constraint_multipliers):
          - states_sensitivity: (N+1, n_x) sensitivities of states w.r.t. params
          - controls_sensitivity: (N, n_u) sensitivities of controls w.r.t. params
          - constraint_multipliers: (m_total,) flat multiplier vector from KKT solve
    """
    KKT, rhs = assemble_backward_kkt_system(qp_data)

    # Solve full KKT system using JAX linear algebra (works in traced context)
    # KKT @ solution = rhs
    solution = jnp.linalg.solve(KKT, rhs)

    # Extract primal solution (first n_total entries are states/controls)
    n_total = qp_data.cost.q.shape[0] * qp_data.cost.q.shape[1]
    x_blocks_flat = solution[:n_total]

    # Reshape from flat (n_total,) to block form (N+1, n)
    N_plus_1 = qp_data.cost.q.shape[0]
    n = qp_data.cost.q.shape[1]
    x_blocks = x_blocks_flat.reshape(N_plus_1, n)

    # Unpack x_blocks → (states, controls)
    x_solution, y_solution = unpack_x(x_blocks, zshape)

    # Extract dual solution (multipliers for constraints)
    multipliers = solution[n_total:]

    return (x_solution, y_solution), multipliers
