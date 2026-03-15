# Self-Symbolic Consistency Check — `clt-duality-note.tex`

**Date:** 2026-03-10 (post categorical GPI insertion)
**Document:** `independent_volume/add_mult_clt/clt-duality-note.tex` (1518 lines, 41 pages)
**Central claim:** The additive and multiplicative CLTs are dual via Fourier–Mellin on LCA groups; §1 now includes the GPI category $\mathsf{Proj}_Y$, the In-context GPI Theorem, and the categorical formalization of reinforcement learning as σ-algebra lattice navigation.

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 5 (0 reinforced, 3 unresolved, 2 contradicted) |
| Time-axis issues | 1 breaking, 5 drift, 5 harmless |
| Unresolved confusions (fresh-eyes) | 7 |
| Symbolic issues | 2 notation (medium), 3 notation (low), 0 reference, 0 citation |

---

## Critical Findings (requires action)

### C1. FPE sign error — line 1324

The Fokker–Planck equation displays $\partial_t \rho = +\varepsilon\,\Omega\rho - \mathrm{div}_G(\rho\,b)$. With $\Omega = -\sum X_i^2$ (Definition, line 1277) having eigenvalues $\lambda_\rho \geq 0$, the term $+\varepsilon\Omega$ produces exponential *growth*, not diffusion. The proof sketch (line 1342) correctly states the generator as $\mathcal{L}f = -\varepsilon\Omega f + X_b f$, and all derived results (lines 1330, 1336, 1338) use the correct sign $-\varepsilon\lambda_\pi$. The displayed equation should read $\partial_t \rho = -\varepsilon\,\Omega\rho - \mathrm{div}_G(\rho\,b)$.

**Sources:** Phase 4 (U3)

### C2. HJB sign error — line 1386

Same sign error propagated: $\partial_t V + \varepsilon\,\Omega V + \min\{\ldots\} = 0$ should be $\partial_t V - \varepsilon\,\Omega V + \min\{\ldots\} = 0$, consistent with the generator $\mathcal{L} = -\varepsilon\Omega + X_b$.

**Sources:** Phase 4 (U4)

### C3. Phantom symbol $\sigma(\xi) = 4\pi^2|\xi|^2$ — line 1286

The text references "the Fourier symbol $\sigma(\xi) = 4\pi^2|\xi|^2$ from `\cref{def:laplacian}` and `\cref{ex:laplacian-symbol}`." Two errors: (a) the symbol function is called $Q$, not $\sigma$, throughout Sections 6–7 (line 820); (b) for $G = (\mathbb{R},+)$, the value is $Q(\xi) = \xi^2$ (line 828), not $4\pi^2|\xi|^2$. The value $4\pi^2 n^2$ appears only for $G = (\mathbb{T},+)$ (line 830).

**Sources:** Phase 3 (F6), Phase 4 (U5)

### C4. Divergent constant $C^2 = \sum d_\rho^2$ — line 1305

The spectral gap corollary (line 1300) states $C^2 = \sum_{[\rho]\neq\mathbf{1}} d_\rho^2$ "depends only on $G$." This sum diverges for any compact Lie group of positive dimension (by Weyl's dimension formula, $d_\rho$ grows polynomially and the sum over all representations diverges). The bound $\|p_t - 1/\mathrm{vol}(G)\|_2 \leq Ce^{-\lambda_1 t}$ is vacuous as stated. A correct formulation: $\|p_t - 1/\mathrm{vol}(G)\|_2 \leq e^{-\lambda_1 t}\|p_0 - 1/\mathrm{vol}(G)\|_2$ for $L^2$ initial data, or replace $C$ with the $t$-dependent heat trace.

**Sources:** Phase 1 (T14), Phase 4 (U14)

### C5. $\mathcal{E}_Y$ called "endofunctor" — line 278

Definition 1.9 (line 266–269) defines $\mathcal{E}_Y : \mathsf{Proj}_Y \to L^2(\Omega, \mathcal{F}, P)$. Its codomain is $L^2$, not $\mathsf{Proj}_Y$. An endofunctor maps a category to itself. Line 278 calls both $\mathcal{E}_Y$ and $\mathcal{I}$ "endofunctors," which contradicts the definition. The GPI diagram (line 297) confirms the type mismatch: $\mathcal{G}_0 \xrightarrow{\mathcal{E}} V_0 \xrightarrow{\mathcal{I}} \mathcal{G}_1 \to \cdots$.

**Sources:** Phase 1 (T3), Phase 3 (F7), Phase 4 (U2)

### C6. Improvement operator $\mathcal{I}$ is not a functor; GPI $\neq$ filtration — CONTRADICTED

The improvement operator (lines 290–293) is a *choice* function: "select a new $\mathcal{G}' \in \Lambda$ with smaller residual." This is not a structure-preserving map. Furthermore, GPI produces σ-algebras with decreasing residuals, but not necessarily *nested* σ-algebras — a σ-algebra with smaller residual need not contain the previous one. Yet Theorem 1.12 (In-context GPI) requires a filtration $\mathcal{G}_0 \subseteq \mathcal{G}_1 \subseteq \cdots$. The in-context case (context extension) does produce a filtration, which is why the theorem applies there, but the general GPI description overclaims.

**Sources:** Phase 1 (T3), cross-validated as CONTRADICTED

### C7. Szegő "necessity" overclaim — line 1108

"processes converging to the Gaussian limit necessarily satisfy the Szegő condition $\int\log f > -\infty$" is false. The Szegő condition is necessary for *Gordin's martingale method* (line 1103 correctly qualifies this), but not for the CLT itself. A process can satisfy the CLT with $\sqrt{n}$ normalization and Gaussian limit while having spectral density with zeros (violating Szegő). The "triple coincidence" rhetoric (line 1106) inflates a sufficient condition for one proof technique into a structural necessity.

**Sources:** Phase 1 (T5), cross-validated as CONTRADICTED

---

## Structural Findings (author's discretion)

### S1. Abstract and Introduction do not mention GPI/categorical framework

The abstract (line 52) describes the paper as "a unified treatment of the additive and multiplicative CLTs." It says nothing about the GPI category, σ-algebra lattice navigation, in-context RL, or the categorical framework — which now constitutes ~240 lines of Section 1. The Introduction (lines 59–69) similarly sets up expectations for a harmonic-analysis paper only.

**Sources:** Phase 3 (F1, F4)

### S2. Keywords and MSC codes omit GPI/category terms

Keywords (line 48) and subjclass (line 47) contain no category-theory, reinforcement-learning, or GPI terms. Missing: 18-XX (category theory), 68T05/90C40 (ML/MDP).

**Sources:** Phase 3 (F2, F3)

### S3. $\mathcal{F}$ overloaded — Fourier transform vs σ-algebra

Line 69: "$\mathcal{F}$ for the Fourier transform." Lines 77+: "$(\Omega, \mathcal{F}, P)$" for the probability space σ-algebra. The collision is never acknowledged. Context disambiguates, but the dual usage spans adjacent sections (Section 1 probability $\mathcal{F}$ through line 496; Fourier $\mathcal{F}$ from Section 5 onward).

**Sources:** Phase 5 (5a), Phase 4 (U1), Phase 3 (F5)

### S4. Transformer convergence conflates ideal vs parametric

Theorem 1.12 (Lévy upward) is correct for ideal conditional expectations. Remark 1.13 (line 490) says "convergence is guaranteed by Theorem 1.12(ii)" for the transformer's forward pass, but provides no approximation bound or conditions. The transformer computes a parametric approximation to $E[Y \mid \mathcal{G}_t]$ with bounded context, finite parameters, and approximate optimization. The theorem guarantees convergence of ideal projections, not of the approximation.

**Sources:** Phase 1 (T4), cross-validated UNRESOLVED

### S5. "Single phenomenon" without a general LCA CLT theorem

The paper's thesis is that the two CLTs are "instances of a single phenomenon." The structural evidence is strong (commutative diagrams, identical ODEs in frequency domain), but no single CLT theorem on a general LCA group is stated from which both CLTs follow. Proposition 6.5 (line 799) characterizes Gaussian measures as CLT limits but does not state convergence conditions. The two CLTs are proved separately and linked by log-isomorphism, not derived from a common ancestor.

**Sources:** Phase 1 (T2), cross-validated UNRESOLVED

### S6. Gaussian uniqueness: Introduction vs body characterization

The Introduction (line 65) characterizes the Gaussian as "the unique probability density that is a fixed point of the Fourier transform." The body (Definition 6.3, line 743) defines Gaussians via $\exp(-Q(\chi))$ Fourier transforms. These are logically compatible but never explicitly connected. On the circle group $\mathbb{T}$, the wrapped normal is NOT a Fourier fixed point, so the Introduction's claim does not generalize as stated.

**Sources:** Phase 1 (T1), cross-validated UNRESOLVED

### S7. F. and M. Riesz theorem invoked without citation — line 1009

Used in the Wold decomposition proof sketch to justify $\bigcap z^nH^2 = \{0\}$. No bibliographic reference given. The result is non-obvious and critical to the argument.

**Sources:** Phase 4 (U6)

### S8. Hardy space $H^2(\mathbb{R}_{>0})$ definition makes Theorem 7.2 tautological

Definition 7.1(b) (line 924) defines $H^2(\mathbb{R}_{>0})$ as the preimage of $H^2(\mathbb{R})$ under the log isomorphism. Theorem 7.2 then proves that log maps $H^2(\mathbb{R}_{>0})$ to $H^2(\mathbb{R})$ — which is immediate from the definition. The real content is the Mellin-analytic characterization, which is cited but not proved.

**Sources:** Phase 1 (T8)

---

## Cosmetic Findings

| Finding | Location | Source |
|---------|----------|--------|
| $G$ overloaded: group vs geometric mean $G(f)$ | line 1049 vs passim | Phase 5 (5a) |
| $\gamma$ overloaded: Gaussian measure vs RL discount factor | line 743 vs line 311 | Phase 5 (5a) |
| $Q$ overloaded: quadratic form vs probability measure | line 731 vs line 215 | Phase 5 (5a) |
| $\mathcal{E}$ vs $\mathcal{E}_Y$ inconsistent subscripting | line 284 vs line 268 | Phase 5 (5a) |
| Gioconda: "uniform probability measure" on possibly uncountable set | line 190 | Phase 1 (T11) |
| "Randomness is in the σ-algebra" — philosophical, not mathematical | line 203 | Phase 1 (T12) |
| IUT analogy — pattern-matching, explicitly hedged | line 1112 | Phase 1 (T6) |
| CNN equivariance ≠ σ-algebra invariance | line 338 | Phase 1 (T7) |
| $\rho$ double-duty near FPE (density vs representation) | line 1318 vs 1246 | Phase 3 (F8) |

---

## Symbolic Integrity

### 5a. Notation — 2 medium, 3 low issues
See S3 ($\mathcal{F}$ overloading) and C5 ($\mathcal{E}_Y$ vs endofunctor) above. Minor: $G$, $\gamma$, $Q$ overloading in non-adjacent sections. All five recently added symbols ($\mathsf{Proj}$, $R_Y$, $\mathcal{E}_Y$, $\mathbb{F}$, $\mathcal{R}_t$) are properly defined where introduced.

### 5b. References — clean
No dangling references. All 75 `\label` definitions resolve. 54 orphan labels (defined but never referenced) — low severity, useful as navigation anchors.

### 5c. Citations — perfect match
21 `\cite` keys, 21 `\bibitem` keys. Every cited key has a bibitem and vice versa.

### 5d. Dependencies — clean
No circular dependencies. Three forward references from Section 1 remarks to Sections 3–5 results — standard cross-referencing, not logical forward dependencies.

### 5e. Numbering — 2 fragile, 8 missing
Hard-coded "Sections~3–5" (line 1156) and "Sections~2–5" (line 1272) are currently correct but fragile. Sections 2–8, 10 lack `\label` tags, preventing `\cref`-based referencing.

---

## Locked Chain — Suggested Fix Order

1. **C1 + C2** (FPE/HJB sign): flip `+ε Ω` → `-ε Ω` on lines 1324, 1386
2. **C3** (phantom σ): replace `σ(ξ) = 4π²|ξ|²` with `Q(\chi)` on line 1286
3. **C4** (divergent C²): rewrite spectral gap bound with correct constant
4. **C5 + C6** (categorical precision): fix "endofunctor" → "functor" for $\mathcal{E}_Y$, qualify that GPI walk is monotone in residual but not necessarily a filtration, and state clearly that Theorem 1.12 applies to the filtration case (in-context RL)
5. **C7** (Szegő): soften "necessarily" → "generically" or restrict to the Gordin class
6. **S1–S2** (abstract/keywords): update to reflect GPI framework — author's call on timing
