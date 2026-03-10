# Self-Symbolic Consistency Check

**Document:** `independent_volume/add_mult_clt/clt-duality-note.tex`
**Date:** 2026-03-10
**Central claim:** The additive and multiplicative CLTs are instances of a single duality phenomenon on LCA groups, connected by the Fourier–Mellin correspondence.

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 5 identified → 4 reinforced, 1 unresolved |
| STRUCTURAL tensions | 4 identified |
| Time-axis issues | 4 DRIFT, 1 HARMLESS |
| Unresolved confusions (Phase 4) | 10 |
| Symbolic issues | 2 critical, 8 moderate notation overloads; 0 dangling refs; 0 citation gaps; 47 orphan labels |

---

## Critical Findings (requires action)

### 1. LOAD-BEARING UNRESOLVED: Non-abelian CLT extension via exponential map (lines 1164–1175)

**Claim:** The CLT duality extends locally to non-abelian Lie groups because `exp` is a local diffeomorphism near the identity; "the CLT limit on any Lie group is locally the pushforward of a Gaussian on 𝔤 under exp."

**Problem:** No proof is given. The compact-group heat kernel asymptotics (line 1221–1225) are stated approximately without proof. The matrix CLT via Cartan decomposition (lines 1177–1184) is attributed to Benoist-Quint but not proved here. No quantitative bounds on the "small fluctuations" regime are provided. The central duality claim is rigorously established only in the abelian case.

**Impact:** The paper promises universality beyond the abelian case (abstract line 53, concluding remarks). This promise is not delivered.

### 2. NOTATION CRITICAL: `\cF` triple overload

`\cF` (= `\mathcal{F}`) denotes three different objects:
- **Fourier transform** (declared line 69, used §5+)
- **Sigma-algebra / event algebra** (lines 77–497, Section 1)
- **Body wrench** `\mathcal{F}_i` (lines 1646–1667, bare `\mathcal{F}` without macro)

These meanings co-occur in the same paper. The Notation paragraph (line 69) explicitly binds `\cF` to the Fourier transform; Section 1 silently rebinds it.

### 3. NOTATION CRITICAL: `\cM` dual meaning

`\cM` (= `\mathcal{M}`) denotes:
- **Mellin transform** (declared line 69, used throughout §4–8)
- **Spatial inertia matrix** `\cM_i` (lines 1641–1760, articulated-body dynamics)

### 4. UNRESOLVED CONFUSION: Uniqueness of Gaussian as Fourier fixed point (line 65)

The Introduction claims "the Gaussian is the unique probability density that is a fixed point of the Fourier transform." Theorem 6.4 (line 771) proves only existence. Remark 6.5 (line 793) notes other eigenfunctions with eigenvalue 1 exist (Hermite functions ψ_{4k}). Uniqueness among probability densities is plausible but never proved.

### 5. UNRESOLVED CONFUSION: Proposition 7.6 lacks proof (lines 1016–1032)

The proposition (CLT and prediction theory) states three results but provides no proof for parts (i) and (ii). Part (iii) cites Billingsley. This is the only formal proposition in the paper without either a proof or explicit deferral.

### 6. BIBLIOGRAPHY: `MenagerCarpentier2025` out of alphabetical order

Currently at line 1833 (between CarpentierMansard and Diaconis). Should be between MarsdenRatiu (line 1893) and MochizukiIII (line 1898).

---

## Structural Findings (author's discretion)

### STRUCTURAL tension: Gaussian uniqueness claim (lines 64–65)
The framework claims the Gaussian is characterized as the unique probability density that is both a Fourier fixed point and the heat equation fundamental solution. Neither uniqueness proof nor the equivalence of the two characterizations is given. The core duality theorem (Thm 5.1) does not depend on this, so the central claim survives.

### STRUCTURAL tension: Hardy space definition on ℝ₊ (lines 926–930)
The multiplicative Hardy space is defined as the preimage of H²(ℝ) under log, then claimed "equivalently" to be the space of functions whose Mellin transform extends analytically to Im(s) > 0. The equivalence is stated without proof.

### STRUCTURAL tension: Strong Szegő openness (lines 1110–1111)
The set {f : Σ k|c_k|² < ∞} is claimed to be an open neighborhood of f ≡ σ² in L¹(𝕋). This functional-analytic claim is unproved. The word "generically" is informal.

### STRUCTURAL tension: Ergodic–CLT bridge (lines 896–904)
The assertion that the heat semigroup simultaneously explains ensemble convergence and time-average convergence is informal. The "Fourier transform diagonalizes it whether we sum over space or over time" is stated without a precise mathematical formulation.

### DRIFT: Abstract–Introduction scope mismatch
The abstract (line 53) now mentions Peter-Weyl decomposition and compact non-abelian groups. The Introduction (lines 59–69) remains purely about LCA groups and makes no mention of non-abelian extensions.

### DRIFT: Section 1 scope vs. paper title
Section 1 "Foundations of probability theory" (lines 72–497, ~425 lines) includes extensive ML/AI content (GPI, RL, supervised learning, diffusion models, JEPA, transformers) that substantially broadens the paper beyond the CLT duality theme. The Introduction does not foreshadow this.

### DRIFT: "Concluding remarks" is the largest section
Section 10 "Concluding remarks" (lines 1154–1802, ~650 lines) contains full theorem-proof content including Peter-Weyl, Casimir operators, heat kernels, Fokker-Planck, Hopf-Cole linearization, MPPI, Riccati compression, and articulated rigid-body dynamics. The title no longer describes the content.

### DRIFT: `\rho` notation switch mid-stream
`\rho` is used for both irreducible representations (from line 1249) and probability density (from line 1303). The switch to `\pi` for representations is introduced at line 1329, but Corollary 10.4 (lines 1302–1312) already has both meanings active simultaneously. After Proposition 10.5, the text reverts to `\rho` for representations (lines 1349, 1393).

---

## Cosmetic Findings

### Notation overloads (moderate severity)
- `G` = generic sigma-algebra set (line 167) AND LCA group (§2+)
- `\mu` = probability measure AND Gaussian mean AND spatial momentum (line 1655)
- `V` = value function (§1) AND isometry (Wold) AND representation space AND HJB value function AND vector group — collision on same line 1393
- `\lambda` = Casimir eigenvalue AND Hopf-Cole parameter (line 1429) AND contact force multiplier (line 1712)
- `S` = shift operator AND partial sum AND screw axis
- `\varepsilon` = projection residual (line 230) AND diffusion coefficient (§10)

### Undefined terms
- **JEPA** (line 358): acronym never expanded, no citation
- **"Mellin spectral density"** (line 1031): used once without definition
- **"Arithmetic completeness"** (line 1482): non-standard term, never defined
- **IUT terminology** (lines 1113–1125): "Hodge theaters," "log-shell," "Indeterminacy 3" are undefined (the remark disclaims a formal correspondence, but the terms are opaque)

### Minor inconsistency
- `\bT` defined as `\R/\Z` (line 69) and as `{z ∈ ℂ : |z| = 1}` (line 509) without explicit reconciliation

### Free probability subsection (lines 1802–1803)
Asserts a parallel to the paper's framework (semicircle ↔ Gaussian, R-transform ↔ Fourier) without any formal statement or development.

---

## Symbolic Integrity

### 5a. Notation consistency
- **2 critical overloads:** `\cF` (3 meanings), `\cM` (2 meanings)
- **8 moderate overloads:** `G`, `\mu`, `\rho`, `V`, `\lambda`, `S`, `\varepsilon`, `\mathcal{F}_i`
- **0 undefined macros:** all `\newcommand`/`\DeclareMathOperator` macros are used and defined before use

### 5b. Reference integrity
- **Dangling references:** 0 (all `\cref`/`\ref`/`\eqref` targets resolve)
- **Orphan labels:** 47 (defined but never referenced). Notable: `thm:birkhoff`, `thm:pontryagin`, `thm:cond-exp-exists`, `prop:gaussian-characterization`, `prop:heat-duality`, `sec:probability`

### 5c. Citation integrity
- **Cited but not in bibliography:** 0
- **In bibliography but never cited:** 0
- **Perfect citation integrity** (all 28 cite keys ↔ bibitems match)

### 5d. Theorem-dependency chain
- No circular dependencies detected
- Forward references (`\cref{thm:add-clt}` at line 159, `\cref{thm:mellin-fourier}` at line 496) resolve correctly on second xelatex pass

### 5e. Color/style consistency
- No semantic color scheme detected in the document
- N/A
