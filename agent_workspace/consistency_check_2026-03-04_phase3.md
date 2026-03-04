# Phase 3 — Time-Axis Consistency Check — 2026-03-04

**Scope:** `git diff HEAD~2..HEAD -- '*.tex'` (commits `31ccb5d` and `e7f95be`).

**Changed files:**
- `sections/meanfield.tex` — 176 new lines (2 remarks, 1 definition, 1 theorem, 1 corollary, 1 remark)
- `appendices/manipulation.tex` — 12 net new lines (expanded `def:m-dag`, expanded `rem:m-dag-md`)
- `main.tex` — 10 new lines (2 bibitems: `martinelli1999`, `liggett2005`)

---

## Inconsistencies

### 1. `\kappa` used as Lipschitz constant — conflicts with notation-unification

- **What changed:** `sections/meanfield.tex:392` (new) — `\kappa \leq 1 - c\,\delta` (contraction constant in proof of `thm:fractal-convergence`)
- **What it conflicts with:** `sections/framework.tex:719-723` (unchanged) — `rem:notation-unification` explicitly assigns `\kappa` two meanings: curvature of the viability manifold and king node of the execution graph.
- **Severity: DRIFT.** The new use is inside a proof environment and locally scoped; the reader can distinguish from context. But `rem:notation-unification` claims the collision is deliberate and exhaustive ("Three symbols recur across chapters"). A fourth, unannounced use breaks the claim of exhaustiveness.

### 2. `\rho` used as parameter-variation rate — conflicts with notation-unification

- **What changed:** `sections/meanfield.tex:427,460` (new) — `\rho = \sup_t \|\alpha(t{+}1) - \alpha(t)\|` (control-rate bound in `cor:event-controllability`)
- **What it conflicts with:** `sections/framework.tex:734-741` (unchanged) — `rem:notation-unification` assigns `\rho` the meaning "displacement from a phase boundary."
- **Severity: DRIFT.** Same structure as issue 1. Inside a theorem/proof, locally clear. But `rem:notation-unification` claims `\rho = 1` is always the switching surface, and the new use has no switching-surface interpretation.

### 3. `\varphi` gains a fourth meaning — not declared in notation-unification

- **What changed:** `sections/meanfield.tex:165,338,340,354` (new) — `\varphi(\mu)` is the external field map from probability measures to `\mathbb{R}^d`.
- **What it conflicts with:** `sections/framework.tex:724-733` (unchanged) — `rem:notation-unification` lists three meanings of `\varphi` (conformal parameter, phase operation, agentic flow) but not "external field map."
- **Severity: DRIFT.** The new meaning is related to the existing ones (external field is a kind of phase parameter), but the remark's claim that "all three are aspects of the same map" doesn't obviously extend to the Wasserstein-Lipschitz external field function. The unification remark needs a fourth bullet or an acknowledgement.

### 4. `\mathcal{X}` used without formal definition — inconsistent with state-space symbol `S`

- **What changed:** `sections/meanfield.tex:332-396` (new) — `\mathcal{X}` appears as the state space (Polish space) throughout `def:causality-fractal` and `thm:fractal-convergence`.
- **What it conflicts with:** `sections/framework.tex:5` (unchanged) — the state space is denoted `S` throughout the framework chapter and all prior content.
- **Severity: DRIFT.** Both symbols coexist. `S` is the viability state space; `\mathcal{X}` is the per-agent state space of the mean-field kernel. The distinction is real but never explained. The reader encounters `S` for 10+ pages, then `\mathcal{X}` appears without a bridging sentence.

### 5. `\mathcal{A}` symbol collision

- **What changed:** `sections/meanfield.tex:414` (new) — `\alpha \in \mathcal{A}` (parameter set in `cor:event-controllability`).
- **What it conflicts with:** `sections/calculus.tex:1879,1918` (unchanged) — `\mathcal{A}` is used as an area/action functional in the Camus theorem discussion.
- **Severity: HARMLESS.** Different chapters, different contexts, no cross-reference between them.

### 6. `$E$` overloading within 32 lines

- **What changed:** `sections/meanfield.tex:312` (new) — `E` = edge set in `def:causality-fractal`.
- **What it conflicts with:** `sections/meanfield.tex:280` (unchanged) — `E` = target event in `prop:event-lock`.
- **Severity: DRIFT.** Same chapter, 32 lines apart. The two environments are self-contained, but a reader scanning the section sees `E` flip meaning without transition.

### 7. Forward reference from main chapter to appendix definition

- **What changed:** `sections/meanfield.tex:313` (new) — `\cref{def:m-dag}` references `appendices/manipulation.tex:928`.
- **What it conflicts with:** Document ordering: `meanfield.tex` is loaded at `main.tex:161`, `manipulation.tex` at `main.tex:180`.
- **Severity: HARMLESS.** Forward references resolve with two-pass LaTeX compilation, and the pattern already exists (e.g., `framework.tex:746` references `sec:manipulation`). Verified: no "undefined reference" warning for `def:m-dag` in the log file.

### 8. `rem:m-dag-md` (manipulation.tex) elides hypotheses of referenced theorems

- **What changed:** `appendices/manipulation.tex:954-959` (new) — states that "ergodic convergence and event controllability follow from the spectral gap `\lambda_1 > 0`."
- **What it conflicts with:** `sections/meanfield.tex:349-360` (new, same commits) — `thm:fractal-convergence` requires three additional hypotheses (Feller continuity, Lipschitz external field, Doeblin minorisation) beyond `\lambda_1 > 0`. `cor:event-controllability` adds a fourth (structural stability / Lipschitz fixed-point map).
- **Severity: DRIFT.** The statement is not wrong (it says "under the regularity conditions of \cref{thm:fractal-convergence}"), so the reference is technically correct. But the sentence structure — "follow from the spectral gap $\lambda_1 > 0$" — places the emphasis on the gap, not the conditions. A reader who doesn't click through will take away an incomplete picture.

### 9. Old "KL gap condition" phrase replaced — but `rem:mother-daughter` still informal

- **What changed:** `appendices/manipulation.tex:635` (old) said "the KL gap condition of `\cref{rem:mother-daughter}`"; the new text (line 951-953) says "the mother-daughter consistency of `\cref{rem:mother-daughter}` (small KL divergence between predicted and actual distributions)."
- **What it conflicts with:** `sections/meanfield.tex:124-143` (unchanged) — `rem:mother-daughter` discusses KL divergence informally ("is small for all monitored agents") but defines no named condition, no quantitative bound, and no formal criterion.
- **Severity: HARMLESS.** The new phrasing is an improvement over the old one (it's more descriptive). The remaining looseness is in the unchanged `rem:mother-daughter` itself, not in the new text.

### 10. Bibliographic entries `martinelli1999` and `liggett2005` — correctly placed

- **What changed:** `main.tex:310-319` (new) — two new `\bibitem` entries.
- **What references them:** `sections/meanfield.tex:405-406` (new) — `\cite{martinelli1999}` and `\cite{liggett2005}` in the proof of `thm:fractal-convergence`.
- **Severity: HARMLESS.** Citations and bibitems are consistent. No orphan citations, no orphan bibitems. Verified in compilation log: no "undefined citation" warning for either.

---

## Cross-reference integrity (all new labels)

| Label | File:Line | Referenced from | Status |
|---|---|---|---|
| `rem:parent-daughter-bridge` | meanfield.tex:147 | meanfield.tex:187,316 | OK |
| `rem:causal-mass-gap` | meanfield.tex:179 | meanfield.tex:321 | OK |
| `def:causality-fractal` | meanfield.tex:311 | meanfield.tex:347; manipulation.tex:955 | OK |
| `thm:fractal-convergence` | meanfield.tex:345 | manipulation.tex:956 | OK |
| `cor:event-controllability` | meanfield.tex:412 | manipulation.tex:958 | OK |
| `rem:rg` | meanfield.tex:472 | (not yet referenced) | OK (leaf) |
| `eq:mf-operator` | meanfield.tex:334 | meanfield.tex:474 | OK |
| `eq:event-conv` | meanfield.tex:368 | (internal to theorem) | OK |
| `eq:exp-mixing` | meanfield.tex:376 | (internal to theorem) | OK |
| `eq:tracking` | meanfield.tex:429 | meanfield.tex:438 | OK |

No dangling references. No multiply defined labels. No removed labels.

---

## Summary table

| # | What changed | Conflicts with | Severity |
|---|---|---|---|
| 1 | `\kappa` as Lipschitz const (meanfield:392) | `rem:notation-unification` (framework:719) | DRIFT |
| 2 | `\rho` as control rate (meanfield:427) | `rem:notation-unification` (framework:734) | DRIFT |
| 3 | `\varphi` as external field (meanfield:165) | `rem:notation-unification` (framework:724) | DRIFT |
| 4 | `\mathcal{X}` undeclared (meanfield:332) | state space `S` (framework:5) | DRIFT |
| 5 | `\mathcal{A}` collision (meanfield:414) | calculus.tex:1879 | HARMLESS |
| 6 | `E` overloading (meanfield:280 vs 312) | same chapter, 32 lines | DRIFT |
| 7 | Forward cref to appendix (meanfield:313) | document order | HARMLESS |
| 8 | Elided hypotheses (manipulation:954) | thm:fractal-convergence conditions | DRIFT |
| 9 | KL phrase updated (manipulation:951) | rem:mother-daughter informal | HARMLESS |
| 10 | New bibitems (main:310) | new citations (meanfield:405) | HARMLESS |

**Totals:** 0 BREAKING, 6 DRIFT, 4 HARMLESS.

The document compiles without errors related to the new content. All new cross-references resolve. No labels were moved, deleted, or duplicated.

The most actionable items are (1-3): the three symbol collisions with `rem:notation-unification`. Either update the remark to include the new uses, or choose different symbols in the new content.
