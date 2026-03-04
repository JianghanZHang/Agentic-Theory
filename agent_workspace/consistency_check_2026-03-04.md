# Self-Symbolic Consistency Check — 2026-03-04 (Full Document)

**Document:** Agentic Theory (viability maintenance under temporal linearity)
**Central claim:** The sword is the mean — the critical threshold separating tools from threats is determined by the system's average autonomous actuation level.
**Scope:** Full document (9 main chapters + 11 appendices), all phases.

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions identified (Phase 1) | 18 |
| — Reinforced by cross-validation (Phase 2) | 4 |
| — Unresolved | 2 |
| — Contradicted | 0 |
| — Not cross-validated (lower priority) | 12 |
| Time-axis issues (Phase 3) | 10 |
| — BREAKING | 0 |
| — DRIFT | 6 |
| — HARMLESS | 4 |
| Fresh-eyes confusions (Phase 4) | 10 |
| — RESOLVED | 5 |
| — UNRESOLVED | 5 |
| Symbolic issues (Phase 5) | ~320 |
| — Dangling references | 0 |
| — Citation errors | 0 |
| — Unacknowledged notation collisions | 3 (V, E, K) |
| — Orphan labels | 314 (59% rate, low severity) |
| — New content (stochastic FOV) label collisions | 0 |

---

## Critical Findings (requires action)

### 1. Finite-cost maintenance never derived from viability axiom
**Source:** Phase 4 (fresh-eyes), results.tex:26-28
**Impact:** LOAD-BEARING — underpins the Forcing Lemma (Lemma 3.1) and Binary Fate Theorem (Theorem 3.2)

The viability axiom guarantees existence of a viable path γ: [0,∞) → K. It does NOT state that the path has finite control cost. The Forcing Lemma claims "the viability axiom requires finite-cost maintenance; therefore the sword must be resolved in finite time." This derivation is missing. The gap between path existence and cost boundedness must be bridged, or the Forcing Lemma must add an explicit finite-energy hypothesis.

### 2. Superharmonicity ≠ Lyapunov decrease along trajectories
**Source:** Phase 4 (fresh-eyes), framework.tex:295-296
**Impact:** LOAD-BEARING — underpins the entire viability geometry (Propositions 2.4–2.5)

The Lyapunov definition (Def 2.6) states D⁺V(x)(v) + W(x,v) ≤ 0 (decrease along trajectories). The geometry section uses ΔV ≤ 0 (superharmonicity as a PDE). These are related but not identical. The connection is assumed, not proved. The negative curvature result and Cheeger constant depend on this.

### 3. Uniqueness of $\bar{U}$ as baseline: argument assumes its conclusion
**Source:** Phase 4 (fresh-eyes) + Phase 1A (core theory), framework.tex:86-93
**Impact:** LOAD-BEARING — underpins the central thesis "the sword is the mean"

The massless axiom states capacity is positional, not personal. The proof claims "deviations from baseline must net to zero" → forces b = $\bar{U}$. But positionality does not imply zero-mean centering. The median, a weighted mean, or any robust statistic could equally serve. The uniqueness claim is the weakest link in the central thesis.

### 4. d = 4 intersection criterion under Lorentzian signature
**Source:** Phase 2 (cross-validation T4), fields2022.tex:209-229
**Impact:** LOAD-BEARING — underpins the mapping of Fields Medal results to agentic framework

The Hausdorff dimension intersection theorem is topological (Euclidean). Applying it to physical spacetime with causal constraints is not formally justified. The control-bandwidth argument in manipulation.tex:rem:m-d4 provides partial mitigation (the scaling arises from control bandwidth, not spacetime metric), but this is stated as a remark, not proved.

### 5. Three new symbol uses not declared in notation-unification remark
**Source:** Phase 3 (time-axis), meanfield.tex → framework.tex:714-748
**Impact:** DRIFT — rem:notation-unification claims exhaustive cataloging

Recent commits introduced: κ as Lipschitz constant (meanfield.tex:392), ρ as parameter-variation rate (meanfield.tex:427), φ as external field map (meanfield.tex:165,338). These are fourth/third uses not listed in the remark. Either update the remark or use different local symbols.

---

## Structural Findings (author's discretion)

### Phase 2 — Cross-Validation Results

| Tension | Verdict | Key Evidence |
|---------|---------|-------------|
| T1: Strategic $\bar{U}$ gaming | REINFORCED | Xiao He = unstable deferral (framework.tex:864); Obs expansion creates swords (results.tex:151); clique amplification acknowledged (meanfield.tex:209) |
| T2: Circular K definition | REINFORCED | thm:massgap (calculus.tex:715) provides 4 non-circular spectral characterizations |
| T3: Full observability assumed | REINFORCED | prop:detection-derivation derives from finite B; manipulation.tex instantiates bounded camera |
| T5: Structure vs. agency (Mulan) | UNRESOLVED | Declared scope limitation (framework.tex:103, rem:scope); framework excludes intentionality by design |
| T6: Wind breaks force closure | REINFORCED | prop:m-wind (manipulation.tex:1520) formalizes 3 regimes; training curriculum includes wind annealing |

### Phase 1 — Notable STRUCTURAL tensions (not cross-validated)

- **Bypass "in time" unformalized** (framework.tex:43-48): Continuous-time model allows instantaneous king reaction, contradicting the bypass intuition. Needs explicit time delay or discrete-time formulation.
- **Unbounded cost assumption not proved** (results.tex:5-29): A "barely threatening" sword could have bounded cumulative cost, softening the binary lifecycle into a continuum.
- **Water dynamics assume monotone depletion** (discussion.tex:49-117): No regeneration model; real collapses are often cyclical.
- **Kalman duality requires control-affine structure** (threebody.tex:768-800): Non-linear damping or position-dependent control authority breaks transpose duality.
- **"Stable until gone" assumes synchronized thresholds** (triad.tex:136-142): Eigenvalue argument depends on all three variables simultaneously having well-defined thresholds.

### Phase 4 — Remaining UNRESOLVED confusions

- **"Execution chain" used 6+ times but never formally defined** (framework.tex:763, results.tex:184). The Breakpoint Strategy (Corollary 3.4) depends on it.
- **F_r(x) used but never formally defined** (framework.tex:633-640). Appears to be {f_r(x,a) : a ∈ U_r} but this is never stated.

---

## Cosmetic Findings

### Phase 3 — Time-axis DRIFT

- **E overloading within meanfield.tex**: E = target event (line 280) and E = edge set (line 312), 32 lines apart.
- **$\mathcal{X}$ used without definition** (meanfield.tex:332-396): per-agent state space, while framework uses S.
- **Elided hypotheses** in manipulation.tex:954-959: convergence claimed from spectral gap alone, but referenced theorems need 4 additional conditions.
- **δ vs λ₁ conflation** (meanfield.tex:369-431): Two different constants for different results claimed equivalent without bridge theorem.
- **Finite G vs infinite G∞ spectral transfer** (meanfield.tex:189-398): λ₁ defined on finite graph, used on infinite unrolled DAG without transfer conditions.
- **Edge notation inconsistency**: (u,v) ∈ E (manipulation.tex) vs (u → v) ∈ E (meanfield.tex).

### Phase 5 — Symbolic Integrity

- **Unacknowledged V collision**: Lyapunov function (framework), vertex set (calculus/meanfield), continuation value (govfi) — 3 distinct meanings across 7 files.
- **Unacknowledged E collision**: Edge set vs. target event — both in meanfield.tex within 30 lines.
- **K collision**: Viability kernel vs. hierarchy depth (zhongxian) vs. MPPI samples (manipulation) vs. Fourier dimension (manipulation).
- **0 dangling references, 0 citation errors** — reference and citation integrity is perfect.
- **314 orphan labels** (59% of all labels) — typical for a document this size; low severity.
- **17 new labels from stochastic FOV section**: 0 collisions, 4 self-referenced, 13 orphaned (expected for new content).

---

## Verdict

The document is **internally consistent** at the level of formal logic: **0 contradictions** found between chapters. The central claim "the sword is the mean" survives cross-validation — every LOAD-BEARING tension tested against other chapters was either reinforced or identified as a declared scope boundary.

**Three genuine gaps require attention:**
1. The finite-cost → finite-time derivation in the Forcing Lemma
2. The superharmonicity bridge from Lyapunov definition to PDE condition
3. The uniqueness argument for $\bar{U}$ (strengthening needed, or acknowledge non-uniqueness)

**Two deliberate scope boundaries are identified (not errors):**
- The d=4 Hausdorff criterion under Lorentzian signature (mathematical gap, mitigated by control-bandwidth argument)
- Structure vs. agency indistinguishability (declared modeling choice)

**Immediate fix:** Update `rem:notation-unification` in framework.tex for 3 new symbol uses from recent commits.

---

*Generated by five-phase self-symbolic consistency check protocol.*
*Phases: 4×Phase 1 (tension identification), Phase 2 (cross-validation), Phase 3 (time-axis), Phase 4 (fresh-eyes), Phase 5 (symbolic).*
*Total agents dispatched: 9. Date: 2026-03-04.*
