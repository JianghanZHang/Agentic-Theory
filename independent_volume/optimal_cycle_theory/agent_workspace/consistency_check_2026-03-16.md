# Self-Symbolic Consistency Check

**Document:** Optimal Cycle Theory (independent_volume/optimal_cycle_theory)
**Date:** 2026-03-16
**Baseline commit:** `99ada8b` (HEAD on branch `quadruped-experiment`)
**Central claim:** The optimal cycle connects (R>0, x), (R, +), (Z, +) via log/Fourier/exp with holonomy H(f) = Sum k|c_k|^2 vanishing iff Gaussian. Part II applies to Lie group control, MPPI, articulated dynamics. Eight Chu dualities are conjectured to form an octonion algebra.

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions identified (Phase 1) | 19 |
| -- reinforced by cross-validation (Phase 2) | 10 |
| -- unresolved after cross-validation | 6 |
| -- partially reinforced | 3 |
| Time-axis issues (Phase 3) | 5 (0 breaking, 1 drift, 4 harmless) |
| Unresolved confusions (Phase 4) | 2 |
| Notation collisions (Phase 5b) | 5 (2 dangerous, 3 confusing) |
| Dangling references (Phase 5a) | 0 |
| Uncited bibliography entries (Phase 5a) | 4 |
| Environment mismatches (Phase 5a) | 0 |

**Net assessment:** The core Part I abelian theory is mathematically rigorous. The Part II non-abelian extension is correctly described as local/approximate with honest acknowledgments. The main vulnerabilities are in three Part II claims that silently assume regularity conditions.

---

## Critical Findings (requires action)

### C1. Schilder's theorem on SE(3) invoked without proof or citation
- **Source:** `mppi.tex:55-59`
- **Claim:** "As epsilon -> 0, a Schilder-type large-deviation argument shows V(t,g) -> min_u{...}"
- **Problem:** Schilder's theorem requires a Gaussian measure on a Banach space. Extending to SE(3) (non-compact, semidirect product) requires non-trivial work (compactness of sub-level sets, exponential tightness). Neither proved nor cited.
- **Phase 2 verdict:** UNRESOLVED. No other chapter addresses this gap.
- **Impact:** Weakens the deterministic-limit justification for MPPI on Lie groups.
- **Suggested action:** Either cite a specific reference for large deviations on Lie groups (e.g., Dembo-Zeitouni for Riemannian manifolds), or state the result as conditional on a technical hypothesis.

### C2. Euler-Poincare reduction incompatible with barrier-augmented costs
- **Source:** `articulated.tex:38-46`, `mppi.tex:21`
- **Claim:** Dynamics follow the Euler-Poincare equation on se(3). The barrier cost -epsilon log h_k is then added.
- **Problem:** Euler-Poincare reduction requires left-invariant Lagrangian. The barrier -epsilon log h_k depends on individual foot heights, which are NOT group-invariant functions on SE(3). The barrier breaks the left-invariance that the reduction requires.
- **Phase 2 verdict:** UNRESOLVED. The document never checks invariance after adding barriers.
- **Impact:** The variational structure may not survive barrier augmentation. The control derivation's logical chain has a gap.
- **Suggested action:** Clarify that Euler-Poincare applies to the kinetic-energy part only, with barriers entering as external forcing (not through the variational structure).

### C3. DARE stabilizability/detectability silently assumed
- **Source:** `riccati.tex:26-35`, `articulated.tex:766,780`
- **Claim:** "The Feynman-Kac path integral is Gaussian and evaluates in closed form; the Boltzmann-weighted average compresses to the matrix Riccati ODE."
- **Problem:** Existence and uniqueness of the stabilizing DARE solution requires (A,B) stabilizable and (A,Q^{1/2}) detectable. These hypotheses are never stated.
- **Phase 2 verdict:** UNRESOLVED. Silently assumed throughout.
- **Impact:** STRUCTURAL for the Riccati section specifically.
- **Suggested action:** Add a one-line hypothesis "(A,B) stabilizable, (C,A) detectable" to the Riccati proposition.

### C4. "Dual ascent on epsilon" referenced but never defined
- **Source:** Referenced 4 times (articulated.tex, chu-duality.tex) as being in Section 9 (sec:cycle)
- **Problem:** Section 9 (optimal-cycle.tex) contains no "dual ascent" construction. The reader cannot find the referenced procedure anywhere in the document.
- **Phase 4 verdict:** UNRESOLVED.
- **Impact:** Readers following the cross-reference find nothing.
- **Suggested action:** Either define the dual ascent procedure in optimal-cycle.tex, or correct the references to point to where the procedure actually lives.

### C5. Entropic OT / Sinkhorn role unsubstantiated
- **Source:** `articulated.tex:888-889` (role 3 of 9 in the nonuple unification)
- **Claim:** "entropic regularization (pi_epsilon ~ e^{-c/epsilon}, Sinkhorn coupling)" is one of nine roles of epsilon.
- **Problem:** Unlike the other eight roles (backed by equations), this one is a structural analogy without formalization. No transport plan is computed, no Sinkhorn algorithm is developed.
- **Phase 4 verdict:** UNRESOLVED.
- **Impact:** The "nonuple unification" is actually an "octuple + one metaphor."
- **Suggested action:** Either develop the OT connection minimally (show that MPPI weights define a coupling measure) or downgrade this item to a remark rather than a numbered role.

---

## Structural Findings (author's discretion)

### S1. Bounded-weight assumption argued informally
- **Source:** `forward-only.tex:46-48`
- **Claim:** Weights w^(i) are bounded (bounded cost, fixed epsilon), giving O(N^{-1/2}) convergence.
- **Status:** The regularized barrier (articulated.tex:216-225) informally argues bounded weights, but no explicit bound is proved. The tracking cost ||log_G(g^{-1} g_target)||^2 is unbounded on non-compact groups.
- **Phase 2 verdict:** PARTIALLY UNRESOLVED.

### S2. Heat kernel approximation unquantified
- **Source:** `compact-groups.tex:37-40`
- **Claim:** p_t(g) ~ (2pi t)^{-d/2} exp(-||exp^{-1}(g)||^2/(2t)) as t -> 0+.
- **Status:** Stated as asymptotic with no error bound. The Riemannian metric on SO(3) is not canonically defined. Acknowledged as short-time approximation.
- **Phase 2 verdict:** PARTIALLY REINFORCED (the local regime is explicitly stated in spectral-decomp.tex:14).

### S3. Tropical Chu interpolation is a limit, not smooth deformation
- **Source:** `chu-duality.tex:397-410`
- **Claim:** epsilon interpolates continuously between Chu(Vect_R, R) and Chu(Set, R_max).
- **Status:** The Maslov limit is discontinuous (heat equation -> Hamilton-Jacobi). No completeness argument shows objects remain separated-extensional across the boundary.

### S4. Jensen gap covers only 1 of 35 triples
- **Source:** `chu-duality.tex:907-967`
- **Status:** The associator -2e_6 is computed for (e_1, e_2, e_5) only. The other 34 triples are not checked. The magnitude relationship to H(f) is noted as analogous, not proved.

### S5. Feasible set Omega_t nonemptiness unstated
- **Source:** `optimal-cycle.tex:56-66`
- **Status:** The Burg/Levinson construction implicitly guarantees existence when the Toeplitz matrix is positive definite, but this hypothesis is not stated.

### S6. Student t holonomy rate O(log nu / nu) unproved
- **Source:** `optimal-cycle.tex:149-169`, `introduction.tex:29`, `concluding.tex:39`
- **Status:** All three locations now state the same rate (corrected in 82b6f7d), but the proof sketch lacks detail on Verblunsky coefficient bounds.

### S7. Gaussian CLT characterization deferred to citation
- **Source:** `gaussian-measures.tex:73-79`
- **Status:** Proposition 9 states Gaussians are "precisely the possible CLT limits" but defers proof to Parthasarathy. Legitimate deferral to a standard reference but not self-contained.

### S8. Singular spectral measures not warned about
- **Source:** Holonomy machinery requires f > 0 a.e. with log f in L^1.
- **Status:** Each theorem correctly states its hypotheses, but the document never warns that the framework breaks for spectral measures with singular components. Gap in exposition, not in mathematics.

---

## Cosmetic Findings

- **Student t philosophical language** (`optimal-cycle.tex:174-184`): "Only Gauss sees the Gaussian" is evocative but not mathematical.
- **Free probability mentioned but undeveloped** (`concluding.tex:34-35`): Pointer to future work with no contribution.
- **Wold analogue in non-abelian case** (`spectral-decomp.tex:156-174`): Intuitive comparison, not formalized.
- **La Gioconda example** (`foundations.tex:118-132`): The linguistic claim about "the" exceeds the measure-theoretic framework.
- **Functoriality remark** (`fourier-mellin.tex:52-58`): Correct but terse; "dual map is the identity" glosses subtlety.
- **Eikonal "exact in one step"** (`mppi.tex:71-72`): Misleading rhetoric; solving eikonal is itself nontrivial.
- **Spectral gap bounds convergence** (`hjb.tex:20`): Conflates diffusion convergence with Bellman-operator convergence.

---

## Symbolic Integrity

### References
- **Dangling references:** 0
- **Orphan labels:** 67 (most are definitions/equations for display numbering; 4 orphan section labels: `sec:probability`, `sec:forward-only`, `sec:half-shift`, `sec:concluding`)
- **Label prefix inconsistency:** Remarks use both `rmk:` (most sections) and `rem:` (mppi.tex, articulated.tex, optimal-cycle.tex)

### Citations
- **Cited but missing:** 0
- **In bibliography but never cited:** 4 (`BarrChuHist`, `Davenport`, `GrenanderSzego`, `IwaniecKowalski`)

### Environment Balance
- All environments balanced across all files (19 theorems, 17 propositions, 31 proofs, 59 remarks, 21 definitions, 49 equations)

### Macros
- All 18 custom macros used. No undefined macros detected.
- `\ind` and `\op` used only once each (candidates for inlining).

### Notation Collisions

| Rank | Symbol | Collision | Severity |
|------|--------|-----------|----------|
| 1 | `\Omega` | Sample space vs Casimir operator | DANGEROUS |
| 2 | `\rho` | Irreducible representation vs probability density (in spectral-decomp.tex) | DANGEROUS |
| 3 | `\sigma` | Variance vs contact fraction vs convergence abscissa (5 meanings total) | CONFUSING |
| 4 | `P` | Probability measure vs Riccati cost-to-go matrix | CONFUSING |
| 5 | `G` | Group vs geometric mean G(f) vs Delassus operator | CONFUSING |

**Readily available fixes:**
- `\Omega` (Casimir): rename to `\Delta_G` (already used in heat-semigroup.tex for the same object)
- `\rho` (density): the paper already switches to `\pi` locally (spectral-decomp.tex:136-137); consider using `\varrho` for density throughout
- `P` (probability): ergodic.tex already uses `\mathbb{P}`; unifying would free `P` for Riccati

### Time-Axis (recent changes)
- **BREAKING:** 0
- **DRIFT:** 1 (`BarrChuHist` bibliography entry defined but never cited)
- **HARMLESS:** 4 (Student-t rate corrected consistently; sextuple->nonuple updated; label rename clean; rmk:octonion-conjecture unreferenced)

---

## Actionable Summary (prioritized)

| Priority | Item | Type | Effort |
|----------|------|------|--------|
| 1 | C4: Define "dual ascent on epsilon" or fix references | Missing content | Small |
| 2 | C3: State DARE hypotheses (stabilizable, detectable) | Missing hypothesis | Tiny |
| 3 | C2: Clarify Euler-Poincare applies to kinetic energy only | Clarification | Small |
| 4 | C1: Cite large-deviations reference for Lie groups | Missing citation | Tiny |
| 5 | C5: Downgrade Sinkhorn role or develop it | Content gap | Medium |
| 6 | Notation: Rename Casimir from Omega to Delta_G | Notation fix | Medium (global) |
| 7 | Notation: Unify P -> mathbb{P} for probability | Notation fix | Medium (global) |
| 8 | Remove 4 uncited bibliography entries | Cleanup | Tiny |
| 9 | Unify remark label prefix (rmk: vs rem:) | Cleanup | Small |
