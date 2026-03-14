"""Shared linear system utilities for block-tridiagonal Schur systems."""

from __future__ import annotations

from typing import Literal, Tuple

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def block_tridi_apply(
    schur_blocks: np.ndarray, x_blocks: np.ndarray
) -> np.ndarray:
    """Apply block-tridiagonal Schur blocks to x in block form.

    Args:
        schur_blocks: (T, n, 3n) blocks [prev, diag, next]
        x_blocks: (T, n)

    Returns:
        y_blocks: (T, n)
    """
    schur_blocks = np.asarray(schur_blocks)
    x_blocks = np.asarray(x_blocks)
    if schur_blocks.ndim != 3:
        raise ValueError(
            f"schur_blocks must be rank-3, got {schur_blocks.ndim}"
        )
    if x_blocks.ndim != 2:
        raise ValueError(f"x_blocks must be rank-2, got {x_blocks.ndim}")
    if schur_blocks.shape[0] != x_blocks.shape[0]:
        raise ValueError(
            "schur_blocks and x_blocks must have same time dimension. "
            f"Got {schur_blocks.shape[0]} vs {x_blocks.shape[0]}"
        )
    n = schur_blocks.shape[1]
    if schur_blocks.shape[2] != 3 * n:
        raise ValueError(
            f"schur_blocks last dim must be 3*n, got {schur_blocks.shape[2]}"
        )
    if x_blocks.shape[1] != n:
        raise ValueError(
            f"x_blocks has wrong block dim. Expected {n}, got {x_blocks.shape[1]}"
        )
    x_prev = np.concatenate([np.zeros((1, n)), x_blocks[:-1]], axis=0)
    x_next = np.concatenate([x_blocks[1:], np.zeros((1, n))], axis=0)
    x_stack = np.concatenate([x_prev, x_blocks, x_next], axis=-1)
    y_blocks = np.einsum("tij,tj->ti", schur_blocks, x_stack)
    return y_blocks


def block_tridi_to_csr(schur_blocks: np.ndarray) -> sp.csr_matrix:
    """Convert block-tridiagonal Schur blocks to a CSR matrix.

    Args:
        schur_blocks: (T, n, 3n) blocks [prev, diag, next]

    Returns:
        A: CSR matrix with shape (T*n, T*n)
    """
    schur_blocks = np.asarray(schur_blocks)
    if schur_blocks.ndim != 3:
        raise ValueError(
            f"schur_blocks must be rank-3, got {schur_blocks.ndim}"
        )
    T = schur_blocks.shape[0]
    n = schur_blocks.shape[1]
    if schur_blocks.shape[2] != 3 * n:
        raise ValueError(
            f"schur_blocks last dim must be 3*n, got {schur_blocks.shape[2]}"
        )

    rows = []
    cols = []
    data = []

    row_base = np.repeat(np.arange(n), n)
    col_base = np.tile(np.arange(n), n)

    for t in range(T):
        row_offset = t * n
        # prev block
        if t > 0:
            block = schur_blocks[t, :, :n]
            rows.append(row_base + row_offset)
            cols.append(col_base + (t - 1) * n)
            data.append(block.reshape(-1))
        # diag block
        block = schur_blocks[t, :, n : 2 * n]
        rows.append(row_base + row_offset)
        cols.append(col_base + t * n)
        data.append(block.reshape(-1))
        # next block
        if t < T - 1:
            block = schur_blocks[t, :, 2 * n :]
            rows.append(row_base + row_offset)
            cols.append(col_base + (t + 1) * n)
            data.append(block.reshape(-1))

    rows = np.concatenate(rows)
    cols = np.concatenate(cols)
    data = np.concatenate(data)
    A = sp.coo_matrix((data, (rows, cols)), shape=(T * n, T * n))
    return A.tocsr()


def solve_block_tridi_system(
    schur_blocks: np.ndarray,
    rhs_blocks: np.ndarray,
    backend: Literal["scipy"] = "scipy",
) -> np.ndarray:
    """Solve block-tridiagonal system S x = b.

    Args:
        schur_blocks: (T, n, 3n)
        rhs_blocks: (T, n) or flat (T*n,)
        backend: "scipy" (only scipy supported in cherry-picked version)

    Returns:
        x_blocks: (T, n)
    """
    schur_blocks = np.asarray(schur_blocks)
    rhs = np.asarray(rhs_blocks)
    T = schur_blocks.shape[0]
    n = schur_blocks.shape[1]
    if rhs.ndim == 1:
        if rhs.size != T * n:
            raise ValueError(
                f"rhs has wrong size. Expected {T * n}, got {rhs.size}"
            )
        rhs_flat = rhs
    elif rhs.ndim == 2:
        if rhs.shape != (T, n):
            raise ValueError(
                f"rhs has wrong shape. Expected {(T, n)}, got {rhs.shape}"
            )
        rhs_flat = rhs.reshape(-1)
    else:
        raise ValueError(f"rhs must be rank-1 or rank-2, got ndim={rhs.ndim}")

    A = block_tridi_to_csr(schur_blocks)
    x_flat = spla.spsolve(A, rhs_flat)
    return x_flat.reshape((T, n))
