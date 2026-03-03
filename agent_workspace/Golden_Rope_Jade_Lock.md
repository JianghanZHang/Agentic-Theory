# Golden Rope, Jade Lock 2.0 — 顿开金绳，扯断玉锁

## What changed from 1.0

1.0 used discrete contact modes (MODE_SEPARATING / SLIDING / STICKING).
2.0 replaces all mode logic with a single continuous **order parameter**:

    ρ = F_repulsion / F_attraction

Everything—edge weights, control law, MPPI sampling—is now a smooth
function of ρ. No enums, no mode switches, no if/else chains.

## The ρ formulation

| Regime | ρ | Mode | Arc type |
|--------|---|------|----------|
| Attraction wins | ρ < 1 | Separating | Singular (free flight) |
| Phase transition | ρ = 1 | Sliding | Switching surface Σ |
| Repulsion wins | ρ > 1 | Sticking | Bang (spectral kick) |
| Existence | ρ → ∞ | Clamped | Attached body |

### Smooth edge weight

    w(ρ) = w_slide · σ(β(ρ−1)) + (w_stick − w_slide) · σ(β(ρ−1.1))

where:
- w_slide = k_n(1 + μ)
- w_stick = k_n + k_t
- σ(x) = 1 / (1 + exp(−x))  (logistic sigmoid)
- β ≈ 20  (sharpness)

C∞ by construction. Closed-form derivative:

    dw/dρ = β · w_slide · σ'(β(ρ−1)) + β · (w_stick − w_slide) · σ'(β(ρ−1.1))

where σ'(x) = σ(x)(1 − σ(x)).

## Module Specifications

### `order_parameter.py` — The heart of 2.0

- `compute_rho(F_repulsion, F_attraction)` → scalar ρ ≥ 0
- `smooth_edge_weight(rho, k_n, k_t, mu, beta)` → w(ρ)
- `d_smooth_edge_weight_d_rho(rho, ...)` → analytical dw/dρ
- `verify_smooth_weight()` → analytical vs finite-diff, rel error < 1e-6
- `build_laplacian_from_rho(rho_pairs, n_bodies)` → graph Laplacian

### `rho_sampler.py` — MPPI with continuous ρ

- `RhoMPPISampler`: sample/reweight/fuse/solve (same pattern as 1.0)
- ρ is **derived** from state+control, not sampled directly
- Phase-transition penalty: cost += γ · exp(−(ρ−1)²/δ²)
- Returns `rho_history` alongside costs

### `pmp_rho_solver.py` — PMP with ρ-weighted Laplacian

- State x = (q, qdot) ∈ R^24 (unchanged)
- Hamiltonian H uses `smooth_edge_weight(ρ)` for λ₁ computation
- Costate chain rule: dH/dx flows through dw/dρ · dρ/dx
- Optimal control u*(t) = sat(−p_qdot_star / (αm_*))

### `threebody_rho.py` — Main simulator

- CLI: `--solver reactive|pmp`, `--headless`
- Reactive: control based on ρ_min < 1
- PMP: `PmpRhoSolver` + `RhoMPPISampler`
- Logs: ρ time series, edge weights, λ₁, control effort
- Plots: ρ vs time, w(ρ) evolution, phase portrait (ρ vs λ₁)

### `compare_v1_v2.py` — Head-to-head

Imports both `grjl.threebody_damper` and `grjl2.threebody_rho`.
4-panel comparison: λ₁, control norm, ρ, edge weights.

### `dribble.xml` — MuJoCo ball-dribble scene

Ball with non-uniform inertia (3 distinct principal axes = "three bodies"),
ground plane, paddle (3 slide joints). ρ = F_paddle / (m·g).

### `dribble_controller.py` — Thin MuJoCo controller

Three-term control mapped to dribbling:
- (I)  Gravity: ball falls — paddle tracks projected landing
- (II) Least action: paddle follows parabolic arc (singular, ~90%)
- (III) Spectral kick: paddle strikes upward at bounce (bang, ~10%)

## Dependency Chain

```
Step 1 (this doc)
  │
  ▼
2a (order_parameter) ──┐
2b (rho_sampler) ──────┤
2c (pmp_rho_solver) ───┤── 2d (threebody_rho) ── 2e (compare) ── DONE
                       │
  ▼ ═══════════════════╝
3a (dribble.xml) ── 3b (dribble_controller) ── DONE
```

## Reusable from 1.0 (symlinked)

- `grjl/bspline_trajectory.py` — pure trajectory maths
- `grjl/spectral_analytical.py` — eigenvector perturbation

## Verification Criteria

### Step 2

| ID | Criterion | Pass condition |
|----|-----------|----------------|
| V2.1 | `python grjl2/threebody_rho.py --solver reactive --headless` | Runs without error |
| V2.2 | `python grjl2/threebody_rho.py --solver pmp --headless` | Runs without error |
| V2.3 | Spectral gap maintained | λ₁ ≥ ε for all t |
| V2.4 | ρ shows phase transitions | ρ crosses 1.0 at bang-singular switches |
| V2.5 | w(ρ) differentiable | dw/dρ analytical vs finite-diff, rel error < 1e-6 |
| V2.6 | Cost finite | J[u] finite, comparable to 1.0 |
| V2.7 | Comparison plot | `compare_v1_v2.py` produces figure |
| V2.8 | Bang fraction | ~10% of time in bang arc |

### Step 3

| ID | Criterion | Pass condition |
|----|-----------|----------------|
| V3.1 | `python grjl2/dribble_controller.py --headless` | Runs without error |
| V3.2 | Ball bounces | ≥ 3 bounce cycles |
| V3.3 | ρ time series | Clear spikes at each bounce |
| V3.4 | Paddle tracks ball | Paddle under projected landing |
| V3.5 | Three-term visible | Singular arcs ≫ bang arcs |
