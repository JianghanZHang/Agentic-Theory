# Self-Symbolic Consistency Check: catching.tex

**Date:** 2026-03-09
**Target:** `appendices/catching.tex` (new chapter) + integration with main thesis

## Summary

- LOAD-BEARING tensions: 2 (0 reinforced, 2 unresolved, 0 contradicted)
- STRUCTURAL tensions: 3
- COSMETIC tensions: 1
- Time-axis issues: 1 DRIFT, 1 BREAKING (commit pairing), 6 HARMLESS
- Unresolved confusions: 3
- Symbolic issues: 4 (notation: 2, reference: 0, citation: 1, dependency: 0, style: 0)

---

## Critical Findings (requires action)

### C1. LOAD-BEARING: The spectral gap claim $\lambda_1(P_2) = 0$ is mathematically wrong

**Location:** `catching.tex` lines 399-403, 447-461

**Claim:** Before gripper closure, the contact graph is a path $P_2$ with $\lambda_1 = 0$. After closure, it becomes cycle $C_3$ with $\lambda_1 = 3 > 0$. The transition $\lambda_1: 0 \to \epsilon$ is the core topological event.

**Problem:** The path graph on 3 vertices ($C_L - \mathrm{obj} - C_R$) is *connected*. Its Laplacian eigenvalues are $\{0, 1, 3\}$, so $\lambda_1 = 1 > 0$ — not zero. The claimed transition $\lambda_1: 0 \to \epsilon$ does not occur on the standard graph Laplacian because $\lambda_1$ is already positive before closure.

**Why it matters:** The entire capture theorem (Thm c-capture) rests on this transition being the spectral kick. If $\lambda_1 > 0$ already holds pre-closure, then gripper closure is not the topological event the framework requires.

**Fix direction:** The physical argument is correct — the open path allows escape, the closed cycle does not. The mathematical formalization needs to use a different operator or graph model. Options:
- Model the pre-closure graph as *disconnected* (2 components: chopstick-pair vs. object with only friction, not rigid contact) until the gripper bang creates rigid closure
- Use directional escape analysis (Cheeger constant of the boundary) instead of the Fiedler eigenvalue
- Frame the transition as $\lambda_1: \text{small} \to \text{large}$ ($1 \to 3$, tripling) rather than $0 \to \epsilon$

**Also:** The notation $P_2$ should be $P_3$ (standard graph theory: subscript = vertex count).

### C2. LOAD-BEARING: Mass invariance breaks at contact

**Location:** `catching.tex` lines 185-201, 266, 432-439

**Claim:** The catching controller $\pi$ is invariant under mass rescaling $m \to \alpha m$.

**Problem:** The trapping condition $v < d\sqrt{K/m}$ depends on $m$. The viability window $\Delta t_{\mathrm{viable}} = L/v_\perp \cdot e^{D\Delta t/m}$ depends on $m$. The text partitions this into "hardware" vs. "software" — but the system's success conditions depend on mass. The controller is mass-invariant only if the hardware is pre-matched to the mass range, which means the overall system is not mass-invariant in an operationally meaningful sense.

**Why it matters:** The equivalence principle is presented as the bridge from Newtonian physics to framework universality. If success conditions depend on mass, the universality claim weakens.

**Fix direction:** Strengthen the theorem statement to specify its scope: "the control *policy* $\pi$ (software) is mass-invariant; the end-effector *design* (hardware) must satisfy $K > mv_\perp^2/d^2$." This is honest and still powerful — it means the same policy catches tennis balls and bowling balls, you just need stiffer springs for the latter.

### C3. UNRESOLVED: $\Delta t_{\mathrm{absorb}}$ is never defined

**Location:** `catching.tex` lines 432, 439, 511

Used three times in proofs and theorem statements but never formally defined. Its meaning (time between object entering the well and start of gripper closure) must be inferred.

---

## Structural Findings (author's discretion)

### S1. Kakeya duality stated as exact but is only approximate

**Location:** `catching.tex` lines 587-609

The theorem states $\mathcal{C} = \mathcal{T} \circ \mathcal{M}$ as equality, but the proof immediately concedes this is approximate when $D > 0$ (the only physical case). No error bound given. Consider: state the theorem with the caveat, or restrict to the conservative case.

### S2. Three-term decomposition proof is argument-by-analogy

**Location:** `catching.tex` lines 516-529

Invokes Pontryagin without specifying cost functional, dynamics, or costate system. Delegates to `thm:3b-damper` by structural isomorphism. Valid as a sketch; not self-contained as a proof.

### S3. Cross-references are stretched (4 of 5)

| Reference | Verdict | Issue |
|-----------|---------|-------|
| `thm:lifecycle` | STRETCHED | Catching uses kinematics for non-persistence; theorem uses cost divergence. "Voluntary relinquish" doesn't apply to a passive projectile. |
| `lem:forcing` | STRETCHED | Thrown object's deadline comes from kinematics, not from the lemma's cost-divergence mechanism. Used in a remark, so low impact. |
| `thm:massgap` | STRETCHED | Claims theorem says $\lambda_1$ is edge-weight-invariant; it actually says $\lambda_1 > 0$ iff connected. The mass-invariance and spectral-gap are unrelated mathematical facts. |
| `thm:3b-damper` | CONSISTENT | Genuine structural parallel (drift + singular + bang). |
| `sec:manipulation` | STRETCHED | "Pre-sword" label for stationary object contradicts framework definition ($U_r = \varnothing$ for stationary objects). Phase-count mismatch (5 vs 3) suppressed. |

### S4. $T_xM$ vs $TM$ notation inconsistency

Introduction uses $T_xM$ (tangent space at a point); Theorem c-equivalence uses $TM$ (tangent bundle). These are different mathematical objects.

### S5. `K` overloaded

Spring stiffness in catching.tex vs. viability kernel throughout the rest of the thesis. Unambiguous in context but creates friction for cross-chapter readers.

---

## Cosmetic Findings

- **10% ratio universality claim** (Remark, lines 563-574): Codimension-1 argument does not yield 10% — it yields measure zero. The 10% is a hardware coincidence.
- **Zero citations:** Chapter cites no bibliography entries despite discussing Newton, Galileo, Cheeger, Pontryagin, MuJoCo. Relevant `\bibitem`s exist.
- **4 orphan labels:** `sec:catching`, `thm:c-kakeya`, `def:c-viability-window`, `prop:c-lifecycle` — defined but never `\cref`'d.
- **`\mathrm{Reach}(\kappa)`** vs. `\mathrm{Reach}(x, U_r, T)` — argument convention differs from framework.

## Symbolic Integrity

| Check | Status |
|-------|--------|
| 5a. Notation | 2 issues (`K` overload, `P_2`/`P_3` naming) |
| 5b. References | CLEAN — all 5 external + all internal refs resolve |
| 5c. Citations | 0 citations in chapter; relevant bibentries uncited |
| 5d. Dependencies | CLEAN — no circular deps, no forward refs |
| 5e. Colors | CLEAN — all 4 semantic colors used correctly |

## Build Status

- Compiles cleanly with `latexmk -xelatex`
- 214 pages, zero undefined references
- Both `main.tex` and `catching.tex` must be committed together (TikZ `coil` decoration requires `decorations.pathmorphing`)
