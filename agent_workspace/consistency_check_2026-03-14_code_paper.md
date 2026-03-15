# Self-Symbolic Consistency Check: Code ↔ Paper Algorithm

**Date:** 2026-03-14
**Target:** Cross-check pre-existing implementation (`experiment/`) against formal algorithm (§articulated, lines 534–648)
**Central claim:** The optimal cycle algorithm is a finite composition of exp, log, and linear algebra (Prop 4.1), with O(N^{-1/2}) convergence (CLT rate) and exact Riccati compression within each gait sample.

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 2 (1 contradicted, 1 unresolved) |
| STRUCTURAL tensions | 5 |
| COSMETIC tensions | 3 |
| Consistent items | 7 |

---

## Critical Findings (requires action)

### T1. Cost Function Mismatch — **LOAD-BEARING / CONTRADICTED**

**Paper** (articulated.tex:591–597):
```
J = Σ_t [‖x_t - x_ref‖²_Q + ‖u_t‖²_R − ε Σ_k log h_k] Δt + Φ(x_H)
```
Three terms: state tracking, control regularization, foot-contact barrier.

**Pre-existing code** (run_experiment.py:138–183, the `run_rollout_tvlqr` path):
```python
costs[i] = c_vel + c_height + c_height_bar + c_ori_bar + c_joint_bar
```
where:
- `c_vel` = velocity error ‖v − v*‖² (no position tracking)
- `c_height` = w_height · (z − z*)² (separate height tracking)
- `c_height_bar` = −w · ε · (log(z−z_min) + log(z_max−z))
- `c_ori_bar` = −w · ε · (log(φ_max² − φ_x²) + log(φ_max² − φ_y²))
- `c_joint_bar` = −w · ε · Σ(log(q̃−a) + log(b−q̃))

**Missing from code that paper includes:**
- Control cost ‖u‖²_R (absent from run_experiment's cost accumulation)
- Foot-contact barrier −ε Σ_k log h_k (the defining barrier of the paper)

**Present in code that paper's algorithm omits:**
- Height corridor barrier (z_min, z_max)
- Orientation barrier (pitch/roll)
- Joint-limit barrier (present in paper text but not in algorithm step 4)
- Separate weighting constants per barrier type

**Impact:** The paper's convergence analysis (holonomy H(f) decreasing, student-t_ν → Gaussian) assumes the cost includes −ε log h_k. Without it, the MPPI weights don't couple to contact sharpness. The code's cost doesn't implement the "unification" the paper claims — the barriers in the cost are height/orientation/joint, not foot-contact.

**Files:** `run_experiment.py:138-183` vs `articulated.tex:591-597`

---

### T2. Dual Ascent Mechanism — **LOAD-BEARING / CONTRADICTED**

**Paper** (articulated.tex:609–619):
```
If S < H_target: ε ← α_up · ε      (multiplicative)
Else:            ε ← α_down · ε
Then:            H_target ← γ · H_target
```

**Pre-existing code** (run_experiment.py:208, mppi_cycle.py:183):
```python
epsilon += alpha_dual * (H_target - entropy)  # additive
```

The paper uses **multiplicative** scaling (ε ← α·ε with α_up > 1, α_down < 1); the code uses **additive** gradient ascent (ε += α·(H−S)).

**Impact:** Both converge ε toward 0, but:
- Multiplicative: ε decreases geometrically, the contraction rate is O(α_down^k)
- Additive: ε moves proportionally to the entropy gap, can overshoot or oscillate

The paper's specific claim "each outer iteration increases ν and decreases H(f)" (articulated.tex:644–647) relies on the monotone multiplicative update. The additive version can increase ε when S < H_target (same direction) but the step size dynamics differ.

**Files:** `run_experiment.py:208-209`, `mppi_cycle.py:183-184` vs `articulated.tex:609-619`

---

## Structural Findings (author's discretion)

### T3. Sampling Distribution — **STRUCTURAL**

**Paper** (articulated.tex:569): `δφ ∼ N(0, Σ_φ)` — Gaussian perturbation
**Pre-existing code**: `sample_student_t_torus(nu, mu, Sigma, N, key)` — Student-t with evolving ν

The pre-existing code implements a more sophisticated sampling scheme (student-t with heavy tails, parameterized by ν that implicitly tracks the re-cycle). The paper's algorithm simplifies to Gaussian. For ν → ∞ they agree; for early iterations (ν ≈ 2) the exploration behavior differs substantially.

The paper's text *does* describe student-t convergence at length (§optimal-cycle, §additive-clt), but the formal algorithm block states N(0, Σ). The code is arguably *more faithful* to the paper's theory than the paper's own algorithm block.

**Files:** `gait_sampler.py:38-62` vs `articulated.tex:567-570`

### T4. Forward Simulation Model — **STRUCTURAL**

**Paper** step 4: centroidal model (exactly linear)
```
x_{t+1} = A_d x_t + B_d(t) u_t + c_d
```

**Pre-existing code**: MuJoCo full-physics simulation
```python
sim.step_tvlqr(K_seq[t], k_seq[t], x_ref[t], scales[t], ...)
```

The paper's "Step 3 is exact—not sampled" (Remark, articulated.tex:638) and "the centroidal dynamics is affine in x" are true for the centroidal model, but the code evaluates trajectories in MuJoCo where dynamics are nonlinear. The Riccati is optimal *for the centroidal model*, not for the full MuJoCo dynamics.

This is by design (code validates theory in full physics) but the paper's remark about arithmetic completeness does not apply to the MuJoCo evaluation.

**Files:** `quadruped_dynamics.py:409-492` vs `articulated.tex:587-597`

### T5. Foot Positions — **STRUCTURAL**

**Pre-existing config** (config.py:9-14):
```python
foot_positions = [
    [ 0.1934,  0.0465, -0.27],  # FL — hip position, z = -standing_height
    ...
]
```

**Standalone optimal_cycle.py** (lines 44-53): computes actual FK through hip/thigh/calf at standing angles (0.9, -1.8). The x-coordinates shift forward (thigh swings forward at hip=0.9), the y-coordinates include the lateral offset (0.0955), and z is computed from link geometry.

Different foot positions → different B matrices → different dynamics and torque mapping. The pre-existing config uses a simplified approximation (hip position projected to ground).

**Files:** `config.py:9-14` vs `optimal_cycle.py:44-55`

### T6. Trust Region Not in Paper — **STRUCTURAL**

**Pre-existing code** (run_experiment.py:220-223):
```python
mu, sigma, kl_actual, tr_alpha = trust_region_step(
    mu, sigma, mu_prop, sigma_prop, delta_kl
)
```

The paper's algorithm step 6 is simply: `φ ← circular_mean(w, φ)`. No KL trust region projection. The code adds a safety mechanism (bisection to project onto KL ball around current distribution) that constrains the update magnitude.

**Files:** `gait_sampler.py:171-220`, `run_experiment.py:220-223` — not in paper algorithm

### T7. Default Mode Missing Riccati — **STRUCTURAL**

`run_rollout()` (the default, non-tvlqr mode) doesn't implement algorithm steps 3-4 at all. It uses pure impedance control (`step_impedance`) — no Riccati backward sweep, no optimal feedback gains. Only `run_rollout_tvlqr()` implements the full algorithm.

This means the default experiment path doesn't correspond to the paper's algorithm.

**Files:** `run_experiment.py:39-274` (run_rollout) vs `articulated.tex:581-597`

---

## Cosmetic Findings

### T8. B-Spline vs Phase Parameterization

`run_rollout_tvlqr` samples B-spline control points (R^{4×n_knots}) rather than phase offsets (T^3). The paper algorithm presents the T^3 version; the B-spline generalization is described separately (articulated.tex:228-253). Both are valid parameterizations. The paper's algorithm is the simpler special case.

### T9. Hyperparameter Values

| Parameter | Pre-existing | Standalone |
|-----------|-------------|------------|
| N_samples | 128 | 64 |
| horizon | 50 | 25 |
| dt | 0.01 | 0.02 |
| v_target | 1.0 m/s | 0.5 m/s |
| gamma | 0.97 | 0.99 |

Paper doesn't specify numerical values (correctly).

### T10. Leg Ordering Convention

Both pre-existing and standalone use FL, FR, RL, RR with FR as reference at phase 0. Paper matches: "three phase offsets φ = (φ_FL, φ_RL, φ_RR) relative to FR at phase 0" (articulated.tex:149-151). ✓

---

## Consistent Items (verified correct)

| Item | Paper | Pre-existing | Standalone |
|------|-------|--------------|------------|
| Barrier scale σ_k = ε/(h_k + ε) | ✓ | ✓ `lam/(lam+1)` | ✓ `eps/(h+eps)` |
| Boltzmann weights w ∝ exp(−J/ε) | ✓ | ✓ with stability shift | ✓ |
| Circular mean on T^3 | ✓ | ✓ `weighted_circular_mean` | ✓ |
| A matrix: ṗ=v, φ̇=ω blocks | ✓ | ✓ `build_AB` | ✓ `build_dynamics` |
| c vector: gravity c_5=−g, phase clock c_12 | ✓ | ✓ | ✓ |
| Riccati: K = S^{-1}B^TP A_d, P update | ✓ | ✓ `solve_tvlqr` | ✓ `solve_riccati` |
| Torque blend: σ·J^Tf + (1−σ)·PD | ✓ step 8 | ✓ `step_tvlqr` | N/A (centroidal only) |

---

## Recommendations

1. **Add −ε Σ log h_k to the MuJoCo cost** in `run_experiment.py`. This is the defining barrier term that couples MPPI temperature to contact sharpness — the paper's central unification claim. Without it, the "sextuple ε" story has a gap.

2. **Switch dual ascent to multiplicative** in `run_experiment.py` and `mppi_cycle.py`, matching the paper's α_up/α_down formulation. The additive version works but doesn't match the formal spec.

3. **Consider noting in the paper** that the algorithm block uses Gaussian sampling (step 1) as the limiting case, while the re-cycle theory involves student-t. Alternatively, change step 1 to state δφ ∼ t_ν(0, Σ) to match the code and the theory.

4. **Add `run_rollout_tvlqr` as the default** or document that `run_rollout` is a simplified baseline without Riccati.
