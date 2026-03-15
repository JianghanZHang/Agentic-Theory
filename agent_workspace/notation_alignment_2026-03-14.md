# Notation Alignment Report: Optimal Cycle Theory

**Date:** 2026-03-14

---

## Collision Severity Classification

Collisions are rated by **proximity** (how close the two meanings appear in the document) and **confusability** (how likely a reader is to mix them up).

- **CRITICAL**: Two meanings in the *same section* or *adjacent sections*, high confusability
- **MODERATE**: Two meanings in *different parts* of the paper, some confusability
- **BENIGN**: Two meanings separated by many sections, universally disambiguated by context

---

## CRITICAL Collisions (same section or adjacent)

### 1. `G` = LCA/Lie group vs `G(f)` = geometric mean

**Sections affected:** optimal-cycle.tex, hardy-spaces.tex, introduction.tex

In `optimal-cycle.tex`, the feasible set is `\Omega_t \subset \Omega` (a space of functions on group `G`), and in the *same paragraph* `G(f) = e^{c_0}` denotes the geometric mean. The paper writes `G(f)^n` (geometric mean raised to power n) right next to discussion of groups `G`. In `hardy-spaces.tex`, the Hardy space is defined on group `G`, and `G(f)` appears in the Szego theorems on the same page.

**Resolution:** Rename the geometric mean. Suggested: `\mathfrak{G}(f)` or `\mathrm{GM}(f)`.
**Alternative:** This is actually standard Szego notation (`G(f)` for the geometric mean is universal in Toeplitz determinant theory). Add a disambiguation remark at first use.

### 2. `\Omega` = sample space vs `\Omega` = Casimir operator vs `\Omega` = feasible set

**Sections affected:**
- `foundations.tex` (sample space, ~50 occurrences)
- `optimal-cycle.tex` (feasible set `\Omega`, `\Omega_t`)
- `spectral-decomp.tex`, `hjb.tex`, `mppi.tex` (Casimir operator)

The Casimir operator `\Omega` and the feasible set `\Omega` are separated by 3 sections, but both are central objects. The sample space `\Omega` is in Section 1 only.

**Resolution options:**
- (a) Rename feasible set: `\mathscr{D}` (for "densities") or `\mathscr{S}` (for "spectral")
- (b) Rename Casimir: `\Delta_G` or `\mathbf{\Delta}` (common alternative in differential geometry)
- (c) Accept — the three uses are never in the same section

**Recommended:** Option (a). The feasible set appears only in `optimal-cycle.tex` and is the easiest to rename without disrupting standard notation. The Casimir as `\Omega` is standard in representation theory. The sample space `\Omega` is standard in probability.

### 3. `\rho` = irreducible representation vs `\rho_t` = density

**Sections affected:** `spectral-decomp.tex` (BOTH meanings in the same file)

The paper acknowledges this at `spectral-decomp.tex:134`: "writing `\pi` for irreducible representations to free `\rho` for the density." This is a local fix within the Fokker-Planck remark, but elsewhere in the same file, `\rho` still means representation (lines 55-101).

**Resolution:** Already partially handled. Consistent within the file.

### 4. `V` = value function vs `V_\rho` = representation space

**Sections affected:** `hjb.tex` (BOTH meanings in same section!)

Line 10: "the value function `V \in C^\infty(G)`"
Line 3: "each irreducible `V_\rho`"

A reader sees `V` for both the value function and the carrier space of a representation *in the same remark*.

**Resolution:** This is actually standard — `V_\rho` always has a subscript `\rho`, and `V` alone always means the value function. The subscript disambiguates. **Benign in practice.**

### 5. `H` = holonomy vs `H` = Hamiltonian vs `H(x)` = bathymetry

**Sections affected:** `mppi.tex` has `H(\nabla V)` (Hamiltonian, line 64) and `H(x)` (bathymetry, line 73), while `concluding.tex` has `H(f)` (holonomy).

Three meanings of `H` within 20 lines of `mppi.tex`.

**Resolution:** The Hamiltonian and bathymetry uses are within self-contained remarks and clearly contextual. The holonomy `H(f)` always takes argument `f`. **Acceptable but worth noting.**

### 6. `g` = group element vs `g(q)` = gravity vector

**Sections affected:** `articulated.tex`

Line 6: "$Q = SE(3) \times \bT^n$" (configuration space, group element is `g`)
Line 73: "$\tau = M(q)\ddot{q} + C(q,\dot{q})\dot{q} + g(q)$" (gravity vector)
Line 78: "`g(q)` is the gravity vector"

A reader parsing the EOM sees `g(q)` and might momentarily think "group element evaluated at `q`."

**Resolution:** Standard robotics notation. Disambiguated by subscript/argument. **Acceptable but flagged.**

### 7. `\cM` = Mellin transform vs `\cM_i` = spatial inertia

**Sections affected:** Part I uses `\cM` for Mellin; Part II `articulated.tex` uses `\cM_i` for inertia.

Separated by multiple sections. The Mellin transform `\cM[\mu](s)` always takes a functional argument; the inertia `\cM_i` always has a body index subscript.

**Resolution:** Disambiguated by usage pattern. **Moderate — no action needed** unless the reader jumps between parts.

### 8. `\lambda` = Casimir eigenvalue vs temperature vs contact force

**Sections affected:**
- `spectral-decomp.tex`, `hjb.tex`: `\lambda_\rho` (Casimir eigenvalue), `\lambda_1` (spectral gap)
- `mppi.tex:24`: `\lambda = 2\varepsilon` (temperature parameter)
- `articulated.tex:111`: `\lambda_k` (contact forces)

The temperature use in `mppi.tex` is particularly dangerous — it appears once, is set equal to `2\varepsilon`, and is never used again. It could be inlined.

**Resolution:** Remove `\lambda = 2\varepsilon` from `mppi.tex` — just write `2\varepsilon` directly. The contact force `\lambda_k` is standard Lagrange multiplier notation and always subscripted.

### 9. `R` and `\Sigma` undefined in `mppi.tex:24`

**Issue:** The line "Setting `\lambda = 2\varepsilon` so that `\lambda R^{-1} = \Sigma`" introduces `R` (control cost matrix) and `\Sigma` (noise covariance) without definition. These are defined only in `riccati.tex:22-25`, five sections later.

**Resolution:** Either define `R` and `\Sigma` inline, or delete this clause entirely — it is a parenthetical that adds nothing to the Hopf-Cole derivation and introduces undefined symbols.

---

## MODERATE Collisions (different parts, some ambiguity)

| Symbol | Meaning 1 | Where | Meaning 2 | Where | Risk |
|--------|-----------|-------|-----------|-------|------|
| `\cF` | Fourier transform | intro, fourier-mellin | σ-algebra | foundations | Low — different typeface contexts |
| `\varepsilon` | Residual `Y - E[Y\|G]` | foundations:159 | Diffusion coefficient | Part II | Low — Part I only uses it once |
| `\gamma` | Discount factor | foundations:243 | Gaussian measure | gaussian-measures | Low — different sections entirely |
| `\mathcal{H}` | Sub-σ-algebra | foundations:111 | Hilbert space (Wold) | hardy-spaces:93 | Low — standard dual usage |
| `A` | Additive group `(R,+)` | introduction | State matrix | riccati | Low — completely different contexts |
| `\mu` | Prob. measure | lca-groups | Spatial momentum | articulated | Low — Part I vs Part II |
| `\xi` | Frequency variable | Part I | Gaussian noise | forward-only | Low — standard in each context |
| `q` | State cost / Dirichlet modulus / quaternion / gen. coords | various | — | — | Moderate — 4 meanings, but always in distinct sections |

---

## BENIGN (no action needed)

| Symbol | Meanings | Verdict |
|--------|----------|---------|
| `\chi` | LCA character / Dirichlet character / representation character | All are "characters" — same concept at different generality levels |
| `\sigma^2` / `\sigma` | Variance / convergence parameter / prediction error | Always subscripted or contextualized |
| `\theta` | Rotation angle / joint angle / circle variable | Universal convention |
| `n` | Number of joints / index variable | Standard |
| `m` | Various indices | Standard |

---

## Undefined Symbols (used without introduction)

| Symbol | File | Issue |
|--------|------|-------|
| `R`, `\Sigma` | mppi.tex:24 | Control cost matrix and noise covariance — undefined |
| `\mathrm{Ad}`, `\mathrm{Ad}^*` | articulated.tex | Adjoint/coadjoint representation — used extensively but never formally defined. Introduced as "the adjoint representation" without definition of what Ad_g does |
| `\mathrm{ad}^*` | articulated.tex:47 | Coadjoint action — used without definition |
| `\mathrm{Sym}^+` | articulated.tex:40 | Positive-definite symmetric operators — notation not introduced |
| `D_n(f)` | introduction.tex:17, optimal-cycle.tex:36 | Toeplitz determinant — used before formal definition in hardy-spaces.tex:140 |
| `\mathbb{FL}` | articulated.tex:150 | Legendre transform — symbol introduced inline but unusual notation |
| `\hat{n}_k` | articulated.tex:114 | Contact normal — used without definition |

---

## Silent Convention Changes

| Convention | Section 8 (heat-semigroup) | Section 12 (spectral-decomp) | Issue |
|-----------|---------------------------|------------------------------|-------|
| Heat equation | $\partial_t p = \frac{1}{2}\Delta_G p$ | $\partial_t u = -\Omega u = \Delta_G u$ | Factor of $\frac{1}{2}$ disappears |
| Sobolev seminorm | — | — | $H(f) = \sum_{k=1}^{\infty} k\|c_k\|^2$ called "$H^{1/2}$ seminorm" but is half the standard definition |

---

## Recommended Actions (prioritized)

### Tier 1: Fix (threatens reader comprehension)

1. **Remove `\lambda = 2\varepsilon` and `\lambda R^{-1} = \Sigma` from `mppi.tex:24`.** Just write $2\varepsilon$ directly. This eliminates three undefined/overloaded symbols in one edit.

2. **Add forward-reference for `D_n(f)`.** At first use in `introduction.tex:17`, add "(the Toeplitz determinant, defined in \S\ref{sec:hardy})".

3. **Reconcile the $\frac{1}{2}$ convention.** Either add a remark at `spectral-decomp.tex:97` noting the convention change, or normalize both to the same convention.

4. **Fix the Sobolev seminorm claim.** At `optimal-cycle.tex:29`, change to "$\frac{1}{2}$ times the $H^{1/2}(\mathbb{T})$ Sobolev seminorm" or define the one-sided convention explicitly.

### Tier 2: Clarify (improves precision)

5. **Add a notation remark** at the start of Part II (`lie-group-intro.tex`) noting that `\cM` shifts from Mellin transform to spatial inertia, and that `\Omega` shifts from feasible set to Casimir operator.

6. **Define `\mathrm{Ad}`, `\mathrm{Ad}^*`, `\mathrm{ad}^*`** at first use in `articulated.tex` or add a forward reference to their definition in `spectral-decomp.tex`.

### Tier 3: Accept (standard notation, context disambiguates)

7. `G` / `G(f)` — standard Szego notation. Accept.
8. `\rho` dual usage — already handled with the `\pi` switch.
9. `V` / `V_\rho` — subscript disambiguates.
10. `g` / `g(q)` — standard robotics convention.
