# Self-Symbolic Consistency Check — GP-UCB Rewrite

**Date:** 2026-03-17
**Scope:** Rewrite of optimal-cycle.tex lines 250–335 (MPPI → GP-UCB / Stein-Variational iLQR), plus preamble changes in main.tex and 6 new bibliography entries.
**Central claim:** The MPPI sample-reweight loop is a special case of GP-UCB optimization with provable no-regret convergence, per-step safety, KL contraction, and poly-logarithmic scaling.

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 2 (0 reinforced, 1 unresolved, 1 contradicted) |
| STRUCTURAL tensions | 1 |
| Time-axis issues | 2 DRIFT, 5 HARMLESS |
| Unresolved confusions (fresh-eyes) | 12 |
| Symbolic issues | 2 must-fix, 2 should-fix, 2 advisory |

---

## Critical Findings (requires action)

### C1. KL Contraction Proposition is Contradicted (Prop 9.10 / `prop:kl-contract`)

**Severity:** LOAD-BEARING + CONTRADICTED

The proposition claims:
$$D_{\mathrm{KL}}(q_{n+1} \| \pi) \leq (1 - 2\alpha\eta) D_{\mathrm{KL}}(q_n \| \pi)$$
citing log-Sobolev inequality for the SE kernel via Ledoux.

**Problems found by cross-validation (Phase 2):**
1. **No log-Sobolev inequality exists in the document.** `heat-semigroup.tex` establishes spectral gap contraction $e^{-\lambda_1 t}$ of the Laplacian — this is NOT log-Sobolev.
2. **Category error.** Heat semigroup contraction applies to forward diffusion dynamics. GP posterior updating is Bayesian inference with a likelihood term. These are mathematically distinct: one is $\partial_t p = \frac{1}{2}\Delta p$, the other is $q_{n+1} \propto q_n \cdot \ell_n$.
3. **No observation noise model.** The proof sketch ignores $\sigma^2_{\mathrm{noise}}$ from domain randomization, which the domain-rand remark (line 548) says "widens posterior confidence bands."
4. **Undefined parameters.** $\alpha$ ("log-Sobolev constant of the kernel") and $\eta$ ("GP update step size") are not standard GP parameters and are never defined. A GP posterior update via Bayes' rule has no step size.
5. **$\pi$ undefined.** Called "the true cost landscape" but KL divergence requires a probability distribution. The Boltzmann definition $\pi(\beta) \propto \exp(-J(\beta)/\varepsilon)$ appears only 100 lines later in `rmk:svgd-ilqr`.

**Impact:** This proposition is cited by Prop 9.13 (`prop:unconditional`) as the bridge between outer (GP-UCB) and inner (Riccati) convergence. Without it, the "two-level contraction" narrative collapses.

**Recommendation:** Either (a) replace with a well-founded contraction result (e.g., GP posterior consistency from Ghosal/van der Vaart), or (b) weaken to a remark stating the contraction interpretation without a formal rate.

---

### C2. GP Model Assumption Unverified (lines 250–254)

**Severity:** LOAD-BEARING + UNRESOLVED

The assumption $J \sim \mathrm{GP}(0, k)$ with SE kernel has three vulnerabilities:

1. **Zero-mean unjustified.** No section in the volume justifies why the cost oscillates around zero.
2. **RKHS membership unverified.** Prop 9.8 (`prop:gp-regret`) assumes $\|J\|_k \leq B$ but this is never checked. `articulated.tex:281–283` shows $\sigma_k(t)$ is C$^\infty$ in $\beta$ (B-spline + sigmoid), but the smoothness of $\sigma_k(t)$ does not automatically propagate through the Riccati solve to $J(\beta)$.
3. **Contact transitions.** `hjb.tex:6–20` reveals barrier costs break group-theoretic smoothness, and `articulated.tex:517,744` shows time-varying $A(t), Q(t)$. The Riccati section assumes constant $A, Q$ (LQG regime).

**Impact:** All six guarantee propositions depend on this assumption. If $J \notin$ RKHS of SE kernel, the regret bound is vacuous.

**Recommendation:** Add a remark acknowledging this as a modeling assumption (standard in Bayesian optimization), not a theorem about the cost structure.

---

### C3. Holonomy-Regret Equivalence Unjustified (lines 286–290)

**Severity:** STRUCTURAL (does not affect propositions, but affects the central narrative)

The claim "$R_T > 0$ iff $H(f) > 0$ — the cycle has not closed" asserts an equivalence between optimization regret and spectral holonomy without:
- Identifying which spectral density $f$ corresponds to the GP-UCB problem
- Any proof, construction, or even a forward reference
- A formal map between the two frameworks

Similarly, the "Cycle connection" paragraph (lines 346–358) labels algorithm lines as log/Fourier/exp maps without mathematical content. These are evocative metaphors, not theorems.

---

### C4. Constraint Function `g` Undefined (Prop 9.9 / `prop:safe-gp`)

**Severity:** STRUCTURAL

Prop 9.9 states "Under Lipschitz continuity of the constraint function $g$, $g(\beta_n) \leq 0$ for all $n$" but `g` is never defined. The algorithm uses $c_{\max}$ as a threshold, and the safe set uses the LCB, but the relationship $g(\beta) = ?$ is never stated.

---

### C5. `q_n` Notation Collision — MUST FIX

**Severity:** Correctness / ambiguity

`q_n` is used for two unrelated objects in the same section:
- **GP posterior distribution** (Prop 9.10, line 396): "Let $q_n$ denote the GP posterior"
- **GP dictionary size** (Algorithm 1 line 8, Prop 9.12 line 441): "$q_n = \mathcal{O}((\log n)^{d+1})$"

One is a distribution, the other is an integer. They appear within a few pages of each other.

**Recommendation:** Rename dictionary size to $d_n$ or $m_n$.

---

### C6. Initial Safe Set `S_1` Never Specified

**Severity:** STRUCTURAL

Algorithm 1 requires `S_1` as input but it is never defined or discussed. The recursive update $S_{n+1}$ is given (line 336), but the initialization is missing.

---

### C7. Dimension `d` Never Defined

**Severity:** COSMETIC but pervasive

The dimension $d$ appears in regret bounds (lines 273, 283, 365, 441, 471) but is never defined. Presumably $d = \dim(\Theta)$, but $\Theta$ itself has no specified dimension.

---

## Structural Findings (author's discretion)

### S1. MPPI Narrative Split (DRIFT)

The rewrite says GP-UCB "replaces the MPPI sample-reweight loop" (line 298), but ~30 references to "MPPI" remain across `articulated.tex`, `chu-duality.tex`, `mppi.tex`, `riccati.tex`, `forward-only.tex`, `lie-group-intro.tex`, and the abstract. The 7-step algorithm in `articulated.tex` is still the MPPI-based loop. The two coexist without compilation error but the narrative is inconsistent.

### S2. Symbol Overloading

| Symbol | Meanings | Locations |
|--------|----------|-----------|
| `k` | GP kernel, Riccati feedforward gain, foot index, Fourier index | lines 254, 323, 494, 527, 18 |
| `σ` | Contact schedule $\sigma_k(t)$, GP std dev $\sigma_{n-1}(\beta)$, noise $\sigma^2_{\mathrm{noise}}$ | lines 321, 260, 548 |
| `β` / `β̄_n` | Gait parameter, UCB exploration coefficient | lines 266, 260 |
| `r_k` | Autocovariance values (Def 9.3), foot positions (GDD remark) | lines 59, 527 |

All are context-disambiguated but the density is high in the algorithm section.

### S3. `\KL` vs `\mathrm{KL}` Inconsistency

Lines 231, 237, 247 (pre-rewrite, Prop 9.7) use `\mathrm{KL}`. Lines 400, 401, 469 (rewrite) use the new `\KL` macro. Both render identically but source is inconsistent.

### S4. `O(...)` vs `\cO(...)` Inconsistency

Pre-rewrite (lines 111, 157, 163) uses bare `O(...)`. Post-rewrite uses `\cO(...)`. Paper-wide stylistic split at line ~250.

---

## Cosmetic Findings

- **`\diag` macro declared but never used** in any .tex file (main.tex line 75)
- **`|\Theta|` in GP-UCB exploration coefficient** (line 265): Srinivas et al. use this for a finite discretization, but $\Theta$ is introduced as a continuous parameter space. Standard in the BO literature (applies to the discretized version) but could confuse readers.
- **OMD-to-GP-UCB transition** (line 296): motivation is thin. Lines 287–290 give the rationale (sharper rate) but "replaces" is stronger than what is justified.

---

## Symbolic Integrity

### References: CLEAN
All 15 labels defined, all `\cref` targets resolve, no dangling references. `\cref{sec:riccati}` verified in `riccati.tex:1`.

### Citations: CLEAN
All 6 new `\cite` keys present in `bibliography.tex`. No old citations removed.

### Colors: CLEAN
All 4 semantic colors (AcqColor, PostColor, ConColor, CycleColor) used consistently with their intended roles.

### Theorem Counter: CLEAN
Propositions 9.8–9.13 follow 9.7 correctly. Algorithm 1 uses separate counter. No downstream breakage (Section 10+ uses `[section]` reset).

### Compilation: CLEAN
Zero undefined references, zero label warnings after 3 passes. 96 pages.

---

## Action Priority

| Priority | Item | Action |
|----------|------|--------|
| 1 | C1: KL contraction | Rewrite or downgrade to remark |
| 2 | C5: `q_n` collision | Rename dictionary size |
| 3 | C2: GP assumption | Add modeling-assumption remark |
| 4 | C4: `g` undefined | Define constraint function |
| 5 | C6: `S_1` unspecified | Add initialization note |
| 6 | C3: Holonomy-regret | Flag as conjecture or add proof |
| 7 | S1: MPPI narrative | Reconcile across volume (future) |
| 8 | S3–S4: Macro consistency | Unify `\KL`/`\cO` usage |
