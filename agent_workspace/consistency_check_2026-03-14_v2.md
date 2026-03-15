# Self-Symbolic Consistency Check v2: Code ↔ Paper Algorithm

**Date:** 2026-03-14
**Central claim:** The optimal cycle algorithm is a finite composition of exp, log, and linear algebra (Prop 4.1), with exact Riccati compression on the centroidal model and O(N^{-1/2}) convergence.
**Architecture:** Riccati plans on centroidal model (exactly linear); MuJoCo realizes torques (step 8). This is standard MPC — not a contradiction.

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 2 (both CONTRADICTED) |
| STRUCTURAL tensions | 3 |
| COSMETIC tensions | 1 |
| Verified consistent | 7 items |
| LaTeX mechanical | All clean (0 dangling refs, 0 dangling cites) |

---

## Critical Findings (requires action)

### T1. Cost Function Mismatch — LOAD-BEARING / CONTRADICTED

**Paper** (articulated.tex:591–596):
```
J^(i) = Σ_t [‖x_t − x_ref‖²_Q + ‖u_t‖²_R − ε Σ_k log h_k] Δt + Φ(x_H)
```

**Code** (run_experiment.py:602–645, `run_rollout_tvlqr` cost loop):
```python
costs[i] = c_vel + c_height + c_height_bar + c_ori_bar + c_joint_bar
```

| Term | Paper | Code |
|------|-------|------|
| ‖x − x_ref‖²_Q (full 13-state) | ✓ | ✗ only velocity + height |
| ‖u‖²_R (control cost) | ✓ | ✗ absent |
| −ε Σ_k log h_k (foot-contact barrier) | ✓ | ✗ absent |
| Height corridor barrier | ✗ | ✓ −w·ε·(log(z−z_min)+log(z_max−z)) |
| Orientation barrier | ✗ | ✓ −w·ε·(log(φ_max²−φ²)) |
| Joint-limit barrier | ✗ (in step 8 only) | ✓ −w·ε·Σ log(...) |

**The two directions:**
- Code **adds** practical barriers (height corridor, orientation, joint limits) not in the algorithm
- Code **omits** the paper's defining terms (control cost, foot-contact barrier)

The foot-contact barrier −ε log h_k is the term that couples MPPI temperature to contact sharpness — the paper's central "sextuple ε unification." Without it, the Boltzmann weights don't see contact barrier cost.

The Riccati solver internally optimizes ‖u‖²_R (it's in the LQR objective at riccati_lqr.py:119), but the outer MPPI cost doesn't include it. This means the inner and outer objectives disagree.

**Files:** `run_experiment.py:645` vs `articulated.tex:591-596`

---

### T2. Dual Ascent: Additive vs Multiplicative — LOAD-BEARING / CONTRADICTED

**Paper** (articulated.tex:609–619):
```
If S < H_target:  ε ← α_up · ε      [multiplicative]
Else:             ε ← α_down · ε
Then:             H_target ← γ · H_target
```

**Code** (run_experiment.py:670, mppi_cycle.py:183):
```python
epsilon += alpha_dual * (H_target - entropy)    # additive gradient ascent
epsilon = clip(epsilon, epsilon_min, epsilon_max)
```

| Property | Paper (multiplicative) | Code (additive) |
|----------|----------------------|-----------------|
| Update | ε ← α·ε | ε ← ε + α·(H−S) |
| Convergence in log(ε) | Linear (geometric) | Sublinear |
| Parameter meaning | α_up, α_down are ratios | alpha_dual is step size |
| Config value | N/A | alpha_dual = 0.1 |
| Monotonicity | ε always decreases when S > H | Can overshoot |

The paper's re-cycle convergence analysis (student-t_ν → Gaussian, H(f) ∼ O(1/ν)) assumes the multiplicative form.

**Files:** `run_experiment.py:670`, `mppi_cycle.py:183` vs `articulated.tex:609-619`

---

## Structural Findings

### T3. Sampling Distribution: Student-t vs Gaussian — STRUCTURAL

**Paper** step 1 (articulated.tex:569): `δφ ∼ N(0, Σ_φ)`
**Code** (gait_sampler.py:38-62): `sample_student_t_torus(nu, mu, Sigma, N, key)` with nu evolving

The code is *more faithful to the paper's theory* (§optimal-cycle describes student-t → Gaussian convergence) than to the paper's algorithm block. The algorithm simplifies to Gaussian for clarity. For ν → ∞ they agree; for early iterations the Student-t has heavier tails (broader exploration).

Not load-bearing: Riccati steps are exact for any sampled gait; Boltzmann reweighting applies identically.

### T4. Foot Positions: Approximate vs FK-Computed — STRUCTURAL

**Config** (config.py:9-14):
```
FL: [0.1934, 0.0465, -0.27]   ← hip y-offset only, z = standing height
```

**FK from go2.xml** (lateral offset = 0.0955):
```
FL: [0.1934, 0.142, -0.265]   ← hip + lateral, z from link geometry
```

The lateral y-offset differs by ~3× (0.0465 vs 0.142). This affects the B matrix's rotational block: roll torque from forces is underestimated. The Riccati is still "exact for the centroidal model" — but the centroidal model has inaccurate parameters.

In MuJoCo execution (step 8), `step_tvlqr` uses the real Jacobian J^T from the simulator, so torque mapping is correct. The mismatch only affects the planning model.

### T5. Cost Decomposition: Paper Theory vs Algorithm Block — STRUCTURAL

The paper's cost decomposition paragraph (articulated.tex:477-502) says:
> J_barrier collects **all** log-barrier contributions (contact, height limits, orientation, joint limits)

But the algorithm block step 4 only includes −ε Σ log h_k (foot-contact). The other barriers appear only in step 8 (inner loop, torque space). The theory describes what the cost *should* include; the algorithm block presents a simplified version.

The code actually implements the theory's richer cost (with height, orientation, joint barriers) — making the code *more aligned with the theory* than the algorithm block.

---

## Cosmetic Findings

### T6. B-Spline vs Phase Parameterization
`run_rollout_tvlqr` samples B-spline control points (R^{4×n_knots}); paper algorithm samples phases on T^3. The B-spline generalization is documented in articulted.tex:228-253. Both valid.

---

## Verified Consistent (7 items)

| Item | Paper | Code | Status |
|------|-------|------|--------|
| Barrier scale σ_k = ε/(h_k+ε) | tex:577 | gait_sampler.py:309-326 | ✓ algebraically identical |
| Riccati recursion K, P | tex:366-367 | riccati_lqr.py:177-209 | ✓ exact match |
| Boltzmann w ∝ exp(−J/ε) | tex:600 | run_experiment.py:660-662 | ✓ with stability shift |
| Circular mean on T^3 | tex:604-607 | gait_sampler.py:106-119 | ✓ |
| A matrix (double integrator) | tex:359-361 | riccati_lqr.py:51-53 | ✓ |
| c vector (gravity + phase) | tex:361 | riccati_lqr.py:56-58 | ✓ |
| Torque blend σ·J^Tf + (1−σ)·PD | tex:626-631 | quadruped_dynamics.py:458-478 | ✓ |

---

## Symbolic Integrity (Phase 5)

### References: ALL CLEAN ✓
- 0 dangling references (all \eqref, \cref, \ref resolve)
- Algorithm block: all 8 references verified (eq:foot-height, eq:riccati-tvlqr, eq:pid-impedance, eq:joint-barrier, eq:anti-windup, prop:forward-only, prop:student-convergence, sec:riccati)

### Citations: ALL CLEAN ✓
- 0 dangling citations
- 17 uncited bibliography entries (reference material, expected)

---

## Action Items

**To align code with paper:**
1. Add −ε Σ_k log h_k to MPPI cost in run_experiment.py (T1)
2. Add ‖u‖²_R to MPPI cost in run_experiment.py (T1)
3. Switch dual ascent to multiplicative in run_experiment.py and mppi_cycle.py (T2)
4. Update foot positions in config.py to FK-computed values (T4)

**To align paper with code (alternative):**
1. Expand algorithm step 4 cost to include all barrier types (T5)
2. Change step 1 to note student-t option (T3)
