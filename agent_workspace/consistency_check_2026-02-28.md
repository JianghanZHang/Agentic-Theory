# Self-Symbolic Consistency Check — 2026-02-28 (v3 FINAL)

**Central claim**: The sword is the mean field; viability maintenance is a mean-field phenomenon.

**Previous checks**: v1 (2026-02-27), v2 (2026-02-28 interim).
**This check**: All 5 phases complete. Deep Phase 2 cross-validation across all 15 chapter files.

## Summary

| Category | Count |
|----------|-------|
| LOAD-BEARING tensions | 8 (0 reinforced, 6 unresolved, 2 contradicted) |
| Time-axis issues | 10 (1 BREAKING, 7 DRIFT, 2 HARMLESS) |
| Unresolved confusions (fresh-eyes) | 7 |
| Symbolic issues | 4 (2 critical notation, 1 high notation, 1 colour) |
| Citation integrity | Perfect (34/34) |
| Reference integrity | 0 dangling, 14 orphan labels |

**Critical takeaway**: The core theorems (Binary lifecycle, Fixed-point impossibility, Perpetual elimination) are **logically independent** of the most vulnerable quantitative claims (mean-field threshold, capacity formula, detection biconditional). The qualitative framework survives; the quantitative mean-field interpretation has gaps.

---

## Critical Findings (requires action)

### LOAD-BEARING + CONTRADICTED

**T5. Binary lifecycle proof gaps** (`results.tex:16-25`)
- Claim: "Condition (2) is controlled by the king (he can always look)"; "the king must act (viability axiom)."
- **Contradiction 1**: The thesis's own Xiao He example (`framework.tex:620-634`, `meanfield.tex:97-101`) demonstrates a *holder* manipulating condition (2) by self-blunting below the detection threshold. The proof says condition (2) is king-controlled, but the mean-field theorem shows it has finite bandwidth and can be gamed.
- **Contradiction 2**: `ax:viability` is existential ("there exists a viable path"), not prescriptive ("the king must take it"). The Jiajing example (`applications.tex:88-92`) shows a king who does not act for twenty years.
- **Phase 2 cross-validation** (15 chapters read):
  - 11/15 chapters independently support binary outcomes
  - The calculus chapter provides 3 independent derivations (flow-cut, contact dynamics, neural network)
  - The Fields Medal appendix grounds it in sharpness of phase transitions
  - The Huarong Pass finite instantiation is an exact verifiable model
  - Every historical path (c) attempt (Bi Ma Wen, Fake Thunder, Zhao An, Atlantic abolition) is shown to fail
  - **But**: The proof's step from "the king has motive" to "the king must act" is never closed. The breakpoint mechanism (cor:breakpoint) is a third mechanism not cleanly mapped to (a)/(b). Japan's path (c) at 80+ years is long-lived for something "unstable."
- **Verdict: CONTRADICTED** — the proof has internal counterexamples, though the *conclusion* is strongly supported by independent evidence
- **Repair path**: (i) Formally widen path (a) to include "falling below detection threshold while retaining U_r"; (ii) add a lemma that a detected persistent sword eventually drives the tangential condition to failure; (iii) classify breakpoint installation as a sub-case of path (a)

**T6. R³×R¹ ≠ R⁴ category error** (`fields2022.tex:183-192, 619-679`)
- Claim: Physical spacetime R³×R¹ = statistical lattice R⁴ = upper critical dimension d_c=4, therefore mean-field is exact.
- **Contradiction**: In statistical physics, d_c=4 is four *spatial* lattice dimensions. The Ising model in d=3 (our physical space) has non-mean-field critical exponents (Wilson-Fisher). Wick-rotated Euclidean time is fictitious, not the irreversible biological time the framework insists on (`rem:temporal`). The `threebody` appendix operates entirely in R³.
- **Impact**: The complexity lock theorem (`thm:complexity-lock`) has no proof, only analogy. The P/NP boundary claim collapses.
- **Repair path**: Reframe as a *structural analogy* (already partially done in `rem:time-hypothesis`), not an identification. Acknowledge d=3 spatial ≠ d=4 lattice.

### LOAD-BEARING + UNRESOLVED

**T1. Capacity formula circularity** (`framework.tex:52-73`, `calculus.tex:124-144`)
- `c(e_r) = max(||U_r|| - Ū, 0)` is asserted in `lem:capacity`. The proof forward-references `thm:meanfield`. `thm:meanfield` rests on `eq:detection` (asserted, not derived). No chapter closes the derivation loop.
- **Phase 2 cross-validation**: The circularity (lem:capacity → thm:meanfield → eq:detection → stipulated) is confirmed. The τ discrepancy (capacity uses Ū, detection uses Ū+τ) is partially reconciled in `calculus.tex:139-143` but never formally resolved. The arithmetic mean is never derived from axioms — `ax:massless` says capacity is positional, not that the reference level is the arithmetic mean. No contradiction found. The core theorems (`thm:lifecycle`, `thm:fixedpoint`, `thm:paradox`) are **independent** of `lem:capacity`.
- **Repair path**: Either derive `eq:detection` from `ax:viability` + `ax:massless`, or explicitly flag the detection model as an axiom (not a consequence).

**T2. Sword definition weakening** (`framework.tex:397-412`)
- `def:sword` requires state-dependent `f_r(s,a)∉K`. Every subsequent chapter uses the state-independent `U_r≠∅`. The DI restatement (`rem:sword-di`) preserves the original but is never invoked again.
- **Repair path**: Either update `def:sword` to the simpler form (and note the implied condition), or add a lemma proving equivalence under the framework's assumptions.

**T3. Cheng et al. misattribution** (`threebody.tex:420-432`)
- The poly(n) claim "under spectral gap condition" is the thesis's translation, not Cheng's language. Cheng uses force balance and friction cones.
- **Repair path**: Soften attribution: "Cheng et al. show poly(n) valid modes under force balance; we identify this with λ₁>0 via the grasp Laplacian."

**T4. Detection equation ungrounded** (`meanfield.tex:22-31`)
- `eq:detection` is flagged "in practice" and "valid when detection is threshold-based." This is a modelling assumption, not a theorem.
- **Phase 2 cross-validation**: The biconditional is confirmed stipulated. The spectral gap criterion (`thm:massgap`, `calculus.tex:715-742`) provides a **mathematically rigorous independent alternative** that does not depend on the detection biconditional. `rem:3b-scope` (`threebody.tex:80-89`) explicitly acknowledges the scope boundary. Multiple chapters provide qualitative validation but not derivation.
- **Repair path**: Elevate `eq:detection` to a named assumption/axiom, or derive from `ax:viability` under finite-bandwidth constraint. Consider grounding in thm:massgap (spectral gap as the general criterion, mean-field detection as a sufficient condition).

**T7. Mean-field threshold not derived for applications** (all appendices)
- The arithmetic mean Ū is applied as the operative threshold in structurally heterogeneous systems. `rem:3b-scope` explicitly states mean-field detection fails without a king. Clique amplification (`zhongxian.tex`) shows local structure dominates global mean.
- **Repair path**: State validity conditions for each application or derive modified thresholds for hierarchical systems.

**T8. ρ definitions incompatible across physics backends** (`threebody.tex:1119-1332`)
- Three definitions of ρ that agree at {ρ=1} but diverge during free flight:
  - Backend 1 (tidal coupling ratio): ρ>0 always (gravity never turns off)
  - Backend 2 (contact force ratio): ρ=0 during free flight
  - Kinematic reduction: ρ=0 during free flight
- **Phase 2 cross-validation** (15 chapters read):
  - No chapter outside threebody.tex depends on physics-backend ρ — the main theorems use Ū, ||U_r||, λ₁ only
  - The notation unification remark (`framework.tex:524-531`) references only the abstract F_rep/F_att definition, consistent with switching-surface-only interpretation
  - The force elimination theorem (`thm:3b-force-elim`) provides a candidate resolution (kinematic ρ as canonical) but is never stated as reconciling the three definitions
  - Chain B's controller (`threebody.tex:1263`) implicitly relies on Backend 1's ρ being informative during free flight, which breaks under the kinematic definition
  - The running text at line 1119 says "The order parameter **is** the tidal coupling ratio," contradicting the kinematic resolution
- **Severity**: Medium-high within threebody.tex; low for main results
- **Repair path**: Add a remark explicitly stating (i) tidal ratio is a *proxy*, not the gauge-invariant ρ; (ii) kinematic definition is canonical; (iii) all three agree at {ρ=1}; (iv) Chain B monitors λ₁ directly, using tidal ratio only to predict Σ-crossing.

### BREAKING (time-axis)

**`appendices/threebody.tex` is untracked but `\input`-ed in `main.tex`**
- Any clean checkout from the remote will fail to compile.
- **Fix**: `git add appendices/threebody.tex` and commit.

### Unresolved confusions (fresh-eyes, 14 tested, 7 unresolved)

1. **`K` vs `Viab(K)` ambiguity** (`framework.tex:14-21`): The viability axiom quantifies over `s∈K` but demands the trajectory stay in `Viab(K)`. The relationship between `K` and `Viab(K)` is never stated — are they identical, or is `Viab(K)⊊K`?
2. **Forward-dependent proof** (`framework.tex:67-68`): Proof of Lemma 2.3 invokes Theorem 4.1 (`thm:meanfield`) as justification, two chapters before it is stated.
3. **`TS` notation** (`framework.tex:163`): Tangent bundle `TS` appears once without definition; all nearby notation is explicitly defined.
4. **"Half-sword"** (`framework.tex:599`, `intro.tex:40`): Used as a classification label in tables and prose but no formal definition exists between "sword" and "not a sword."
5. **`||U_r||` norm used before defined** (`framework.tex:56`): Appears in Lemma 2.3 (Ch.2), defined in `meanfield.tex:10-13` (Ch.4) with no forward pointer.
6. **φ/ϕ identity asserted, not proved** (`framework.tex:517-523`): The remark claims the conformal parameter, phase operation, and agentic flow "are aspects of the same map" but provides no proof or worked example.
7. **"Submartingale" used non-standardly** (`applications.tex:111-116`): Applied to a deterministic historical sequence with an added irreversibility condition not in the standard probabilistic definition.

---

## Structural Findings (author's discretion)

### STRUCTURAL tensions

| # | Location | Issue |
|---|----------|-------|
| 1 | `applications.tex:152-164` | Shang Yang paradox "proof" uses "unitary group" on a state space with no Hilbert structure |
| 2 | `applications.tex:294-302` | Force-substitutes-for-water in Triangular Trade: mapping coercion→water is asserted |
| 3 | `huarongdao.tex:139-141` | Cut vertex = free cell is definitionally inverse; acknowledged but asserted as isomorphism |
| 4 | `results.tex:102-105` | U→Umax ⟹ Obs→Obs_max "adjoint process" undefined |
| 5 | `triad.tex:136-142` | `thm:triad(d)` proves local stability, not abrupt global collapse |
| 6 | `calculus.tex:124-144` | Binary fate assumes king has sufficient capacity to enforce elimination |
| 7 | `threebody.tex:420-432` | Generic λ₁→0 for unsupported three-body is asserted, not proved |

### Phase 2 confinement analysis

The most important finding from Phase 2 is the **confinement structure**:

```
Core theorems (results.tex):
  thm:lifecycle, thm:fixedpoint, thm:paradox, cor:breakpoint
  ↓
  Depend ONLY on def:sword (two conditions)
  Do NOT depend on: lem:capacity, thm:meanfield, eq:detection
  ↓
  IMMUNE to T1, T4, T7
```

The vulnerabilities cluster in the **quantitative mean-field interpretation layer**, not the **qualitative viability framework**. The central thesis "the sword is the mean" is vulnerable; the structural results about sword lifecycle are not.

### DRIFT (time-axis)

| # | Location | Issue |
|---|----------|-------|
| 1 | `framework.tex:52-73` | `lem:capacity` proof forward-references `thm:meanfield` (Ch.4 from Ch.2) |
| 2 | `intro.tex:14-17` vs `framework.tex:472-476` | Intro dropped "unique", added finite-bandwidth qualifier; `rem:necessity` still says "unique" |
| 3 | `calculus.tex:146-162` | `rem:flowthms` bullet on "Binary fate" not updated for above-mean restriction |
| 4 | `conclusion.tex:36-37` vs `main.tex:148-151` | Conclusion scopes thesis; abstract does not |
| 5 | `govfi.tex:80,1608` | `K`→`𝒦` rename for damping matrix; notation overlap with viability kernel `K` |
| 6 | `threebody.tex:1573-1684` | Figures on disk but no `\includegraphics` |
| 7 | 13 instances across 6 files | Residual American spellings after British normalisation |

---

## Symbolic Integrity

### Notation (Phase 5a)

| Symbol | Conflict | Severity |
|--------|----------|----------|
| **κ** | Curvature (framework.tex) vs King node (calculus.tex) | ~~CRITICAL~~ → RESOLVED (`rem:notation-unification`) |
| **φ/ϕ** | Conformal parameter vs Phase operation vs Flow function | ~~CRITICAL~~ → RESOLVED (`rem:notation-unification`) |
| **ρ** | Rank function (zhongxian.tex) vs Force ratio (threebody.tex) | ~~HIGH~~ → RESOLVED (`rem:notation-unification`) |
| **ρ** | Three internal definitions within threebody.tex | HIGH — see T8 above |

### References (Phase 5b)
- 0 dangling references
- 14 orphan labels — low severity

### Citations (Phase 5c)
- Perfect 34/34 match

### Theorem dependency chain (Phase 5d)
- DAG is acyclic (no circular dependencies)
- 3 HIGH forward references:
  - `lem:capacity` → `thm:meanfield` (framework.tex → meanfield.tex)
  - `rem:water-metric` → `thm:dumu` (framework.tex → discussion.tex)
  - `ex:xiaohe` → `thm:meanfield` (framework.tex → meanfield.tex)

### Colours (Phase 5e)
- 99.6% consistency
- `govfi.tex:1502`: wrong colour (should be `dao`)

---

## Phase 2 Cross-Validation Detail

### LB-A + LB-D (Capacity circularity + Detection biconditional)

| Chapter | LB-A verdict | LB-D verdict |
|---------|-------------|-------------|
| intro.tex | Neutral | Neutral |
| framework.tex | **Primary locus; circularity confirmed** | Forward-ref dependency |
| results.tex | **Confined** (independent of capacity formula) | **Confined** (independent of detection model) |
| meanfield.tex | τ discrepancy confirmed | **Primary locus; stipulated** |
| calculus.tex | Propagated; partial τ reconciliation | **Spectral alternative** (thm:massgap) |
| huarongdao.tex | Neutral (qualitative) | Neutral (trivial observability) |
| discussion.tex | Neutral | Alternative sword-genesis (prop:binary) |
| threebody.tex | Weakly reinforced (scope acknowledged) | **Explicit scope boundary** (rem:3b-scope) |
| zhongxian.tex | Weakly reinforced (empirical fit) | Neutral |
| fields2022.tex | Weakly reinforced (duality analogy) | Weakly reinforced (sieve precedent) |
| triad.tex | Neutral | Neutral |
| govfi.tex | Neutral | Neutral |
| gaokao.tex | Neutral | Neutral |
| three_li.tex | Neutral | Neutral |
| second_sex.tex | Neutral | Weakly reinforced (qualitative) |

**Both UNRESOLVED. No contradiction found. Core theorems are independent.**

### LB-C (Binary partition exhaustiveness)

| Chapter | Verdict | Key evidence |
|---------|---------|-------------|
| results.tex | UNRESOLVED (proof gap) | "king must act" not derived from ax:viability |
| framework.tex | SUPPORTS + complication | Breakpoint mechanism is 3rd mechanism |
| meanfield.tex | SUPPORTS + gap | Xiao He games finite-bandwidth detection |
| applications.tex | STRONGLY SUPPORTS | Every path (c) attempt fails historically |
| calculus.tex | STRONGLY SUPPORTS | 3 independent derivations of binary partition |
| huarongdao.tex | REINFORCED | Exact finite instantiation |
| second_sex.tex | UNRESOLVED | Hua Mulan: system coexists with sword during war |
| triad.tex | SUPPORTS within domain | Mesh immunity is outside single-king domain |
| fields2022.tex | STRONGLY SUPPORTS | Sharpness of phase transition |
| three_li.tex | REINFORCED | Every path (c) labelled as failure |

**UNRESOLVED — the proof has internal gaps but the conclusion is strongly supported by independent evidence.**

### LB-I (ρ definitions incompatibility)

| Chapter | Verdict | Key evidence |
|---------|---------|-------------|
| framework.tex | Consistent | `rem:notation-unification` references abstract F_rep/F_att only |
| calculus.tex | No conflict | Uses ρ_task (probability distribution), unrelated |
| threebody.tex | **Primary locus** | Line 1119 identifies ρ as tidal ratio; line 1325 redefines kinematically |
| All other chapters | Neutral | No physics-backend ρ used |

**UNRESOLVED — localised to threebody.tex. Main theorems unaffected.**

---

## Comparison with previous checks

| Finding | v1 verdict | v2 interim | v3 final | Change |
|---------|-----------|-----------|----------|--------|
| T1 Capacity formula | REINFORCED | UNRESOLVED | **UNRESOLVED** | Confirmed by deep cross-validation |
| T2 Sword weakening | UNRESOLVED | UNRESOLVED | **UNRESOLVED** | Stable |
| T3 Cheng misattribution | REINFORCED | UNRESOLVED | **UNRESOLVED** | Stable |
| T4 Detection ungrounded | UNRESOLVED | UNRESOLVED | **UNRESOLVED** | Spectral alternative identified |
| T5 Binary lifecycle | UNRESOLVED | CONTRADICTED | **CONTRADICTED** | Confirmed: Xiao He + Jiajing are internal counterexamples to the proof (not the conclusion) |
| T6 Complexity lock | REINFORCED | CONTRADICTED | **CONTRADICTED** | Confirmed: d_c=4 is spatial lattice ≠ spacetime |
| T7 Mean-field for apps | (new) | UNRESOLVED | **UNRESOLVED** | Stable |
| T8 ρ definitions | (new) | (new) | **UNRESOLVED** | New from deep Phase 2; localised to threebody.tex |
| Fresh-eyes | 0 | 3 | **7** | Full Phase 4 returned: 14 tested, 7 unresolved |
| Time-axis | 0 | 1B+7D | **1B+7D** | Stable |
| Notation | 1H | 2C+1H | **2C+1H (all resolved)** | rem:notation-unification covers κ, φ, ρ |

---

## Priority ranking for author

### Tier 1: Fix now (threatens paper integrity)

1. **T5 repair**: Close the proof gap in `thm:lifecycle`. The conclusion is correct (strongly supported by 11/15 chapters), but the proof has internal counterexamples. The fix is surgical: widen path (a) definition, add a lemma for the forcing mechanism.
2. **T6 repair**: Reframe `thm:complexity-lock` as structural analogy, not identification. Acknowledge d=3 spatial ≠ d=4 lattice.
3. **BREAKING**: `git add appendices/threebody.tex`.

### Tier 2: Fix before submission (logical gaps)

4. **T1+T4 joint repair**: Elevate `eq:detection` to a named axiom or derive it. This breaks the circularity and grounds the mean-field interpretation.
5. **T8 repair**: Add a remark reconciling the three ρ definitions in threebody.tex.
6. **Fresh-eyes #1**: Clarify `K` vs `Viab(K)` in the viability axiom — state the relationship explicitly.
7. **Fresh-eyes #3**: Define `TS` at first use, or remove it.
8. **Fresh-eyes #4**: Define "half-sword" formally.
9. **Fresh-eyes #5**: Add forward pointer for `||U_r||` at first use in framework.tex.

### Tier 3: Strengthen (author's discretion)

10. **T2**: Reconcile `def:sword` with its operational usage.
11. **T3**: Soften Cheng et al. attribution.
12. **T7**: Add validity conditions for mean-field threshold in applications.
13. **Fresh-eyes #6**: Prove or weaken the φ/ϕ identity claim.
14. **Fresh-eyes #7**: Fix non-standard "submartingale" usage (either justify the extension or rename).

---

*Report generated by 5-phase self-symbolic consistency check protocol.*
*Phase 1: 7 parallel agents (tension identification)*
*Phase 2: 3 parallel agents (deep cross-validation, 15 chapters each)*
*Phase 3: 1 agent (time-axis, git diff analysis)*
*Phase 4: 1 fresh agent (confusion scan, no prior context — 14 confusions tested, 7 resolved, 7 unresolved)*
*Phase 5: 5 parallel agents (notation, references, citations, theorem deps, colours)*
