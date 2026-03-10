# Self-Symbolic Consistency Check — `clt-duality-note.tex`

**Date:** 2026-03-10
**Document:** `independent_volume/add_mult_clt/clt-duality-note.tex` (929 lines)
**Central claim:** The additive and multiplicative CLTs are dual via Fourier–Mellin on LCA groups; Hardy spaces + Szegő Limit Theorems provide non-trivial cross-theater volume comparison, contrasting with Mochizuki's trivializing indeterminacies.

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 3 (0 reinforced, 2 unresolved, **1 contradicted**) |
| STRUCTURAL tensions | 4 |
| COSMETIC tensions | 2 |
| Time-axis issues | N/A (file untracked, no git baseline) |
| Unresolved confusions (fresh-eyes) | 10 |
| Symbolic issues | 4 (notation: 1, references: 36 orphans, citations: 2 uncited, dependencies: 1 forward ref) |

---

## Critical Findings (requires action)

### C1. **CLT does NOT force E(f) < ∞** — LOAD-BEARING, CONTRADICTED

**Location:** Lines 677, 691

**Claim (line 677):** "any process converging to the Gaussian limit automatically satisfies both the Szegő condition and the regularity condition ∑k|c_k|² < ∞, ensuring all cross-theater comparisons yield finite, nonzero bounds."

**Claim (line 691):** "The central limit theorem, being absent from the IUT framework, is precisely the missing tool: it provides the universal Gaussian attractor that constrains inter-theater coupling to the non-trivializing regime."

**The contradiction:** The paper's own Theorem 8.8 (line 633) explicitly states that the Strong Szegő Theorem requires the *additional* hypothesis ∑|k|·|c_k|² < ∞. The CLT (via Gordin's condition, cited at line 598) requires only the Szegő condition ∫log f > −∞, which is strictly weaker. The paper's technical apparatus shows these are different conditions:

- **Szegő condition** (∫log f > −∞) → pure non-determinism, G(f) ∈ (0,∞) ✓
- **Strong Szegő regularity** (∑k|c_k|² < ∞) → E(f) < ∞ ✓
- **CLT (Gordin)** → Szegő condition ✓, but **⇏** Strong Szegő regularity ✗

A stationary process can satisfy a CLT while having log f too rough for ∑k|c_k|² < ∞. The logical hinge connecting "CLT → non-trivial multiverse" is broken.

**Impact:** This is the single most dangerous point. If CLT convergence does not force E(f) < ∞, the entire "non-trivial multiverse" narrative (the firepower point against Mochizuki) rests on a false implication.

**Possible fix directions (not prescriptive):**
- Restrict the claim to i.i.d. or short-range-dependent processes where E(f) = 1 or finite
- Replace "CLT forces" with "the Gaussian fixed point (i.i.d. case) satisfies E(f) = 1, and perturbations in a neighborhood inherit E(f) < ∞ by continuity"
- Introduce the regularity condition as a separate requirement and argue it is "natural" rather than automatic

---

### C2. **Szegő asymptotics transport from 𝕋 to ℝ₊ not proved** — LOAD-BEARING, UNRESOLVED

**Location:** Line 665 (Corollary 8.9(iii))

**Claim:** "Via Fourier–Mellin duality (Theorem 8.4), this comparison transports to the multiplicative group: the Mellin-side Toeplitz determinant on H²(ℝ₊) satisfies the same asymptotics with the same Szegő constant."

**The gap:** Theorem 8.8 (Szegő) is stated and proved for **𝕋** (compact, discrete spectrum). Theorem 8.4 (Hardy duality) connects **ℝ₊ ↔ ℝ** (non-compact). The passage from 𝕋 to ℝ (or ℝ₊) requires either:
- A conformal map (Cayley transform) that changes operator-theoretic structure nontrivially, or
- A separate Szegő-type theorem for Wiener–Hopf operators on ℝ

Neither is provided. The paper bridges ℝ₊ ↔ ℝ but not 𝕋 ↔ ℝ.

**Impact:** The quantitative content of the "non-trivial multiverse" (E(f) ∈ (0,∞)) is stated for 𝕋 but claimed for ℝ₊ without justification.

---

### C3. **IUT analogy has no formal content** — LOAD-BEARING, UNRESOLVED

**Location:** Lines 680–692 (Remark on non-trivial vs trivial multiverses)

**Claim:** Mochizuki's Ind 3 "corresponds in our framework to allowing f to vary without the constraint ∑k|c_k|² < ∞." The CLT is "precisely the missing tool."

**The gap:** No formal map is constructed between IUT objects (Hodge theaters, log-shells, theta-pilot objects) and the Szegő/Toeplitz framework. The correspondence is purely verbal. IUT operates on arithmetic objects (number fields, p-adic Hodge theaters); this paper is purely analytic (LCA groups, L² spectral theory). The Scholze–Stix objection concerns ring-structure identification across theaters, which has no analogue in the spectral-density setting.

**Impact:** This is interpretive rather than mathematical. As currently written, it presents an analogy with the rhetorical force of a theorem. The paper should either formalize the correspondence or explicitly mark it as heuristic/programmatic.

---

## Structural Findings (author's discretion)

### S1. "Szegő condition is necessary for the CLT" — overstated (line 674)

The Szegő condition is necessary for the CLT *via Gordin's martingale method* with standard √n normalization and Gaussian limit. CLTs exist for certain long-range-dependent processes violating this condition (with non-Gaussian limits or non-standard normalization). The "triple coincidence" remark weakens if the Szegő condition is not truly necessary for all CLT-type results.

### S2. "Connected LCA group with Lie algebra" — not all connected LCA groups are Lie (line 386)

Connected LCA groups include solenoids (connected but not Lie). The paper implicitly assumes G is a Lie group. Since only three examples (ℝ, ℝ₊, 𝕋) are used, the theorems are correct, but the generality framing is overstated.

### S3. Wold/prediction transport from 𝕋 to ℝ₊ incomplete (line 600)

The Wold decomposition is for a single isometry (discrete time, H²(𝕋)). On H²(ℝ), the shift is a continuous semigroup, not a single isometry. The transport claim "the entire prediction-theoretic structure transports to (ℝ₊,×)" passes through two different isomorphisms only one of which (ℝ↔ℝ₊) is established.

### S4. Mellin-Toeplitz winding number (line 612)

The claim that "log preserves winding numbers" is correct for loops on compact T but needs compactification machinery for functions on ℝ/ℝ₊ (Wiener–Hopf setting). Stated in a remark, not a theorem.

---

## Cosmetic Findings

### K1. Introduction says "unique fixed point" of Fourier transform (line 64)

The body (Remark 5.5, line 364) correctly notes eigenvalues {1,−1,i,−i} with infinite-dimensional eigenspaces. The Gaussian is the unique *Gaussian* fixed point, not the unique fixed point. The introduction overstates.

### K2. H²(G)⊥ definition (line 516)

The notation χ ≥ 0 on a general dual Ĝ uses an ordering that is introduced informally (line 508) but never axiomatized. Fine for the three examples, but the phrasing suggests false generality.

---

## Fresh-Eyes Confusions (Phase 4)

### Unresolved (10)

| ID | Lines | Issue |
|----|-------|-------|
| U1 | 857, 917 | Bibliography entries `Grenander` and `Terras` never cited |
| U2 | 516 | Ordering χ ≥ 0 on Ĝ informally mentioned but never defined for general LCA |
| U3 | 711–712 | ker(S*) column shows "---" for ℝ and ℝ₊ without explanation; text (line 684) claims dim ker S* = 1 |
| U4 | 698 | g_V, V, g_S (Lyapunov conformal metric) appear without definition anywhere |
| U5 | 699 | "horizon redshift" — undefined metaphor from cosmology, no reference |
| U6 | 694–702 | Viability theory remark: viability kernel, differential inclusions never defined, no citation (Aubin etc.) |
| U7 | 711–712 | C₀ (continuous functions vanishing at ∞) used in summary table without definition |
| U8 | 372–378 | Proposition 5.4: "appropriate tightness and variance conditions" — deliberately vague hypotheses |
| U9 | 689–692 | IUT analogy presented with mathematical force ("correspond in our framework") but no formal correspondence |
| U10 | 758 | Hat notation $\widehat{(\cdot)} : ℝ³ → \mathfrak{so}(3)$ collides with Fourier/dual hat used throughout |

### Resolved (13)

Standard confusions that the document resolves internally (𝕋 dual definition, Plancherel vs probability convention, eigenfunction vs fixed point, "outer function" terminology, etc.).

---

## Symbolic Integrity (Phase 5)

### 5a. Notation

| Symbol | Overloading | Severity |
|--------|------------|----------|
| μ | probability measure (§1–4) vs scalar mean (§5, §7) | MEDIUM — same section sometimes |
| D | Euler operator (§3) vs Toeplitz determinant D_n(f) (§8) | LOW — subscripted differently |
| E | Expectation E[·] vs Szegő constant E(f) | LOW — argument syntax differs |
| G | Group vs geometric mean G(f) | LOW |
| S | Partial sums vs unilateral shift vs dilation | LOW |

**Missing operator:** `E` (expectation) used throughout but never declared as `\DeclareMathOperator` (unlike `\Var` and `\tr`).

### 5b. Reference Integrity

- **Dangling references: 0** (all \cref/\ref targets resolve)
- **Orphan labels: 36** (defined but never \cref'd — including `thm:pontryagin`, `thm:birkhoff`, most equation labels)

### 5c. Citation Integrity

- **Missing bibliography entries: 0** (all \cite keys resolve)
- **Uncited bibliography entries: 2** — `Grenander` (line 857), `Terras` (line 917)

### 5d. Theorem Dependencies

- **Circular dependencies: 0** (graph is a clean DAG)
- **Forward references: 1** — `rmk:gaussian-dual` (line 145) → `thm:gaussian-fixed` (line 342)
- **Missing dependencies: 0**

### 5e. Color/Style

Not applicable (no semantic colors used).

---

## Prioritized Action Items

| Priority | ID | Action |
|----------|----|--------|
| **P0** | C1 | Fix the false implication "CLT → E(f) < ∞". This is the load-bearing contradiction. |
| **P1** | C2 | Either prove the 𝕋→ℝ₊ transport (cite Wiener–Hopf Szegő analogues) or weaken the claim |
| **P1** | C3 | Mark the IUT analogy explicitly as heuristic/programmatic, or remove "correspond in our framework" |
| **P2** | U4,U5,U6 | Define or remove undefined terms in viability remark (g_V, g_S, "horizon redshift") |
| **P2** | U3 | Explain the "---" entries in the summary table for ker(S*) on non-compact groups |
| **P3** | U1 | Remove or cite `Grenander` and `Terras` |
| **P3** | U7 | Define C₀ |
| **P3** | S1,S2 | Qualify overstated generality claims |
