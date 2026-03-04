# Phase 5 -- Symbolic Consistency Checks
**Date**: 2026-03-04
**Scope**: All 22 `.tex` files in the repository

---

## 5a. Notation Consistency

### Acknowledged overloads (NOT errors)
Per `rem:notation-unification` (framework.tex, line 714), four symbols are deliberately overloaded:
- **kappa**: curvature of viability manifold AND king node of execution graph
- **varphi**: conformal parameter, phase operation, AND agentic flow
- **rho**: displacement from phase boundary (cadre lattice rank function AND force ratio)
- **Sigma**: switching surface in both three-body and manipulation contexts

### UNACKNOWLEDGED symbol collisions flagged

**MEDIUM severity -- same letter, genuinely different mathematical objects:**

1. **V** (7 files): Used simultaneously as:
   - Lyapunov function / water level (framework.tex, main.tex, threebody.tex)
   - Vertex set in execution graph G = (V, E, c) (calculus.tex, meanfield.tex, fields2022.tex)
   - Optimal continuation value (govfi.tex:695)

   **Assessment**: The Lyapunov V vs vertex-set V collision is the most structurally concerning. Both appear in core chapters (framework vs calculus) and a reader following cross-references will encounter both meanings. Consider adding V to the notation-unification remark or using a distinct symbol (e.g., `\mathbb{V}` for vertex set).

2. **E** (4 files): Used simultaneously as:
   - Edge set in execution graph G = (V, E, c) (calculus.tex, fields2022.tex)
   - Target event on external sigma-algebra (meanfield.tex:280)
   - Event "all blocks at goal" (manipulation.tex:1636)

   **Assessment**: The edge-set E and probabilistic-event E coexist in the core theory. The meanfield chapter uses both G_task = (V, E) and E-as-event within 30 lines of each other.

3. **K** (4 files): Used simultaneously as:
   - Viability kernel (framework.tex -- central to the entire theory)
   - Number of hierarchy levels (zhongxian.tex:42)
   - Number of MPPI samples (manipulation.tex:996)
   - Fourier embedding dimension (manipulation.tex:1136)

   **Assessment**: The manipulation.tex usages of K as sample count/dimension are local and clearly contextual, so confusion is unlikely. But zhongxian.tex uses K as hierarchy depth in a chapter that also discusses viability kernels.

4. **S** (4 files): Used simultaneously as:
   - State space (framework.tex -- foundational)
   - Vertex subset in flow-cut context (calculus.tex:681-682)
   - RANK subspace of Jacobian transpose (manipulation.tex:218)
   - Surplus from agreement (govfi.tex:937)

5. **sigma** (5 files): Used as:
   - Optimal exit strategy sigma* (huarongdao.tex:452)
   - Standard deviation output of neural net (calculus.tex:1061)
   - sigma-algebra (meanfield.tex:281)
   - Weight vector parameter (threebody.tex:393)
   - Revenue volatility (govfi.tex:626)

6. **theta** (3 files): Used as:
   - Neural network parameters (calculus.tex:1061)
   - Percolation probability function (fields2022.tex:145)
   - GP kernel hyperparameters (manipulation.tex:731, 762, 787)

**LOW severity -- standard mathematical convention, unlikely to confuse:**

7. **T**: time horizon vs map vs cumulative price level (5 files)
8. **F**: set-valued dynamics vs causality fractal vs friction cone (3 files)
9. **G**: execution graph vs Cheeger constant argument vs ground reflection (4 files)
10. **alpha**: mask parameter vs kernel parameter vs regularization weight vs loss-given-default (4 files)
11. **mu**: neural net output vs mean-field measure vs drift coefficient (3 files)
12. **tau**: capacity margin vs detection threshold (2 files)
13. **beta**: inheriting agent vs drift coefficient (2 files)
14. **gamma**: curve in state space vs edge weight (2 files)
15. **mathcal{L}**: Lagrangian (threebody.tex) vs loss field (govfi.tex) -- different calligraphic object
16. **mathcal{G}**: step-distance graph (huarongdao.tex) vs ground reflection (threebody.tex)

### Recommendation
Add V and E to the notation-unification remark alongside kappa, varphi, rho, Sigma. The V collision is the most structurally important since both the Lyapunov function and the vertex set are central abstractions used throughout the document.

---

## 5b. Reference Integrity

### Dangling references (label used but never defined): **0**
No dangling references found. All `\cref`, `\ref`, and `\eqref` targets resolve to defined labels.

### Orphan labels (defined but never referenced): **314**
This is a large number but expected for a document of this size where many labeled environments serve as anchor points for future cross-referencing. Notable categories:

**Structural orphans (sections/chapters never cross-referenced):**
- `sec:intro`, `sec:conclusion`, `sec:sword`, `sec:tower`, `sec:training`
- Many sub-sections: `sec:alien-*`, `sec:gaokao-*`, `sec:gf-*`, `sec:zx-*`, `sec:triad-*`

**Theorem/definition orphans (stated but never cited elsewhere):**
- `thm:nolie`, `thm:saddle`, `thm:ergodic`, `thm:m-bilevel`, `thm:m-commutator`, `thm:m-intractable`
- `thm:alien-mountain`, `thm:duffin-schaeffer`, `thm:cheeger-viab`, `thm:3b-strong-duality`
- `thm:dynamic-allocation`, `thm:optimal-trigger`, `thm:spectral-contagion`, `thm:gaokao-sword-removal`
- Many `def:*`, `prop:*`, `cor:*` labels in appendix chapters

**Equation orphans:**
- Many equations in manipulation.tex (see 5d below)
- Many equations in govfi.tex, threebody.tex, gaokao.tex

**Remark orphans:**
- Large number of `rem:*` labels (195+) defined but never referenced

**Assessment**: Orphan labels are low severity. They may serve as future cross-reference anchors. However, the orphan count (314 out of ~530 total labels, i.e. ~59%) is high enough to suggest that many were defined speculatively.

---

## 5c. Citation Integrity

### Cited but not in bibliography: **0**
All citation keys resolve to defined `\bibitem` entries.

### In bibliography but never cited: **0**
All bibliography entries are cited at least once.

**Assessment**: Citation integrity is perfect. The bibliography is clean with no orphans or dangling citations.

---

## 5d. New Content Label Check (manipulation.tex)

### Definition and reference status of each new label:

| Label | Defined? | Referenced within manipulation.tex? | Referenced from outside? |
|-------|----------|-------------------------------------|--------------------------|
| `sec:m-stochastic-fov` | Yes (line 575) | No | No |
| `def:m-stochastic-fov` | Yes | Yes (within manipulation.tex) | No |
| `rem:m-soft-invisibility` | Yes | No | No |
| `eq:m-fov-product` | Yes | No | No |
| `eq:m-gp-boundary` | Yes | Yes (within manipulation.tex) | No |
| `eq:m-gp-extinction` | Yes | No | No |
| `eq:m-gp-sensor` | Yes | No | No |
| `eq:m-fov-gp` | Yes | No | No |
| `eq:m-fov-mean` | Yes | No | No |
| `eq:m-fov-kernel` | Yes | Yes (within manipulation.tex) | No |
| `eq:m-vis-prob` | Yes | No | No |
| `eq:m-kernel-param` | Yes | No | No |
| `eq:m-info-gain` | Yes | No | No |
| `eq:m-joint-opt` | Yes | Yes (within manipulation.tex) | No |
| `eq:m-gradient-decomp` | Yes | No | No |
| `rem:m-active-optics` | Yes | No | No |
| `eq:m-active-optics-update` | Yes | No | No |

### Collision check: **No collisions**
None of the 17 new labels collide with any existing label in the document. The `m-` prefix namespace is clean.

### Cross-reference assessment:
- **4 out of 17 labels** are referenced within manipulation.tex itself (`def:m-stochastic-fov`, `eq:m-gp-boundary`, `eq:m-fov-kernel`, `eq:m-joint-opt`)
- **0 out of 17 labels** are referenced from outside manipulation.tex
- **13 out of 17 labels** are completely orphaned (never referenced anywhere)

### Should they be referenced from outside?
- `sec:m-stochastic-fov` -- Possibly. If other chapters discuss stochastic visibility or sensor planning, this section should be cross-referenced. The notation-unification remark already mentions manipulation's Sigma as a contact transition; the stochastic FoV section extends this to observation.
- `def:m-stochastic-fov` -- Potentially useful if meanfield.tex or threebody.tex discuss observation under uncertainty.
- `rem:m-soft-invisibility` -- Self-contained remark; orphan status is fine.
- The equation labels are mostly internal to the stochastic FoV development and do not need external references unless other chapters build on the GP-based visibility framework.

---

## Summary

| Check | Status | Issues Found |
|-------|--------|-------------|
| 5a. Notation | 2 medium-severity collisions | V (Lyapunov vs vertex set) and E (edge set vs event) are unacknowledged |
| 5b. References | Clean | 0 dangling; 314 orphans (low severity) |
| 5c. Citations | Perfect | 0 missing; 0 unused |
| 5d. New labels | Clean, no collisions | 13 of 17 are orphaned; none referenced from outside manipulation.tex |
