# Self-Symbolic Consistency Check — Post-Fix Verification

**Date:** 2026-03-17
**Scope:** Verification after fixing all 8 issues from the prior consistency check (C1–C3, S1–S3, C1b, C1c).
**Central claim:** The optimal cycle carries holonomy H(f) vanishing iff Gaussian; Part II applies this via GP-LCB gait optimization with provable guarantees.

---

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 5 (4 reinforced, 1 unresolved, 0 contradicted) |
| STRUCTURAL tensions | 4 |
| Time-axis issues | 7 (0 BREAKING, 3 DRIFT, 4 HARMLESS) |
| Unresolved confusions (Phase 4) | 2 |
| Symbolic issues | 2 actionable (1 HIGH line ref, 1 MEDIUM naming) + 4 uncited bib entries |

---

## Critical Findings (requires action)

### C1. Per-Iteration Holonomy Decrease Claim Unsupported

**Severity:** LOAD-BEARING + UNRESOLVED

**Passage** (articulated.tex:1191–1193):
```
Each outer iteration decreases $H(f)$
(\cref{prop:student-convergence}): the re-cycle converges
to the cycle.
```

**Problem:** `prop:student-convergence` (optimal-cycle.tex:149–168) proves that H(f_{t_ν}) = O(log ν / ν) → 0 as ν → ∞ for the Student t family. It does NOT prove that each GP-LCB iteration of Algorithm 2 or 3 decreases H(f). The missing link — "each GP-LCB iteration increases the effective ν" — is never formally stated. The lie-group-intro.tex:9 analogy ("the barrier parameter ε corresponds to the effective ν") is interpretive, not a theorem.

**Impact:** The claim that "the re-cycle converges to the cycle" (i.e., H(f) → 0 through iteration) is central to the paper's thesis but rests on an unsupported citation.

---

### C2. Algorithm 3 Line Reference Off by 2

**Severity:** HIGH (symbolic)

**Passage** (articulated.tex:173):
```
In the cost functional (\cref{alg:quadruped}, line~13),
$h_k$ is regularized to $h_k + \varepsilon$
```

**Problem:** In Algorithm 3 (`alg:quadruped`), line 13 is `\EndFor` (end of inner t-loop). The cost functional J_n containing the h_k barrier term is at **line 15**. The two `\EndFor` statements at lines 13–14 push the cost computation down.

---

## Structural Findings (author's discretion)

### S1. Cross-Reference Error in lie-group-intro.tex

**Passage** (lie-group-intro.tex:9):
```
the barrier parameter $\varepsilon$ corresponds to the effective
$\nu$ of the exploration distribution (\cref{rmk:mpc}).
```

**Problem:** `rmk:mpc` (optimal-cycle.tex:578–602) discusses MPC state and Lyapunov stability but never mentions Student t distributions, effective ν, or the ε–ν correspondence. The correct reference is `rmk:dual-ascent` (optimal-cycle.tex:186–223), which describes the ε-annealing schedule.

### S2. "MPPI Estimator" in forward-only.tex

**Passage** (forward-only.tex:5):
```
Consider the MPPI estimator for the controlled diffusion
on a Lie group~$G$
```

**Problem:** The MPPI → re-cycle terminology update touched riccati.tex and chu-duality.tex but not forward-only.tex. The proposition still says "MPPI estimator" while the rest of the paper has shifted to "re-cycle" framing. This is the method's proper name (technically correct) but creates narrative drift.

### S3. Equation Label `eq:gp-ucb` Names a LCB Formula

**Passage** (optimal-cycle.tex:261–267):
```
The GP-UCB acquisition function
\[
  \ell_n(\beta) = \mu_{n-1}(\beta) -
  \sqrt{\bar\beta_n}\;\sigma_{n-1}(\beta)
\]
\label{eq:gp-ucb}
```

**Problem:** The label `eq:gp-ucb` and the prose "GP-UCB acquisition function" name this formula as UCB, but the formula itself is μ − √β̄σ, a Lower Confidence Bound. The algorithm annotation at line 369 correctly says "(GP-LCB)". The document does explain both terms (GP-UCB for the method name, GP-LCB for the cost-minimization formula), so this is not broken — but the label is misleading.

### S4. Fano Triad Summary Understates New Content

**Passage** (chu-duality.tex:574–576):
```
Triad~T1 is the contact Jacobian constructed in detail below;
the remaining six triads are identified by their physical content
but their full Chu tensor-product verification is deferred.
```

**Problem:** T1, T2, and T6 are now fully proved (thm:fano-triads), and T3–T5, T7 have sketched constructions with identified key identities. The summary still claims only T1 is constructed and the other six are deferred.

---

## Phase 3: Time-Axis Findings

| # | Location | Description | Severity |
|---|----------|-------------|----------|
| 1 | chu-duality.tex:574–576 | Fano triad summary understates new proofs (= S4 above) | DRIFT |
| 2 | articulated.tex:891–896 vs 861–868 | Two Sinkhorn analogies within 30 lines use different framings | DRIFT |
| 3 | articulated.tex:889 | "exploration temperature" renamed to "Boltzmann target"; exploration concept lost from nonuple | DRIFT |
| 4 | optimal-cycle.tex:191 | rmk:dual-ascent uses "MPPI sample" while sibling text uses "GP-UCB queries" | HARMLESS |
| 5 | mppi.tex:55–58 | "Schilder-type" → Varadhan citation; clean | HARMLESS |
| 6 | riccati.tex:28–29 | Stabilizability condition added; strengthens existing reference | HARMLESS |
| 7 | bibliography.tex | Two new bibentries (BaezOctonions, Varadhan1967) properly cited | HARMLESS |

**No BREAKING issues found.**

---

## Phase 4: Fresh-Eyes Confusion Scan

| # | Topic | Verdict |
|---|-------|---------|
| 1 | GP-UCB label vs LCB formula | RESOLVED — document explains both terms |
| 2 | Algorithm 3 line~13 for cost functional | **UNRESOLVED** — line 13 is EndFor; cost is line 15 |
| 3 | rem:arithmetic-complete "lines 3–15" | RESOLVED — range covers full loop body |
| 4 | "lines 7–8" backward solve | RESOLVED — P_H + Riccati = backward solve |
| 5 | Algorithm 3 vs Algorithm 2 faithfulness | RESOLVED — faithful instantiation confirmed |
| 6 | ε fixed vs β̄_n controlled exploration | RESOLVED — two modes explicitly distinguished |
| 7 | Per-iteration H(f) decrease | **UNRESOLVED** — prop:student-convergence doesn't support this |
| 8 | rmk:sigma-algebra readability | RESOLVED — dense but self-contained |
| 9 | Quintuple → nonuple count | RESOLVED — deliberate incremental construction |
| 10 | Cycle connection line references | RESOLVED — metaphorical but precise |
| 11 | Verblunsky splitting indexing | RESOLVED — α₀ has weight k=0, contributes nothing |
| 12 | Jensen gap vs holonomy | RESOLVED — document explicitly distinguishes |
| 13 | Chu pairing for Action-State | RESOLVED — bilinear, separated, extensional |
| 14 | T3/T5 technical gaps | RESOLVED — acknowledged as conjecture |
| 15 | Forward-only scalar exponential | RESOLVED — exp of (ℝ₊,×) |
| 16 | Nonuple count integrity | RESOLVED — 9 roles confirmed |
| 17 | "Sections 1–8" scope | RESOLVED — foundations through ergodic |

---

## Symbolic Integrity

### References: CLEAN
All \cref, \ref, \eqref targets resolve. Zero dangling references. ~60 orphan labels (low severity — foundational definitions for self-containment).

### Citations: CLEAN
All \cite keys resolve. 4 uncited bibliography entries: BarrChuHist, Davenport, GrenanderSzego, IwaniecKowalski (low severity).

### Colors: CLEAN
All 4 semantic colors (AcqColor, PostColor, ConColor, CycleColor) used consistently within their domains. No misuse found.

### Signs: CLEAN
- All 8 argmin instances correct for cost minimization. Zero argmax in algorithms/propositions.
- All acquisition formulas use μ − √β̄σ (LCB, correct for cost minimization).
- All safe sets use μ + √β̄σ ≤ c_max (UCB, correct for pessimistic safety).

### Algorithm Line References: 1 ERROR
- articulated.tex:173: "line~13" should be "line~15" (= C2 above).
- All other 22 line references verified correct.

### Compilation: CLEAN
101 pages. Zero errors. Zero undefined references.

---

## Comparison with Prior Check

| Issue | Prior Status | Current Status |
|-------|-------------|----------------|
| C1: Acquisition sign error (argmax UCB for cost) | UNRESOLVED | **FIXED** — all argmin LCB |
| C1b: Safe set S₁ vs S_{n+1} sign mismatch | UNRESOLVED | **FIXED** — all UCB pessimistic |
| C1c: Phase 1 sigma points not in safe set | UNRESOLVED | **FIXED** — Θ ∩ S₁ |
| C2: Algorithm 3 missing Phase 1 | UNRESOLVED | **FIXED** — sigma-point warm start added |
| C3: Sufficiency overclaim | CONTRADICTED | **FIXED** — "optimal batch design" |
| S1: G ⊥ F_n false | UNRESOLVED | **FIXED** — G_n ⊥ F_{n-1} |
| S2: MPPI terminology drift | UNRESOLVED | **MOSTLY FIXED** — forward-only.tex remains |
| S3: Line-range fragility | UNRESOLVED | **FIXED** — all references verified |
| NEW: Per-iteration H(f) decrease | — | **NEW FINDING** |
| NEW: articulated.tex:173 line~13 error | — | **NEW FINDING** |
| NEW: lie-group-intro.tex:9 wrong \cref | — | **NEW FINDING** |

---

## Action Priority

| Priority | Item | Action |
|----------|------|--------|
| 1 | C1: Per-iteration H(f) decrease | Either prove the link (GP-LCB iteration ↔ effective ν increase) or weaken the claim |
| 2 | C2: Line reference error | Change "line~13" to "line~15" at articulated.tex:173 |
| 3 | S1: Wrong \cref in lie-group-intro | Change \cref{rmk:mpc} to \cref{rmk:dual-ascent} at lie-group-intro.tex:9 |
| 4 | S2: forward-only.tex MPPI | Consider "forward-only estimator" or leave as method proper name |
| 5 | S3: eq:gp-ucb label | Consider renaming to eq:gp-lcb (low priority, cosmetic) |
| 6 | S4: Fano triad summary | Update "deferred" text to reflect completed proofs |
