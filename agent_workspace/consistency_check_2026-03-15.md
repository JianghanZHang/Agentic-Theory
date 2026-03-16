# Self-Symbolic Consistency Check — 2026-03-15

**Paper:** Optimal Cycle Theory: holonomy of the additive-multiplicative loop via Fourier analysis on groups
**Central claim:** The optimal cycle R_{>0} →(log) R →(F) Z →(exp) R_{>0} carries holonomy H(f) = Σ k|c_k|², vanishing iff Gaussian. Part II applies this to Lie group control via exp : g → G.

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 3 (all UNRESOLVED — in Part I foundations) |
| STRUCTURAL tensions | 8 |
| COSMETIC tensions | 8 |
| Time-axis issues | 0 breaking, 0 drift |
| Unresolved confusions (fresh-eyes) | 6 |
| Symbolic issues | 2 notation, 0 ref, 1 citation, 0 dependency |
| Code–paper inconsistencies | 1 naming issue |

---

## Critical Findings (requires action)

### C1. Cycle diagram mislabels A = (R, +) in introduction
**Source:** Phase 4 (fresh-eyes), introduction.tex:3-12
**Issue:** The introduction's cycle diagram writes A = (R, +) →(Fourier) Â = (Z, +), but the Pontryagin dual of (R, +) is R, not Z. The dual Z corresponds to T (the circle group). All actual constructions in Section 10 (optimal-cycle.tex) work with spectral densities on T, taking Fourier coefficients indexed by Z. The diagram should read T → Z or the chain R_{>0} → R → T → Z should be made explicit.
**Severity:** LOAD-BEARING. The central claim is about this cycle; the introductory diagram is wrong.

### C2. Constrained minimizer f_t* lacks existence proof
**Source:** Phase 1 (Part I), optimal-cycle.tex:56-80
**Issue:** The constrained optimal cycle (Definition 10, Proposition 11) asserts a unique minimizer f_t* ∈ Ω_t of H(f) among spectral densities with prescribed autocovariances r_0,...,r_t. The proof invokes "Burg's theorem" (maximum-entropy AR(t) density) but does not prove that Burg's maximizer of ∫ log f equals the minimizer of H(f) = Σ k|c_k|². These are different objective functions. Existence of f_t* is assumed, not proved; the feasible set Ω_t may be non-convex.
**Severity:** LOAD-BEARING. The monotonicity H_0* ≤ H_1* ≤ ... ≤ H(f_true) and the entire "learning is holonomy increasing" narrative depend on f_t* existing.

### C3. Multiplicative CLT conditions not characterized
**Source:** Phase 1 (Part I), additive-clt.tex:15 + multiplicative-clt.tex:16
**Issue:** The multiplicative CLT substitutes X_k = log Y_k without verifying when E[log Y_1] = 0 and Var(log Y_1) < ∞ hold. For positive random variables with E[Y_1] < ∞, E[log Y_1] may not exist. The restricted class of measures for which the multiplicative CLT holds is not characterized.
**Severity:** LOAD-BEARING. Part II applies this to Lie group control; if the conditions are not met, the CLT does not hold.

### C4. Part I → Part II mathematical gap
**Source:** Phase 4 (fresh-eyes), lie-group-intro.tex
**Issue:** No theorem in Part II uses any Part I result (H(f), E(f), Szegő limit, half-shift) as a hypothesis. The connection is thematic (both use exp) rather than mathematical. A first-time reader cannot determine why the Szegő/Hardy machinery of Part I is needed for quadruped control.
**Severity:** STRUCTURAL. Does not break the central claim but undermines the paper's narrative unity.

### C5. "Re-cycle" used ≥6 times without formal definition
**Source:** Phase 4, optimal-cycle.tex:87,97,112,116,149,161
**Issue:** The term "re-cycle" is central to the constrained-cycle narrative but never defined. A reader must infer its meaning from context.

### C6. "Spectral density associated to Student t_ν" undefined
**Source:** Phase 4, optimal-cycle.tex:136
**Issue:** The paper writes "let f_{t_ν} denote the spectral density associated to the Student t_ν distribution" but never defines this association. The proof sketch treats the probability density on R as if it were a spectral density on T.

### C7. Critical ν* never computed or bounded
**Source:** Phase 4, optimal-cycle.tex:127-138
**Issue:** Proposition 10.6(i) asserts ∃ν* > 1 such that E(f_{t_ν}) < ∞ iff ν > ν*. The value ν* is never computed, bounded, or cited.

### C8. "Burg's theorem" cited by name without \cite{Burg}
**Source:** Phase 5, optimal-cycle.tex:73 and introduction.tex:27
**Issue:** "Burg's theorem" and "(Burg)" appear without \cite{Burg}, though \bibitem{Burg} exists in bibliography.tex. Should be \cite{Burg}.

---

## Structural Findings (author's discretion)

### S1. foundations.tex:424-426 — misleading "expectation commutes with log"
The remark says the duality "rests on the fact that expectation is a linear functional that commutes with the group isomorphism log." But log is nonlinear; the proof in fourier-mellin.tex uses pushforward measures, not expectation commutativity. The statement is not false (one can interpret it as pushforward), but it creates a wrong impression.

### S2. Hopf-Cole assumes bounded cost; barrier costs violate this
mppi.tex:27-32 derives the linear PDE via ψ = e^{-V/(2ε)}, which requires globally smooth V. The barrier cost V = -ε log h → ∞ as h → 0 (used in articulated.tex) violates this. The Feynman-Kac representation's behavior at infinite barriers is not discussed.

### S3. Student t holonomy rate O(1/ν) stated without derivation
optimal-cycle.tex:142-146. The Fourier coefficient decay estimate |c_k| = O(k^{-1}ν^{-1}) is asserted but not derived. The stated decay gives H = O(ν^{-2} log k), not O(1/ν).

### S4. Heat kernel approximation domain unstated
compact-groups.tex:36-40. The approximation requires |g|_exp = O(√t), not independent limits t → 0 and g → e.

### S5. "Dimension-free" O(N^{-1/2}) conflates rate with constant
forward-only.tex:19. The MC rate O(N^{-1/2}) is independent of dim G, but the constant (variance of the estimator) may grow with dimension.

### S6. Noncompact groups "typically" vanishing spectral gap
noncompact-groups.tex:11-12. True for SE(3) but not "typical" for all semidirect products.

### S7. GPI acronym used before expansion
foundations.tex:178 uses "GPI category" ~50 lines before "Generalized policy iteration" (line 227).

### S8. Contragredient reference misleading
chu-duality.tex:13 references \S\ref{sec:compact} for contragredient representations, but compact-groups.tex never uses this term.

---

## Cosmetic Findings

- **Notation overload:** `\cF` = both σ-algebra (foundations) and Fourier transform (elsewhere). `\cM` = both Mellin transform (Part I) and spatial inertia (articulated). Context disambiguates; structurally contained by Part I/II boundary.
- **Reference style inconsistency:** Mixed `\cref{sec:...}` vs `\S\ref{sec:...}` throughout.
- **Orphan bibliography entries:** BarrChuHist, Davenport, GrenanderSzego, IwaniecKowalski (never cited). Burg is cited by name but lacks `\cite`.
- **65+ orphan labels:** Structural definitions/equations; not errors.
- **Tropical Chu spaces** (chu-duality.tex:346-410): mathematically correct but never applied in any calculation.
- **Wold decomposition analogy** for non-abelian heat semigroup (spectral-decomp.tex:156-174): suggestive but structurally imprecise.
- **Quadratic form notation** (gaussian-measures.tex:5-15): multiplicative notation on additive group ambiguous.
- **Half-shift "Jacobian mechanism"** (half-shift.tex:38-40): intuitive explanation, not formal.

---

## Octonion Conjecture Verification (chu-duality.tex)

### Fano Plane: INTERNALLY CONSISTENT ✓
The 7 triads use cyclic orderings:
- T1: (1,2,3), T2: (1,4,5), T3: (1,7,6), T4: (2,4,6), T5: (2,5,7), T6: (3,4,7), T7: (3,6,5)

This is one of 480 valid octonion multiplications. Verified:
- All 21 pairs from {1,...,7} covered exactly once ✓
- Cayley-Dickson consistency: e₅·e₆ = -e₃, e₅·e₇ = e₂, e₆·e₇ = -e₁ ✓
- Associator (e₁e₂)e₅ = -e₆, e₁(e₂e₅) = +e₆ → [e₁,e₂,e₅] = -2e₆ ✓
- Alternating property: [e₁,e₂,e₅] = -[e₂,e₁,e₅] = -[e₁,e₅,e₂] ✓

**Note:** The convention differs from some standard references (which use cyclic ordering (1,6,7) rather than (1,7,6)). Recommend adding a one-line note: "We adopt the left-handed Cayley-Dickson convention compatible with the doubling e_{4+k} = e_k · e_4."

### Assignment Table: CONSISTENT ✓
The quaternionic subalgebra {1, e₁, e₂, e₃} = {PF, BB, Ri, LP} (control-loop) and the e₄-coset {e₄, e₅, e₆, e₇} = {HC, Ha, PW, AS} (spectral-analytic) are compatible with the Cayley-Dickson structure e₅ = e₁e₄, e₆ = e₂e₄, e₇ = e₃e₄.

### Evidence Items: CORRECTLY STATED
(a)-(f) in the conjecture are internally consistent with the triad table. The paper is honest about what is proved (T1 only) vs conjectured (T2-T7).

### Self-product e_i² = -1: WEAKLY SUPPORTED
The Green's function / symplectic argument is suggestive but not verified for any specific Chu object. Recommend verifying e₁² = -1 (Barrier-Boltzmann self-tensor) by explicit calculation.

---

## Code–Paper Consistency

### MEDIUM: `holonomy` diagnostic ≠ paper's H(f)
**File:** mppi_cycle.py:202
**Code:** `self.history['holonomy'].append(cost_var)` stores `jnp.var(costs_jnp)` — the variance of sampled trajectory costs.
**Paper:** H(f) = Σ_{k≥1} k|c_k|², the H^{1/2}(T) Sobolev seminorm.
**Assessment:** Conceptually related (low cost variance → holonomy decreasing) but numerically different. The docstring "holonomy → 0" conflates the two.

### All other code–paper checks: CLEAN
- State dimensions NX=13, NU=12 ✓
- Sigmoid σ = 1/(1+e^{-β}) ✓
- Barrier force scale σ = λ/(λ+1) ✓
- B-spline log-contact h = ε·exp(-β) ✓
- Viscous friction A-matrix ✓
- Contact projector Π = I - n̂n̂ᵀ ✓
- Riccati backward recursion ✓
- DARE terminal cost ✓
- Impedance controller ✓
- Anti-windup ✓
- Joint-limit barrier ✓
- Renormalization convention ✓
- No-slip cost ✓
