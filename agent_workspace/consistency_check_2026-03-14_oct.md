# Self-Symbolic Consistency Check: Optimal Cycle Theory

**Date:** 2026-03-14
**Document:** `independent_volume/optimal_cycle_theory/` (56 pages, 22 sections + bibliography)
**Central claim:** The optimal cycle $(\mathbb{R}_{>0}, \times) \xrightarrow{\log} (\mathbb{R}, +) \xrightarrow{\text{Fourier}} (\mathbb{Z}, +) \xrightarrow{\exp} (\mathbb{R}_{>0}, \times)$ carries holonomy $H(f) = \sum_{k=1}^{\infty} k|c_k|^2$ that vanishes iff $f$ is Gaussian.

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 11 (6 reinforced, 5 unresolved, 0 contradicted) |
| STRUCTURAL tensions | 11 |
| COSMETIC tensions | 4 |
| Time-axis issues | 1 drift, 0 breaking |
| Unresolved confusions (fresh-eyes) | 8 |
| Notation collisions | 2 HIGH, 2 MEDIUM |
| Reference integrity | 0 dangling, 61 orphan labels |
| Citation integrity | 0 missing, 4 unused bibliography entries |

**Overall assessment:** The abelian core (Part I, Sections 1--12) is well-supported -- all LOAD-BEARING tensions in Part I are REINFORCED by cross-validation. The five UNRESOLVED tensions cluster in Part II (Lie group control), where implicit assumptions about metric choice, mixing time, and spectral gap are never made explicit. The fresh-eyes scan found 8 genuine confusions, most involving undefined quantities or silent convention changes.

---

## Critical Findings (requires action)

### 1. Hopf--Cole metric dependence (UNRESOLVED)
**File:** `lie-group-intro.tex:3`, `mppi.tex:10-26`
**Issue:** The Hopf--Cole linearization requires the control cost metric to match the diffusion metric (both defined by the same inner product on $\mathfrak{g}$). For compact semisimple groups, the bi-invariant metric (negative Killing form) is canonical. For $SE(3)$ (the main application target), no bi-invariant metric exists. The choice of metric affects whether linearization is exact. **Never acknowledged.**

### 2. CLT rate on $SE(3)$ ignores mixing time (UNRESOLVED)
**File:** `mppi.tex:1-7`, `articulated.tex:184-196`
**Issue:** The paper claims $O(N^{-1/2})$ convergence "independently of $\dim G$." This is technically correct as a CLT statement for i.i.d. samples. However, on $SE(3)$ (no spectral gap, polynomial convergence), the effective sample size after Boltzmann reweighting may degrade -- weights may concentrate on few trajectories, inflating the variance constant hidden in the $O$. The document acknowledges the vanishing spectral gap (`noncompact-groups.tex:13`) but never analyzes its impact on MPPI sample efficiency.

### 3. Three connections in articulated.tex are unformalized (UNRESOLVED)
**File:** `articulated.tex:162-197`
**Issue:** Connection (i) correctly identifies $\mathrm{Ad}/\mathrm{Ad}^*$ but the "Peter--Weyl sparsity" claim is an unproven analogy. Connection (ii) identifies the Schur complement / Riccati structure but the parallel with HJB Riccati is not formalized. Connection (iii) inherits the metric assumption gap and the sample efficiency issue. All three are stated as remarks, which is appropriate, but the word "connection" overpromises.

### 4. Small-time Gaussian approximation lacks error bounds (UNRESOLVED)
**File:** `compact-groups.tex:35-40`
**Issue:** The heat kernel approximation $p_t(g) \approx (2\pi t)^{-d/2} \exp(-\|\exp^{-1}(g)\|^2 / 2t)$ is stated as $t \to 0^+$, $g \to e$. No error bounds or crossover analysis. The exact heat kernel formula (`spectral-decomp.tex:97-106`) implicitly contains the transition, but Varadhan's short-time asymptotics is not cited.

### 5. Burg existence/uniqueness cited but not proved (UNRESOLVED)
**File:** `optimal-cycle.tex:73-80`
**Issue:** The constrained minimizer's existence is hedged ("when it exists") and deferred to Burg's thesis. Classical result, appropriate citation, but not self-contained.

### 6. Student $t_\nu$ spectral density undefined (fresh-eyes)
**File:** `optimal-cycle.tex:136-146`
**Issue:** The mapping from the Student $t_\nu$ distribution (on $\mathbb{R}$) to a spectral density $f_{t_\nu}$ on $\mathbb{T}$ is never defined. The critical value $\nu^*$ is asserted to exist but never computed or bounded.

### 7. $D_n(f)$ used before defined (fresh-eyes)
**File:** `optimal-cycle.tex:36`, `introduction.tex:17`
**Issue:** The Toeplitz determinant $D_n(f)$ is used in Section 9 and the introduction before its definition in Section 10 (`hardy-spaces.tex:140`).

### 8. Undefined $R$ and $\Sigma$ in Hopf--Cole (fresh-eyes)
**File:** `mppi.tex:24`
**Issue:** The relation $\lambda R^{-1} = \Sigma$ introduces $R$ and $\Sigma$ without definition. Vestige of standard MPPI derivation not adapted to the Lie group setting.

### 9. Silent convention change: factor of $\frac{1}{2}$ (fresh-eyes)
**File:** `heat-semigroup.tex:37` vs `spectral-decomp.tex:97`
**Issue:** Section 8 uses $\partial_t p = \frac{1}{2}\Delta_G p$; Section 12 uses $\partial_t u = -\Omega u = \Delta_G u$ (no $\frac{1}{2}$). The convention changes silently between variance $t$ and variance $2t$ normalization.

### 10. Sobolev seminorm off by factor of 2 (fresh-eyes)
**File:** `optimal-cycle.tex:29`
**Issue:** $H(f) = \sum_{k=1}^{\infty} k|c_k|^2$ is identified as "the $H^{1/2}(\mathbb{T})$ Sobolev seminorm" but equals half the standard seminorm $\sum_{k \in \mathbb{Z}} |k||c_k|^2$ for real-valued $\log f$. Non-standard convention, unstated.

### 11. $n$ vs $\nu$ relationship unstated (fresh-eyes)
**File:** `optimal-cycle.tex:97`
**Issue:** The CLT rate $O(1/\sqrt{n})$ is applied to the Student $t_\nu$ re-cycle without establishing how $\nu$ (degrees of freedom) relates to $n$ (sample size).

---

## Structural Findings (author's discretion)

### Phase 1 STRUCTURAL tensions (11 total)

| File | Lines | Issue |
|------|-------|-------|
| `additive-clt.tex` | 13-27 | Characteristic function expansion uniformity not justified explicitly (standard, presentation gap) |
| `multiplicative-clt.tex` | 14-28 | Measure-theoretic compatibility of log transformation not stated (correct but implicit) |
| `foundations.tex` | 143-149 | Measure-theoretic Bayes' denominator non-degeneracy condition unstated |
| `hardy-spaces.tex` | 181-193 | Szego constant $E(f) \in (0,\infty)$ nonzero claim: outer function regularity in $H^{1/2}$ |
| `spectral-decomp.tex` | 5-22 | Non-abelian exponential map generalization: decorative extension, abelian case self-contained |
| `hardy-spaces.tex` | 51-68 | Hardy projection commutation across groups: Mellin domain well-definedness |
| `noncompact-groups.tex` | 3-15 | Mixing time on non-compact groups undermines dimension-free claims |
| `hjb.tex` | 5-21 | Riccati decoupling for product groups $SE(3) \times \mathbb{T}^n$ not derived |
| `forward-only.tex` | 3-50 | Constructive enumeration without consistency proof for weighted estimator |
| `riccati.tex` | 19-42 | Riccati-to-nonlinear cost gap: "cost of leaving the Riccati regime" is rhetorical, not quantified |
| `optimal-cycle.tex` | 74-80 | Prediction error monotonicity $\sigma_t^2 \downarrow$ stated without proof |

### Phase 4 fresh-eyes: notable RESOLVED confusions

- **Cycle diagram duality** (`introduction.tex:9`): The cycle labels $\widehat{A} = (\mathbb{Z}, +)$ but $\widehat{(\mathbb{R},+)} = \mathbb{R}$, not $\mathbb{Z}$. Resolved: the cycle operates on $\mathbb{T}$ (whose dual is $\mathbb{Z}$), but the diagram is a heuristic schematic, not a literal commutative diagram.
- **Sign conventions in Hopf--Cole** (`mppi.tex:28-30`): Consistent when backward PDE nature and Feynman--Kac correspondence are properly tracked.
- **IUT analogy** (`hardy-spaces.tex:216-218`): Explicitly flagged as "structural analogy" without formal correspondence.

---

## Cosmetic Findings

| File | Lines | Issue |
|------|-------|-------|
| `foundations.tex` | 35 | Conditional probability undefined for null events; gap to conditional expectation not flagged |
| `introduction.tex` | 21 | "constant (Gaussian spectral density)" conflates spectral-domain and time-domain statements |
| `optimal-cycle.tex` | 152-162 | "Only Gauss sees the Gaussian" epistemological remark: unfalsifiable philosophical gloss |
| `concluding.tex` | 23-30 | "Truth is $\nu = \infty$, which is never reached but always approached -- almost surely" uses probabilistic language metaphorically |

---

## Symbolic Integrity

### 5a. Notation consistency

| Symbol | Meaning 1 | Meaning 2 | Meaning 3 | Severity |
|--------|-----------|-----------|-----------|----------|
| $\Omega$ | Sample space (`foundations.tex`) | Casimir operator (`spectral-decomp.tex`) | Feasible set (`optimal-cycle.tex`) | **HIGH** |
| $\rho$ | Probability density (`spectral-decomp.tex:134`) | Irreducible representation (`spectral-decomp.tex:55`) | -- | **HIGH** |
| $\mathcal{M}$ | Mellin transform (`multiplicative-clt.tex`) | Spatial inertia (`articulated.tex`) | -- | MEDIUM |
| $\pi$ | Literal constant 3.14... | Representation variable (`spectral-decomp.tex`) | -- | MEDIUM |

**Undefined symbols in `articulated.tex`:** $\mathrm{Ad}$, $\mathrm{ad}$, $\mathrm{Ad}^*$, $\mathrm{ad}^*$, $\mathrm{Sym}^+$ used without formal definition (standard in geometric mechanics but not introduced).

### 5b. Reference integrity

- **Dangling references:** 0 (all `\cref`, `\ref`, `\eqref` resolve)
- **Orphan labels:** 61 (defined but never explicitly referenced -- many are implicit structural anchors)

### 5c. Citation integrity

- **Missing citations:** 0 (all `\cite` keys have `\bibitem`)
- **Unused bibliography entries:** 4
  - `Burg` -- referenced by name but not `\cite`d
  - `Davenport` -- never mentioned
  - `GrenanderSzego` -- never mentioned
  - `IwaniecKowalski` -- never mentioned

### 5d. Theorem-dependency chain

- No circular dependencies detected.
- Forward reference: $D_n(f)$ used in Section 9 before defined in Section 10 (flagged above).
- Forward reference: Theorem 9.2 parts (ii)-(iii) deferred to Theorem 10.6 (acceptable, noted in proof).

### 5e. Color/style consistency

No semantic colors used. Not applicable.

---

## Phase 2 Cross-Validation Summary

| # | Tension | Verdict | Location |
|---|---------|---------|----------|
| 1 | Holonomy trichotomy domain | **REINFORCED** | `optimal-cycle.tex:16` defines $f > 0$ a.e., $\log f \in L^1(\mathbb{T})$ |
| 2 | Dual map = identity | **REINFORCED** | `fourier-mellin.tex:39-42` proves it; `lca-groups.tex:20-22` confirms parametrization |
| 3 | Burg existence/uniqueness | **UNRESOLVED** | Proof sketch + citation; hedged by "when it exists" |
| 4 | Fourier injectivity / semigroup | **REINFORCED** | Levy theorem (`lca-groups.tex:41-43`); Bochner guarantees closure |
| 5 | F.&M. Riesz / outer function | **REINFORCED** | Correctly invoked; boundary regularity not needed for conclusions |
| 6 | Half-shift $\sigma_M^* = 1/2$ | **REINFORCED** | Proof correct; boundary excluded; conductor harmless; disclaimer at line 47 |
| 7 | Hopf-Cole metric dependence | **UNRESOLVED** | $SE(3)$ has no bi-invariant metric; never acknowledged |
| 8 | Small-time vs spectral gap | **UNRESOLVED** | Heat kernel formula implicit; no error bounds; Varadhan not cited |
| 9 | $O(N^{-1/2})$ on $SE(3)$ | **UNRESOLVED** | CLT rate correct for i.i.d.; weight concentration on non-compact groups not analyzed |
| 10 | Three articulated connections | **UNRESOLVED** | Ad correct; Riccati suggestive; Peter--Weyl sparsity is analogy |
| 11 | $H(f)=0$ iff Gaussian | **REINFORCED** | Proven at `optimal-cycle.tex:41-43`; proof is immediate from definition |

---

## Phase 3 Time-Axis Summary

| Severity | Count | Details |
|----------|-------|---------|
| BREAKING | 0 | -- |
| DRIFT | 1 | 4 uncited `\bibitem` entries (`Burg`, `Davenport`, `GrenanderSzego`, `IwaniecKowalski`) |
| HARMLESS | 6 | All `\cref` resolve; no orphan text from `\cite{OCT}` removal; lie-group-intro.tex references valid sections; clean LaTeX log |

---

## Action Items (prioritized)

### Must fix (threatens correctness or clarity)
1. Define Student $t_\nu$ spectral density: specify the mapping $t_\nu \to f_{t_\nu}$ on $\mathbb{T}$
2. Fix Sobolev seminorm factor: either state $H(f) = \frac{1}{2}\|{\log f}\|_{H^{1/2}}^2$ or define the one-sided convention
3. Remove or define $\lambda R^{-1} = \Sigma$ in `mppi.tex:24`
4. Reconcile $\frac{1}{2}$ convention between Sections 8 and 12

### Should fix (improves rigor)
5. Acknowledge Hopf--Cole metric assumption for non-semisimple groups
6. Add forward definition or remark for $D_n(f)$ before Section 9
7. State the relationship between sample size $n$ and Student $t$ degrees of freedom $\nu$
8. Add `\cite{Burg}` to the two passages mentioning Burg by name

### Consider (author's judgment)
9. Prune 3 never-cited bibliography entries (`Davenport`, `GrenanderSzego`, `IwaniecKowalski`)
10. Acknowledge weight concentration / effective sample size issue for MPPI on non-compact groups
11. Add remark on $\Omega$ notation overload (sample space vs Casimir vs feasible set)
