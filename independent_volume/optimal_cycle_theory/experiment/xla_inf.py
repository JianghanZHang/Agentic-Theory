"""XLA-∞: Palindrome compile primitives for branch elimination.

Three constructive primitives + one verification primitive.
Together they guarantee: all intermediate values finite, no branches,
the computation is a fixed DAG independent of input.

Reference: Zhang, "XLA-∞: Palindrome Compile — Branch Elimination
and the Removal of Infinity from Differentiable Programs", 2026.

Transmutation stack:
    Layer 0 (Physics):  barrier smoothing removes physics discontinuities
    Layer 1 (Code):     palindrome compile removes code branches
    Layer 2 (Hardware): compiler removes conditional jumps
    Result:             fixed DAG, no branches, all values finite
"""

import numpy as np


# ═══════════════════════════════════════════════════════════════════
# Primitive 1: smooth_where  (replaces if/else)
# ═══════════════════════════════════════════════════════════════════

def smooth_where(condition, x_true, x_false, eps):
    """Smooth branch blend: sigmoid interpolation between two values.

    Replaces:  x_true if condition > 0 else x_false
    With:      μ · x_true + (1 − μ) · x_false,  μ = σ(condition / ε)

    As ε → 0, recovers the hard branch.
    Both branches are always evaluated (no control flow).

    Args:
        condition: scalar or array, the branch discriminant
        x_true: value when condition >> 0
        x_false: value when condition << 0
        eps: transition width (the ε parameter)

    Returns:
        Smooth blend of x_true and x_false.
    """
    mu = _sigmoid(np.asarray(condition, dtype=np.float64) / max(eps, 1e-30))
    return mu * x_true + (1.0 - mu) * x_false


# ═══════════════════════════════════════════════════════════════════
# Primitive 2: grad_rescale  (forward = identity, backward = soft clip)
# ═══════════════════════════════════════════════════════════════════

def grad_rescale(x, max_grad):
    """Forward pass: identity.  Backward pass: soft gradient clip.

    The backward map is:  g ↦ g / (1 + |g| / M)

    Properties: monotone, sign-preserving, |output| < M for all g.
    In a pure-numpy (forward-only) context, this is the identity.
    The function is provided so that the palindrome-compiled forward
    simulator has the same API as the JAX/autodiff version.

    Args:
        x: input value (passed through unchanged)
        max_grad: gradient bound M

    Returns:
        x (unchanged — the rescaling acts only on gradients)
    """
    return x


def grad_rescale_bwd(g, max_grad):
    """Explicit backward pass for grad_rescale.

    Use when manually implementing the backward pass (e.g. in a
    custom Riccati adjoint).  g ↦ g / (1 + |g| / M).

    Args:
        g: incoming gradient
        max_grad: bound M

    Returns:
        Soft-clipped gradient, |output| < M.
    """
    return g / (1.0 + np.abs(g) / max_grad)


# ═══════════════════════════════════════════════════════════════════
# Primitive 3: safe_ops  (remove singularities from forward pass)
# ═══════════════════════════════════════════════════════════════════

def safe_sqrt(x, eps=1e-12):
    """√(max(x, ε)) — prevents grad = ∞ at x = 0."""
    return np.sqrt(np.maximum(x, eps))


def safe_div(a, b, eps=1e-12):
    """a / (sign(b) · max(|b|, ε)) — prevents NaN on division by zero."""
    b_safe = np.copysign(np.maximum(np.abs(b), eps), b)
    return a / b_safe


def safe_log(x, eps=1e-12):
    """log(max(x, ε)) — prevents -∞ at x = 0."""
    return np.log(np.maximum(x, eps))


def safe_norm(v, eps=1e-12):
    """‖v‖ with floor ε — prevents grad = ∞ at v = 0."""
    return safe_sqrt(np.sum(v * v), eps)


# ═══════════════════════════════════════════════════════════════════
# Verification: devil_check  (confirms no infinity escaped)
# ═══════════════════════════════════════════════════════════════════

def devil_check(*arrays):
    """Check that all values are finite (no NaN, no ±∞).

    The NASA principle: check extremes to verify interior.
    Cost: one min + one max reduction per array (2 passes, not element-wise).

    Returns True if all clean, False if any devil escaped.
    """
    for x in arrays:
        x = np.asarray(x)
        if x.size == 0:
            continue
        lo, hi = x.min(), x.max()
        if not (np.isfinite(lo) and np.isfinite(hi)):
            return False
    return True


# ═══════════════════════════════════════════════════════════════════
# Composite: log_barrier  (Layer 0 physics smoothing)
# ═══════════════════════════════════════════════════════════════════

def log_barrier(gap, kappa, eps):
    """Barrier force: κ / max(gap, ε).

    Replaces the physics discontinuity (contact on/off) with a
    smooth penalty that diverges as gap → 0⁺.

    Args:
        gap: signed distance (positive = no contact)
        kappa: barrier strength
        eps: floor (prevents division by zero)

    Returns:
        Barrier force, finite for all inputs.
    """
    return kappa / np.maximum(gap, eps)


def anneal(val_uv, val_ir, t, T):
    """Linear annealing: UV → IR over time [0, T].

    The RG flow schedule.  At t=0: val_uv (smooth, easy).
    At t≥T: val_ir (sharp, physical).

    Args:
        val_uv: UV (initial) value
        val_ir: IR (final) value
        t: current time
        T: total annealing time

    Returns:
        Interpolated value.
    """
    alpha = min(t / max(T, 1e-30), 1.0)
    return val_uv + (val_ir - val_uv) * alpha


# ═══════════════════════════════════════════════════════════════════
# Internal
# ═══════════════════════════════════════════════════════════════════

def _sigmoid(x):
    """Numerically stable sigmoid: 1 / (1 + exp(-x)).

    Underflow (exp(-large) → 0) is mathematically correct and expected
    when |x| is large.  We locally permit it; the result is always in [0, 1].
    """
    x = np.asarray(x, dtype=np.float64)
    # Clamp to [-500, 500] to avoid even triggering the underflow flag.
    # σ(500) = 1 - 7e-218 ≈ 1, σ(-500) ≈ 7e-218 ≈ 0.
    x = np.clip(x, -500.0, 500.0)
    pos = x >= 0
    exp_neg = np.exp(-np.abs(x))
    result = np.where(pos, 1.0 / (1.0 + exp_neg), exp_neg / (1.0 + exp_neg))
    return result
