# Self-Symbolic Consistency Check — Final Pass (2026-02-28)

## Summary

| Category | Count | Breakdown |
|----------|-------|-----------|
| LOAD-BEARING tensions | 22 | 6 REINFORCED, 14 UNRESOLVED, 0 CONTRADICTED |
| Time-axis issues | 11 | 0 BREAKING, 3 DRIFT, 8 HARMLESS |
| Fresh-eyes confusions | 10 | 0 RESOLVED, 10 UNRESOLVED |
| Symbolic issues | ~235 | 0 dangling refs, ~230 orphan labels, 0 duplicates, 0 colour errors, 0 undefined commands |

**Headline**: The paper compiles cleanly and has zero symbolic errors. The formal infrastructure (viability axiom, sword definition, binary lifecycle, flow-cut duality) is internally consistent. The three genuine vulnerabilities are: (1) the mean-field baseline derivation is a proof sketch with a circular reference chain, (2) the main text has structural forward-reference violations against its own declared reading order, and (3) the pawn-to-sword reversibility at w=0 is unaddressed.

---

## Critical Findings (requires action)

### CF-1. Mean-field baseline circularity (LOAD-BEARING, UNRESOLVED)

`lem:capacity` (framework.tex:61) → defers to `prop:detection-derivation` (meanfield.tex:22) → cites `lem:capacity` step (iii). Circular. The "proof sketch" label on `prop:detection-derivation` propagates upward through the entire mean-field interpretation.

**Evidence**: Phase 2 (T1) + Phase 4 (confusion #10).

**Impact**: The capacity formula c(e_r) = max(||U_r|| − Ū, 0) is the bridge between viability theory and the mean-field claim. If the baseline is not uniquely justified, the central slogan "the sword is the mean" rests on assertion.

**Key question**: Why is the arithmetic mean (not median, weighted mean, or percentile) the uniquely optimal baseline under finite bandwidth and the viability axiom?

---

### CF-2. Forward-reference violations in reading order (UNRESOLVED × 3)

The main text uses three concepts before defining them:

| Concept | Used in | Defined in | Gap |
|---------|---------|------------|-----|
| Du Mu's theorem (`thm:dumu`) | framework.tex:200, 400 | discussion.tex:74 | Ch.2 → Ch.8 |
| Water (`def:water`, `sec:water`) | framework.tex:194, 390 | discussion.tex:31, 49 | Ch.2 → Ch.8 |
| Execution chain (`def:exgraph`) | framework.tex:848, results.tex:190 | calculus.tex:48 | Ch.2-3 → Ch.6 |

**Evidence**: Phase 4 (confusions #4, #5, #7).

---

### CF-3. Appendix-dependent claims in main text (UNRESOLVED × 3)

Three main-text passages depend on appendix-only material:

| Passage | Reference | Location |
|---------|-----------|----------|
| "The two failure modes in `\cref{sec:errorlog}`" | applications.tex:85 | → three_li.tex:420 |
| "rank function of the cadre lattice `\cref{def:cadre-lattice}` and force ratio `\cref{eq:3b-rho}`" | framework.tex:715 | → zhongxian.tex:35, threebody.tex:1051 |
| "the superconducting state — see `\cref{rem:3b-superconductor}`" | calculus.tex:1902 | → threebody.tex:1797 |

**Evidence**: Phase 4 (confusions #1, #2, #3).

---

### CF-4. Pawn-to-sword reversibility at w=0 (LOAD-BEARING, UNRESOLVED)

Du Mu's theorem (discussion.tex:74) assumes w(t) monotonically decreasing. The paper never addresses whether the king can restore w > 0 before the transition completes. If reversible, the binary lifecycle for water-depleted systems collapses.

**Evidence**: Phase 2 (T7).

**Key question**: Is there a structural irreversibility (hysteresis in pawn loyalty, trust destruction) that creates a point of no return? If so, formalise it. If not, state Du Mu's theorem applies only to the extraction-dominant regime.

---

### CF-5. U = U_max guarantees viability — asserted without proof (UNRESOLVED)

framework.tex:33: "When U = U_max, the control set is full and this path is mathematically guaranteed to exist." No proof that full control implies the tangential condition F(x) ∩ T_K(x) ≠ ∅ for all x.

**Evidence**: Phase 4 (confusion #6).

---

## Structural Findings (author's discretion)

### SF-1. Phase transitions: mean-driven vs king-driven (UNRESOLVED)

`thm:meanfield` proves the Ū-shift channel (τ fixed). But `prop:imperfect`, `prop:phase`, and `rem:guanxi-sword` describe king-driven (τ-shift) mechanisms. The headline "the sword is the mean" elides the king-driven channel. The two channels are not formally unified.

### SF-2. No thermodynamic limit justification

The mean-field interpretation is an "interpretive result" (conclusion.tex:7), not a theorem about large-N limits. Huarong Dao (N=10) instantiates the full framework without invoking the mean. Zhongxian shows clique correlations that violate independence. The formal results (binary lifecycle, fixed-point impossibility) survive without the mean-field claim.

### SF-3. Pre-sword instability: qualitative, not quantitative

Pre-sword regression is correctly classified as "a bet, not a resolution" (framework.tex:840). But no timescale bound is given for the instability. The Obs-expansion drive (prop:imperfect) provides the mechanism but not the rate.

### SF-4. Training completeness (thm:training) lacks convergence proof

calculus.tex:506-524 claims "each iteration increases |φ| toward the max-flow value" — a convergence claim without a convergence proof.

### SF-5. "Path to infinity" vs "path to exit" (UNRESOLVED)

The viability axiom requires γ: [0,∞) → K (unbounded survival). Huarong Dao uses a finite path to an exit state. Neural networks use a static condition. These three mathematical objects are mapped to one axiom without reconciliation.

### SF-6. Three DRIFT items from Phase 3

1. `lem:capacity` / `prop:detection-derivation` mutual citation (confusing for linear reading)
2. `rem:viab-subset` exposes pre-existing tension in axiom's ∀ s ∈ K quantifier
3. γ=0 superconductor parenthetical placed inside `\end{proof}` environment (stylistic)

---

## Cosmetic Findings

- ~230 orphan labels (defined but never referenced) — normal for a 182-page paper
- 4 new labels from today not yet cross-referenced: `rem:3b-rho-reconcile`, `rem:gap-superconductor`, `rem:viab-subset`, `rem:meanfield-validity`
- Guanxi scalar quantification (zhongxian.tex) is operationalised as yuan spent on vote canvassing — the formal dual-ring model allows multi-dimensional x_G but the prose oversimplifies
- 政績同構 (self-similar viability pressure, zhongxian.tex:538) — asserted not proven from data
- Transcendence fractions in second_sex.tex — author-assigned, no inter-coder reliability
- Sources.tex proverb analysis — reads framework INTO history (creative hermeneutics, not structural proof)

---

## Symbolic Integrity

| Check | Status |
|-------|--------|
| Dangling references | **0** — all `\cref{}`, `\ref{}`, `\eqref{}` resolve |
| Duplicate labels | **0** |
| Undefined custom commands | **0** — `\Viab`, `\Ur`, `\Obs` all defined in main.tex |
| Colour consistency | **CLEAN** — 545 semantic colour uses (sword/dao/water/caution), no rogue colours |
| New labels from today | **8/8 defined**, 4/8 cross-referenced |

---

## Phase 1 Tension Manifest (all chapters)

### LOAD-BEARING (22 total)

| # | File | Lines | Claim | Vulnerability |
|---|------|-------|-------|---------------|
| 1 | intro.tex | 20-22 | Binary lifecycle exhaustive | Regression case acknowledged later; intro oversimplifies |
| 2 | intro.tex | 27-34 | Mean-field derived from viability | Detection model assumed, not derived |
| 3 | framework.tex | 44-85 | Capacity baseline = mean | Circular with prop:detection-derivation |
| 4 | framework.tex | 3-42 | Sword is unique threat class | Coalitions, uncertainty, stochasticity excluded |
| 5 | framework.tex | 222-276 | Lyapunov function exists under sword | Not proven for adversarial dynamics |
| 6 | results.tex | 5-29 | Forcing cost unbounded | **REINFORCED** — positive floor + pointwise DI |
| 7 | results.tex | 31-60 | Pre-sword not stable | **REINFORCED** — "bet, not resolution" |
| 8 | meanfield.tex | 75-100 | Phase transition = Ū shift | King can shift τ independently |
| 9 | calculus.tex | 125-143 | Detection optimal under finite bandwidth | Proof sketch, not proof |
| 10 | applications.tex | 111-166 | Shang Yang reforms = submartingale | Irreversibility stipulated; centralisation index undefined |
| 11 | applications.tex | 174-195 | Qin existence proof | U_r = 0 unfalsifiable for historical systems |
| 12 | discussion.tex | 60-72 | Pawn→sword at w=0 irreversible | **UNRESOLVED** — reverse direction not addressed |
| 13 | conclusion.tex | 7-8 | Mean-field claim | No thermodynamic limit justification |
| 14 | fields2022.tex | 183-229 | Hausdorff dim 2 for agents | Agents are not random curves; dim 2 stipulated |
| 15 | fields2022.tex | 661-676 | L ≤ T prohibits thermo limit | L = T identity unjustified |
| 16 | threebody.tex | 61-78 | λ₁ → 0 for generic IC | "Generic" never formalised |
| 17 | threebody.tex | 501-523 | Free stability impossible (ū* > 0) | Kakeya sufficient not necessary |
| 18 | govfi.tex | 1103-1112 | Full observability eliminates swords | Observable ≠ controllable |
| 19 | zhongxian.tex | 209-233 | Mean guanxi level as threshold | Guanxi not quantifiable as scalar |
| 20 | second_sex.tex | 52-76 | Transcendence fractions measure phase | Author-assigned data |
| 21 | three_li.tex | 159-189 | Three agents = same fixed point | Fixed points differ; uniqueness unproven |
| 22 | three_li.tex | 254-282 | Factorisation → smooth recognition | Criterion not operationalised |

### STRUCTURAL (19 total, not listed individually — see Phase 1 agent outputs)

### COSMETIC (6 total — see Phase 1 agent outputs)

---

## Verdict

The paper is **structurally sound**. The formal infrastructure (axioms → definitions → theorems → proofs) holds together with zero compilation errors and zero dangling references. The binary lifecycle theorem and the flow-cut duality are internally rigorous. The three main formal results — `thm:lifecycle`, `thm:paradox`, `thm:flowcut` — are proven from their stated premises without circular dependencies.

The vulnerabilities cluster around the **interpretive layer**: the claim that "the sword IS the mean" (not merely "the sword is a threshold function of the actuation distribution"). This claim rests on a proof sketch (`prop:detection-derivation`) with a circular forward reference, no thermodynamic limit argument, and an unacknowledged king-driven channel. These do not break the formal results, but they do weaken the paper's central slogan.

The fresh-eyes scan reveals that the **main text is not self-contained**: it depends on forward references within its own chapters and on appendix material for three substantive claims. A reader going from intro to conclusion would encounter undefined concepts in the Framework chapter that are only resolved in Discussion or Calculus.
