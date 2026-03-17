# Post-Fix Verification: Consistency Check Residuals

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the 4 actionable issues found by the post-fix consistency check (1 LOAD-BEARING, 1 HIGH, 2 STRUCTURAL).

**Architecture:** Four independent edits (no inter-task dependencies) followed by a single compilation + grep verification pass. All edits are in `.tex` files — no code changes.

**Tech Stack:** LaTeX (xelatex), grep for verification.

---

## Dependency Graph

```
Task 1 (C1: holonomy claim)  ──┐
Task 2 (C2: line ref)         ──┼──→ Task 5 (compile + verify)
Task 3 (S1: wrong \cref)      ──┤
Task 4 (S4: triad summary)   ──┘
```

Tasks 1–4 are fully independent (different files or non-overlapping lines in the same file). Task 5 depends on all four.

---

## File Map

| File | Tasks | Action |
|------|-------|--------|
| `sections/articulated.tex:173` | Task 2 | Change `line~13` → `line~15` |
| `sections/articulated.tex:1191-1193` | Task 1 | Rewrite 3-line holonomy convergence claim |
| `sections/lie-group-intro.tex:9` | Task 3 | Change `\cref{rmk:mpc}` → `\cref{rmk:dual-ascent}` |
| `sections/chu-duality.tex:574-576` | Task 4 | Update Fano triad summary to reflect completed proofs |

All paths relative to `/Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory/`.

---

## Task 1: Rewrite Holonomy Convergence Claim (C1 — LOAD-BEARING)

**Files:**
- Modify: `sections/articulated.tex:1191-1193`

**Context:** The current text claims "Each outer iteration decreases H(f) (prop:student-convergence)" but prop:student-convergence only proves H(f_{t_ν}) → 0 along the Student t family, not per GP-LCB iteration. The fix replaces the per-iteration H(f) claim with the per-iteration V_n contraction (which IS proved in rmk:mpc), connects the rate to γ_T as algorithmic holonomy (rmk:omd-regret), and cites prop:student-convergence for the Gaussian endpoint only.

**Mathematical justification:**
- V_n = tr(Σ_n) strictly decreasing per iteration: proved at rmk:mpc (optimal-cycle.tex:594-597)
- γ_T plays the role of holonomy H(f): stated at rmk:omd-regret (optimal-cycle.tex:293-298)
- H(f) = 0 iff Gaussian: prop:student-convergence (optimal-cycle.tex:149-168)
- Lines 1186-1190 already cite R_T/T → 0 via γ_T (prop:gp-regret) — no redundancy

- [ ] **Step 1: Replace lines 1191-1193**

Current text (articulated.tex:1191-1193):
```latex
Each outer iteration decreases $H(f)$
(\cref{prop:student-convergence}):
the re-cycle converges to the cycle.
```

Replace with:
```latex
Each outer iteration contracts the Lyapunov function
$V_n = \tr(\Sigma_n)$ (\cref{rmk:mpc}), with
$\gamma_T$ playing the role of holonomy
(\cref{rmk:omd-regret}): the re-cycle converges to the
Gaussian fixed point $H(f) = 0$
(\cref{prop:student-convergence}).
```

- [ ] **Step 2: Verify no dangling references**

Run: `grep -n 'prop:student-convergence\|rmk:mpc\|rmk:omd-regret' sections/articulated.tex`

Expected: The new text references all three labels. All three are defined in `sections/optimal-cycle.tex`. No new labels introduced.

---

## Task 2: Fix Algorithm 3 Line Reference (C2 — HIGH)

**Files:**
- Modify: `sections/articulated.tex:173`

**Context:** Algorithm 3 (`alg:quadruped`) has `\EndFor` at lines 13-14 (end of inner loops), pushing the cost functional J_n to line 15. The current reference says "line~13" but should say "line~15".

- [ ] **Step 1: Change line number**

Current text (articulated.tex:173):
```latex
In the cost functional (\cref{alg:quadruped}, line~13), $h_k$ is regularized to
```

Replace with:
```latex
In the cost functional (\cref{alg:quadruped}, line~15), $h_k$ is regularized to
```

---

## Task 3: Fix Cross-Reference in lie-group-intro (S1 — STRUCTURAL)

**Files:**
- Modify: `sections/lie-group-intro.tex:9`

**Context:** The text says "the barrier parameter ε corresponds to the effective ν of the exploration distribution (\cref{rmk:mpc})." But rmk:mpc (optimal-cycle.tex:578-602) discusses MPC state and Lyapunov stability — it never mentions Student t, effective ν, or the ε–ν correspondence. The correct target is rmk:dual-ascent (optimal-cycle.tex:186-223), which describes the ε annealing schedule and the Boltzmann temperature interpretation.

- [ ] **Step 1: Change \cref target**

Current text (lie-group-intro.tex:9, end of line):
```latex
(\cref{rmk:mpc}).
```

Replace with:
```latex
(\cref{rmk:dual-ascent}).
```

**Note:** The full line is very long. The edit targets only the `\cref{rmk:mpc}` at the end, changing it to `\cref{rmk:dual-ascent}`. Everything else on line 9 remains unchanged.

---

## Task 4: Update Fano Triad Summary (S4 — STRUCTURAL)

**Files:**
- Modify: `sections/chu-duality.tex:574-576`

**Context:** The text claims only T1 is constructed and the other six are deferred. In reality, thm:fano-triads (chu-duality.tex:637-783) now fully proves T1, T2, and T6, while rmk:remaining-triads sketches T3-T5 and T7 with identified key identities.

- [ ] **Step 1: Update summary text**

Current text (chu-duality.tex:574-576):
```latex
Triad~T1 is the contact Jacobian constructed in detail below;
the remaining six triads are identified by their physical content
but their full Chu tensor-product verification is deferred.
```

Replace with:
```latex
Triads~T1, T2, and~T6 are constructed in full below
(\cref{thm:fano-triads}); the remaining four (T3--T5, T7)
are identified by their physical content with key identities
verified (\cref{rmk:remaining-triads}).
```

- [ ] **Step 2: Verify labels exist**

Run: `grep -n 'thm:fano-triads\|rmk:remaining-triads' sections/chu-duality.tex`

Expected: Both labels are defined in chu-duality.tex (thm:fano-triads around line 637, rmk:remaining-triads around line 786).

---

## Task 5: Compile and Verify

**Files:** All `.tex` files (read-only verification)

**Depends on:** Tasks 1–4

- [ ] **Step 1: Double-pass compilation**

Run:
```bash
cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory
xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex
```

Expected: "Output written on main.pdf (101 pages)." Zero errors.

- [ ] **Step 2: Check for undefined references**

Run: `grep 'undefined' main.log`

Expected: No output (zero undefined references).

- [ ] **Step 3: Verify Task 1 — no stale H(f) per-iteration claims**

Run: `grep -n 'iteration.*decreases.*H(f)\|iteration.*H(f).*decreases' sections/articulated.tex sections/optimal-cycle.tex`

Expected: No output. The old claim has been replaced.

- [ ] **Step 4: Verify Task 2 — line~15 reference**

Run: `grep -n 'line~13' sections/articulated.tex`

Expected: No output (the old reference is gone).

- [ ] **Step 5: Verify Task 3 — no rmk:mpc in lie-group-intro**

Run: `grep -n 'rmk:mpc' sections/lie-group-intro.tex`

Expected: No output.

- [ ] **Step 6: Verify Task 4 — triad summary updated**

Run: `grep -n 'deferred' sections/chu-duality.tex`

Expected: No output matching the old "verification is deferred" text. (Other uses of "deferred" elsewhere in the file are acceptable.)

---

## Summary

| Task | Issue | Severity | Edit size | Risk |
|------|-------|----------|-----------|------|
| 1 | Per-iteration H(f) claim | LOAD-BEARING | 3 lines → 6 lines | Low — cites existing results, no new math |
| 2 | Line ref 13→15 | HIGH | 1 number | Zero |
| 3 | Wrong \cref target | STRUCTURAL | 1 label | Zero |
| 4 | Stale triad summary | STRUCTURAL | 3 lines → 3 lines | Low — references existing theorem/remark |
| 5 | Compile + verify | — | Read-only | Zero |
