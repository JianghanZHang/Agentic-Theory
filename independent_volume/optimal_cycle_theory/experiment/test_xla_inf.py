"""Comprehensive tests for XLA-∞ palindrome compile primitives.

Tests follow the structure from the XLA-∞ technical report:
  - Level 0: safe_ops (singularity removal)
  - Level 1: log_barrier, anneal (physics smoothing)
  - Level 2: grad_rescale (gradient bounding)
  - Palindrome: smooth_where (branch elimination)
  - Verification: devil_check
  - Integration: composite operations matching forward_simulate patterns

All tests run under np.seterr(all='raise') — any floating-point
exception is a hard failure, not a warning to suppress.
"""

import numpy as np
import sys

np.seterr(all='raise')

from xla_inf import (
    smooth_where, grad_rescale, grad_rescale_bwd,
    safe_sqrt, safe_div, safe_log, safe_norm,
    devil_check, log_barrier, anneal, _sigmoid,
)

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        msg = f"  FAIL: {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)


# ═══════════════════════════════════════════════════════════════════
# 1. _sigmoid internals
# ═══════════════════════════════════════════════════════════════════
print("=== _sigmoid ===")

# Basic values
check("sigmoid(0) = 0.5", abs(_sigmoid(0.0) - 0.5) < 1e-15)
check("sigmoid(large+) ≈ 1", abs(_sigmoid(100.0) - 1.0) < 1e-10)
check("sigmoid(large-) ≈ 0", abs(_sigmoid(-100.0)) < 1e-10)

# Symmetry: σ(x) + σ(-x) = 1
x = np.linspace(-50, 50, 1001)
sym_err = np.max(np.abs(_sigmoid(x) + _sigmoid(-x) - 1.0))
check("σ(x) + σ(-x) = 1", sym_err < 1e-14, f"max err = {sym_err:.2e}")

# Monotonicity
s = _sigmoid(x)
check("sigmoid monotone", np.all(np.diff(s) >= 0))

# Range [0, 1]
check("sigmoid in [0,1]", np.all(s >= 0) and np.all(s <= 1))

# Extreme inputs — no overflow
check("sigmoid(710) finite", np.isfinite(_sigmoid(710.0)))
check("sigmoid(-710) finite", np.isfinite(_sigmoid(-710.0)))

# No devils
check("sigmoid devil_check", devil_check(s))


# ═══════════════════════════════════════════════════════════════════
# 2. safe_ops (Level 0)
# ═══════════════════════════════════════════════════════════════════
print("=== safe_ops ===")

# -- safe_sqrt --
check("safe_sqrt(4) = 2", abs(safe_sqrt(4.0) - 2.0) < 1e-15)
check("safe_sqrt(0) > 0", safe_sqrt(0.0) > 0)
check("safe_sqrt(-1) > 0", safe_sqrt(-1.0) > 0)  # clamps negative
check("safe_sqrt(0, eps=1e-6) ≈ 1e-3", abs(safe_sqrt(0.0, 1e-6) - 1e-3) < 1e-10)

# Array input
arr = np.array([0.0, 1.0, 4.0, 9.0, -0.1])
check("safe_sqrt array finite", devil_check(safe_sqrt(arr)))

# -- safe_div --
check("safe_div(6, 3) = 2", abs(safe_div(6.0, 3.0) - 2.0) < 1e-15)
check("safe_div(1, 0) finite", np.isfinite(safe_div(1.0, 0.0)))
check("safe_div(0, 0) finite", np.isfinite(safe_div(0.0, 0.0)))

# Sign preservation: safe_div(1, -0.0) should be negative
check("safe_div sign(-)", safe_div(1.0, -1e-20) < 0)
check("safe_div sign(+)", safe_div(1.0, 1e-20) > 0)

# Array division by near-zero
b = np.linspace(-0.01, 0.01, 101)
check("safe_div array finite", devil_check(safe_div(np.ones_like(b), b)))

# -- safe_log --
check("safe_log(1) = 0", abs(safe_log(1.0)) < 1e-15)
check("safe_log(e) = 1", abs(safe_log(np.e) - 1.0) < 1e-15)
check("safe_log(0) finite", np.isfinite(safe_log(0.0)))
check("safe_log(-1) finite", np.isfinite(safe_log(-1.0)))

# Array with zeros
arr = np.array([0.0, 1e-20, 1.0, 100.0])
check("safe_log array finite", devil_check(safe_log(arr)))

# -- safe_norm --
check("safe_norm([3,4]) = 5", abs(safe_norm(np.array([3.0, 4.0])) - 5.0) < 1e-10)
check("safe_norm([0,0,0]) > 0", safe_norm(np.zeros(3)) > 0)
check("safe_norm(1e-20) finite", np.isfinite(safe_norm(np.array([1e-20, 0, 0]))))


# ═══════════════════════════════════════════════════════════════════
# 3. log_barrier (Level 1)
# ═══════════════════════════════════════════════════════════════════
print("=== log_barrier ===")

check("barrier(1, 1, 1e-4) = 1", abs(log_barrier(1.0, 1.0, 1e-4) - 1.0) < 1e-10)
check("barrier(0.01, 1, 1e-4) = 100", abs(log_barrier(0.01, 1.0, 1e-4) - 100.0) < 1e-10)
check("barrier(0, 1, 1e-4) finite", np.isfinite(log_barrier(0.0, 1.0, 1e-4)))
check("barrier(-1, 1, 1e-4) finite", np.isfinite(log_barrier(-1.0, 1.0, 1e-4)))

# Monotonicity: barrier decreases as gap increases
gaps = np.linspace(0.01, 1.0, 100)
forces = log_barrier(gaps, 1.0, 1e-6)
check("barrier monotone decreasing", np.all(np.diff(forces) <= 0))
check("barrier all finite", devil_check(forces))

# At gap=eps, force = kappa/eps (maximum finite value)
eps = 1e-4
check("barrier(eps) = kappa/eps",
      abs(log_barrier(eps, 2.0, eps) - 2.0 / eps) < 1e-6)


# ═══════════════════════════════════════════════════════════════════
# 4. anneal (RG flow)
# ═══════════════════════════════════════════════════════════════════
print("=== anneal ===")

check("anneal(t=0) = UV", anneal(10.0, 1.0, 0, 100) == 10.0)
check("anneal(t=T) = IR", anneal(10.0, 1.0, 100, 100) == 1.0)
check("anneal(t=T/2) = midpoint", anneal(10.0, 1.0, 50, 100) == 5.5)
check("anneal(t>T) = IR", anneal(10.0, 1.0, 200, 100) == 1.0)
check("anneal(T=0) = IR", anneal(10.0, 1.0, 1, 0) == 1.0)  # edge case

# Monotonicity (UV > IR case: decreasing)
ts = np.linspace(0, 100, 50)
vals = [anneal(10.0, 1.0, t, 100) for t in ts]
check("anneal monotone", all(a >= b for a, b in zip(vals, vals[1:])))


# ═══════════════════════════════════════════════════════════════════
# 5. grad_rescale (Level 2)
# ═══════════════════════════════════════════════════════════════════
print("=== grad_rescale ===")

# Forward = identity
check("grad_rescale forward identity", grad_rescale(42.0, 10.0) == 42.0)
check("grad_rescale forward array",
      np.array_equal(grad_rescale(np.arange(5.0), 10.0), np.arange(5.0)))

# Backward: g / (1 + |g|/M)
check("bwd(0) = 0", grad_rescale_bwd(0.0, 10.0) == 0.0)
check("bwd(10, M=10) = 5", abs(grad_rescale_bwd(10.0, 10.0) - 5.0) < 1e-10)
check("bwd(-10, M=10) = -5", abs(grad_rescale_bwd(-10.0, 10.0) - (-5.0)) < 1e-10)

# Bounded: |output| < M for all g
gs = np.linspace(-1e6, 1e6, 10001)
clipped = grad_rescale_bwd(gs, 10.0)
check("bwd bounded < M", np.all(np.abs(clipped) < 10.0))

# Monotone
check("bwd monotone", np.all(np.diff(clipped) >= 0))

# Sign-preserving
check("bwd sign+", np.all(clipped[gs > 0] > 0))
check("bwd sign-", np.all(clipped[gs < 0] < 0))

# Asymptotic: as |g| → ∞, output → M
check("bwd(1e10, M=10) ≈ 10",
      abs(grad_rescale_bwd(1e10, 10.0) - 10.0) < 0.001)


# ═══════════════════════════════════════════════════════════════════
# 6. smooth_where (Palindrome compile)
# ═══════════════════════════════════════════════════════════════════
print("=== smooth_where ===")

# Deep in each branch
check("sw(+10, a, b) ≈ a", abs(smooth_where(10.0, 1.0, 0.0, 1.0) - 1.0) < 1e-4)
check("sw(-10, a, b) ≈ b", abs(smooth_where(-10.0, 1.0, 0.0, 1.0) - 0.0) < 1e-4)

# At boundary: blend
check("sw(0, a, b) = (a+b)/2", abs(smooth_where(0.0, 1.0, 0.0, 1.0) - 0.5) < 1e-10)

# Continuity: no jumps
c = np.linspace(-5, 5, 10000)
result = smooth_where(c, 10.0, -10.0, eps=1.0)
max_jump = np.max(np.abs(np.diff(result)))
check("sw continuous", max_jump < 0.1, f"max jump = {max_jump:.6f}")

# Epsilon controls sharpness
sharp = smooth_where(c, 1.0, 0.0, eps=0.01)
smooth = smooth_where(c, 1.0, 0.0, eps=10.0)
# Sharp: transition happens in narrow band
sharp_width = np.sum((sharp > 0.01) & (sharp < 0.99))
smooth_width = np.sum((smooth > 0.01) & (smooth < 0.99))
check("eps controls sharpness", sharp_width < smooth_width,
      f"sharp_width={sharp_width}, smooth_width={smooth_width}")

# Array inputs for both branches
x_true = np.array([1.0, 2.0, 3.0])
x_false = np.array([10.0, 20.0, 30.0])
cond = np.array([5.0, 0.0, -5.0])
r = smooth_where(cond, x_true, x_false, eps=1.0)
check("sw array elem 0 ≈ x_true", abs(r[0] - 1.0) < 0.1)
check("sw array elem 1 = blend", abs(r[1] - 11.0) < 0.1)  # (2+20)/2 = 11
check("sw array elem 2 ≈ x_false", abs(r[2] - 30.0) < 1.0,
      f"got {r[2]:.4f}")

# Replaces clip(u, -M, M) pattern:
#   clip(u, -M, M) = sw(u+M, sw(M-u, u, M, ε), -M, ε)
# Simpler: smooth_clip
def smooth_clip(u, lo, hi, eps):
    u = smooth_where(u - lo, u, lo, eps)    # u = max(u, lo)
    u = smooth_where(hi - u, u, hi, eps)    # u = min(u, hi)
    return u

u = np.linspace(-200, 200, 1000)
clipped = smooth_clip(u, -100, 100, eps=5.0)
check("smooth_clip bounded", np.all(clipped > -102) and np.all(clipped < 102))
check("smooth_clip passthrough", np.max(np.abs(clipped[400:600] - u[400:600])) < 1.0)
check("smooth_clip finite", devil_check(clipped))

# Replaces if eff_fz < required: boost pattern
def smooth_support_floor(u_z, eff_fz, required_fz, sigma_sum, eps):
    deficit = required_fz - eff_fz
    boost = smooth_where(-deficit, 0.0, deficit / max(sigma_sum, 1e-6), eps)
    return u_z + boost

u_test = smooth_support_floor(50.0, 100.0, 150.0, 3.6, eps=5.0)
check("support floor boosts", u_test > 50.0)
u_test2 = smooth_support_floor(50.0, 200.0, 150.0, 3.6, eps=5.0)
check("support floor no-op when sufficient", abs(u_test2 - 50.0) < 1.0)

# Replaces max(gap, 1e-6) in barrier floor
gap = np.linspace(-0.1, 0.1, 1000)
smooth_gap = smooth_where(gap - 1e-6, gap, 1e-6, eps=1e-6)
check("smooth barrier floor ≥ ~0", np.all(smooth_gap > -1e-5))
check("smooth barrier floor finite", devil_check(smooth_gap))


# ═══════════════════════════════════════════════════════════════════
# 7. devil_check
# ═══════════════════════════════════════════════════════════════════
print("=== devil_check ===")

check("clean array", devil_check(np.array([1.0, 2.0, 3.0])))
check("empty array", devil_check(np.array([])))
check("scalar", devil_check(np.float64(3.14)))
check("detect +inf", not devil_check(np.array([1.0, np.inf])))
check("detect -inf", not devil_check(np.array([-np.inf, 1.0])))
check("detect NaN", not devil_check(np.array([np.nan])))
check("detect NaN among finite", not devil_check(np.array([1.0, np.nan, 3.0])))

# Multiple arrays
check("multi clean", devil_check(np.ones(3), np.zeros(5), np.array([42.0])))
check("multi one bad", not devil_check(np.ones(3), np.array([np.inf])))

# Large array
big = np.random.randn(10000)
check("large clean", devil_check(big))
big[5000] = np.nan
check("large with NaN", not devil_check(big))


# ═══════════════════════════════════════════════════════════════════
# 8. Convergence: ε → 0 recovers hard operations
# ═══════════════════════════════════════════════════════════════════
print("=== convergence (ε → 0) ===")

# smooth_where → hard branch
for eps in [1.0, 0.1, 0.01, 0.001]:
    err_pos = abs(smooth_where(1.0, 10.0, -10.0, eps) - 10.0)
    err_neg = abs(smooth_where(-1.0, 10.0, -10.0, eps) - (-10.0))
    if eps <= 0.01:
        check(f"sw convergence eps={eps}", max(err_pos, err_neg) < 1e-4,
              f"err={max(err_pos, err_neg):.2e}")

# smooth_clip → hard clip
u_val = 150.0
for eps in [10.0, 1.0, 0.1, 0.01]:
    clipped_val = smooth_clip(u_val, -100, 100, eps)
    err = abs(clipped_val - 100.0)
    if eps <= 0.1:
        check(f"smooth_clip convergence eps={eps}", err < 1.0,
              f"clipped={clipped_val:.4f}")


# ═══════════════════════════════════════════════════════════════════
# 9. Composition: chaining primitives stays finite
# ═══════════════════════════════════════════════════════════════════
print("=== composition ===")

# Chain: barrier → log → sqrt → where → check
x = np.linspace(-1, 1, 1000)
gap = np.abs(x) + 0.001
f = log_barrier(gap, kappa=1.0, eps=1e-6)
l = safe_log(f)
s = safe_sqrt(l * l)
r = smooth_where(x, s, -s, eps=0.5)
check("chain all finite", devil_check(r))

# Realistic pattern: σ_k = ε/(h_k + ε) through barrier → force_scale
h = np.maximum(0.0, np.sin(np.linspace(0, 2*np.pi, 100)) * 0.08)
eps_val = 0.1
sigma = eps_val / (h + eps_val)  # barrier force scale
slip_cost = sigma * 0.5**2  # w_slip * sigma * v^2
check("slip cost chain finite", devil_check(sigma, slip_cost))
check("sigma in [0,1]", np.all(sigma >= 0) and np.all(sigma <= 1))


# ═══════════════════════════════════════════════════════════════════
# 10. Forward simulator patterns (pre-integration test)
# ═══════════════════════════════════════════════════════════════════
print("=== forward_simulate patterns ===")

# Pattern 1: smooth force clip (replaces np.clip(u, -100, 100))
u = np.array([50.0, -150.0, 200.0, -30.0, 0.0, 99.0])
u_smooth = smooth_clip(u, -100.0, 100.0, eps=5.0)
check("force clip bounded", np.all(np.abs(u_smooth) < 105))
check("force clip interior preserved",
      np.max(np.abs(u_smooth[np.abs(u) < 80] - u[np.abs(u) < 80])) < 1.0)
check("force clip finite", devil_check(u_smooth))

# Pattern 2: smooth support floor (replaces if eff_fz < mg: boost)
sigma_t = np.array([0.9, 0.9, 0.1, 0.1])  # two stance, two swing
fz = np.array([30.0, 30.0, 5.0, 5.0])
eff_fz = np.sum(sigma_t * fz)  # 27 + 27 + 0.5 + 0.5 = 55
mg = 15.206 * 9.81  # ~149.2 N
deficit = mg - eff_fz
sigma_sum = np.sum(sigma_t)
boost = smooth_where(-deficit, 0.0, deficit / max(sigma_sum, 1e-6), eps=5.0)
check("support floor boost > 0 when deficit", boost > 0)
check("support floor boost ≈ deficit/σ_sum",
      abs(boost - deficit/sigma_sum) < 5.0,
      f"boost={boost:.2f}, expected≈{deficit/sigma_sum:.2f}")
check("support floor finite", devil_check(np.array([boost])))

# Pattern 3: smooth barrier floor (replaces max(gap, 1e-6))
pz_values = np.array([0.13, 0.135, 0.27, 0.405, 0.41])
z_min = 0.13
for pz in pz_values:
    gap = pz - z_min
    smooth_gap = smooth_where(gap - 1e-6, gap, 1e-6, eps=1e-6)
    barrier_val = safe_log(smooth_gap)
    check(f"barrier floor pz={pz:.3f} finite",
          np.isfinite(barrier_val), f"val={barrier_val:.4f}")


# ═══════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════
print()
print(f"{'='*50}")
print(f"  XLA-∞ test results: {PASS} passed, {FAIL} failed")
print(f"{'='*50}")
sys.exit(0 if FAIL == 0 else 1)
