# Design Spec — *Toward Interface Elimination in Robotic Manipulation*

**Status:** Draft v1, 2026-04-28
**Source:** Spinoff of `appendices/manipulation.tex` (Appendix J of agentic-theory main manuscript) into a standalone IJRR paper.
**Companion (deferred):** `appendices/catching.tex` (Appendix K) — to be brainstormed separately after this spec is locked.

---

## 1. Identity

| Field | Value |
|---|---|
| **Working title** | *Toward Interface Elimination in Robotic Manipulation: A Five-Phase Architecture from Force to Vision* |
| **Target venue** | IJRR (Int'l J. Robotics Research) — long-form, theory + algorithmic-learning friendly, no strict page limit |
| **Format** | Single full-length article (no companion / no series) |
| **Hedge** | "Toward" carried throughout. Position-style framing acceptable. |
| **Self-containment level** | (γ) Fully self-contained — main manuscript is **not** cited (it is years from publication). All theorems used by manipulation re-stated and re-proved in §2 |

## 2. Submission timeline gates

| Milestone | Gate condition |
|---|---|
| **Theory freeze** | §1–§8 written; §2 proofs verified; spec approved | aiming: as soon as §1–§8 drafted |
| **arXiv v1** | grjl4 fully works **in simulation** (FSM + planner + controller + training + curriculum on Franka with vision in MuJoCo, no real robot yet) |
| **arXiv v2 / IJRR submission** | grjl4 reproduces the simulation result on **real Franka with real vision** under wind |
| **Conclusion section written** | only after IJRR submission gate is met |

The author has **not** committed to a calendar date. arXiv v1 is gated by software, not the clock.

## 3. Hard rules

These rules are **non-negotiable** until the IJRR submission gate is reached:

1. **No experimental claims anywhere in the paper.** Abstract, intro, all section bodies, figure captions: every claim must be theoretical / architectural / formal. When experiments are referenced, only declarative scope ("Stage III exercises the kinematic interface") and future-tense verification statements ("This stage will validate that…") are allowed. No numbers, no plots, no "we demonstrate".
2. **§10 Conclusion is empty until experiments land.** The discussion paragraph at the end of the paper is a placeholder pointing to the staircase plan.
3. **"Toward" stance is consistent everywhere.** No section may slip into completed-tense success language. Reviewer should never infer that experimental validation is finished.
4. **No reference to the agentic-theory main manuscript.** Not as `[in preparation]`, not as `[arXiv:to-appear]`. The paper stands or falls on §2. (Once main is on arXiv, future revisions may cite it for context — not now.)
5. **No Chinese in the body.** Possible exception: a single classical-Chinese line as §1 epigraph if rendered with parallel English translation. To be decided when drafting §1.
6. **No metaphor unless backed by definition.** "Interface elimination" is the one keyword the paper builds — every other metaphor (sword, king, summer insect, golden rope, jade lock, Cook Ding, three-foot tripod) is dropped.

## 4. Section structure

Adopted: **Functional grouping** (Brainstorm proposal 2). Nine main sections + three appendices.

```
§1   Introduction                                              ~1 pg
       └─ thesis: 5-phase architecture + interface-elimination staircase
       └─ optional Chinese epigraph (TBD when drafting)

§2   Framework (γ self-contained)                              ~5 pg
       §2.1  Contact order parameter ρ
       §2.2  Spectral gap λ₁ of contact graph
       §2.3  Switching surface Σ and the two-crossing lemma
       §2.4  Three-term control decomposition (gravity + least-action + spectral kick)
       §2.5  Task-space / null-space decomposition (Khatib-Nakamura grounded)
       §2.6  Bi-level optimization scaffold
       §2.7  Causal observability (partial observability with delay)
       §2.8  Notation table
       (Detailed proofs deferred to Appendix C)

§3   The five-phase cycle                                      ~2 pg
       §3.1  Phase structure (5 phases forced by ρ crossing Σ twice)
       §3.2  Operator algebra T_0..T_4 (joint-space loop)
       §3.3  G-action: discrete reflection group {z→−z, g→−g, F→−F}
              ├─ Definition: G acts on (state, gravity, force)
              └─ Closure under G: 5-phase cycle is G-equivariant
              └─ Sets up Stage III's dual-dribble in §9.3

§4   Hierarchical decomposition                                ~3 pg
       §4.1  Task-space / null-space at each phase (RANK/NULL renamed)
       §4.2  Bi-level structure (force-closure inner, trajectory outer)
       §4.3  The commutator as dexterity measure

§5   Perception under causal observability                     ~2 pg
       §5.1  Cognitive boundary of a wrist-mounted sensor
       §5.2  Observation–action coupling
       §5.3  Information timeliness
       §5.4  Three sensory modalities
       (Stochastic FOV field deferred to Appendix A)

§6   Plan generation and training                              ~3 pg
       §6.1  Plans, feasibility, and the two-level architecture
       §6.2  Training: conditional flow matching with measure-matching reward (MMD-only)
       §6.3  Phase-conditioned MLP (network architecture, summary)
       §6.4  Risk-locked training, sketch of sim-to-real transfer
       (Detailed deployment / inference flow deferred to Appendix B)

§7   Curriculum                                                ~1.5 pg
       §7.1  Four orthogonal axes (layers, count, types, wind)
       §7.2  Adversarial robustness: wind as the sole external perturbation

§8   Sim-to-real bridge                                        ~1.5 pg
       §8.1  What sim-to-real has to transfer (state model, perception, control)
       §8.2  Risk-locked training as the bridge mechanism
       §8.3  Failure modes anticipated (declarative only — no measured numbers)

§9   Experiments: the interface-elimination staircase          ~3 pg [PLACEHOLDER]
       §9.1  Stage I — Force Interface
              (parallel-jaw grasp; gravitational three-body Easter egg → supplementary)
       §9.2  Stage II — Continuous-ρ Interface
              (basketball dribble; three-body in ρ form Easter egg)
       §9.3  Stage III — Kinematic Interface
              (G-dual dribble + juggle; xy-tracked transport)
       §9.4  Stage IV — Visual Interface
              (Franka block stacking under wind, sim → real)

§10  Discussion / Conclusion                                   ~1 pg [EMPTY]

Appendix A  Stochastic FOV field
Appendix B  Detailed training & deployment pipeline
Appendix C  Proofs deferred from §2
```

**Total estimated length:** ~20 pages double-column IEEE-style, comfortable for IJRR.

## 5. Stage naming (Scheme A — interface as primary)

| Old codename | Paper name | Interface state | Task instances |
|---|---|---|---|
| `grjl/` (1.0) | **Stage I — Force Interface** | force F, discrete contact modes | parallel-jaw grasp; gravitational three-body damper (Easter egg) |
| `grjl2/` (2.0) | **Stage II — Continuous-ρ Interface** | smooth ρ = F_rep/F_att (still force-derived) | basketball dribble; three-body in ρ form (Easter egg) |
| `grjl3/` (3.0) | **Stage III — Kinematic Interface** | ρ = \|q̈_z/g + 1\|, no force in interface | dribble + juggle G-dual; xy-trajectory tracked transport |
| `grjl4/` (4.0) | **Stage IV — Visual Interface** | vision + kinematic; pixel in, torque out | Franka block stacking under adversarial wind |

The Stage label always carries the **interface state** as primary (matching the paper's thesis); the **task** appears in italics in subsection titles and figure captions.

Each Stage subsection (§9.1–§9.4) initially contains **only**:
1. A *scope statement* — declarative description of what the stage exercises in the architecture, and what the interface variable is.
2. A *verification claim* in future tense — what this stage will validate once experiments land.
3. (Where applicable) a one-line "Easter egg" remark pointing to the corresponding three-body sub-experiment in supplementary.

No figures, no tables, no numbers until experiments land.

## 6. Terminology

### 6.1 Dropped (do not appear in the paper)

| Main-manuscript term | Reason |
|---|---|
| sword (剑), sword lifecycle, path (a)/(b)/(c) | object is passive in manipulation; lifecycle = 5-phase cycle itself |
| king (κ, 王者) | replaced by *the robot* / *the agent* |
| 夏虫运冰, 顿开金绳, 玉锁, 庖丁解牛, 三足之鼎 | classical metaphors not appropriate for IJRR |
| Chu triad, viability axioms, $U_r$ (autonomous actuation set) | not needed by manipulation |
| Kakeya duality | property of catching (Appendix K material), out of scope |
| Reach(κ) | renamed reachable workspace $\mathcal{W}_{\text{reach}}$ |
| Obs (observation operator) | renamed observation map $h(\cdot)$ |
| RANK/NULL decomposition | renamed task-space / null-space decomposition (Khatib-Nakamura standard) |

Possible exception: a single classical line **may** appear once as a §1 epigraph with parallel English translation, to be decided when drafting §1. No other Chinese in the paper body.

### 6.2 Retained

| Term | Reason |
|---|---|
| ρ (contact order parameter) | physical quantity; name is generic |
| λ₁ (spectral gap of contact graph Laplacian) | standard spectral graph notation |
| Σ (switching surface) | standard hybrid systems notation |
| T_0, T_1, T_2, T_3, T_4 (phase operators) | original to this work; no replacement |
| three-term control decomposition (gravity + least-action + spectral kick) | original to this work |
| bi-level optimization | standard optimization term |
| causal observability | partial observability with delay; explicit reading-bridge in §2.7 |
| **interface elimination** | **the** paper keyword — title and §1 thesis |
| G-action / G-dual | discrete reflection group; standard group-theory language |

## 7. Housekeeping

1. **Codebase not renamed.** Directories `grjl/`, `grjl2/`, `grjl3/`, `grjl4/` keep their current names. Paper's README (or §experiments preamble) provides a one-line mapping `grjl(N) ↔ Stage N`.
2. **Three-body as Easter egg.** Stages I, II, III each contain a celestial three-body sub-experiment that demonstrates universality of the controller. In the paper these are mentioned as one-line remarks pointing to a supplementary section, not in the main flow.
3. **G-action is defined early.** §3.3 introduces the discrete reflection group {z→−z, g→−g, F→−F} so that Stage III's dual-dribble in §9.3 has framework to attach to. Without this, §9.3 would have to introduce the duality ad hoc.

## 8. Out of scope (intentionally)

- **Appendix K (catching) integration.** Decided against in brainstorm. Catching is a sister paper, not part of this manuscript. Kakeya duality is K's centerpiece, not J's.
- **Active perception via RKHS kernel optimization** (current J §5.5). Pushed to Appendix A to keep §5 tight; status remains speculative.
- **Detailed deployment / inference flow** (current J §7.5–§7.6). Pushed to Appendix B.
- **Comparison with prior work / benchmarks.** §1 and §10 will have related-work paragraphs once experiments land; no premature benchmarking.

## 9. Open items (to be resolved before §1 drafting)

| # | Item | When |
|---|---|---|
| O1 | §1 epigraph: include classical-Chinese line or pure English? | when drafting §1 |
| O2 | Exact mathematical re-statement of the two-crossing lemma in §2.3 (must avoid sword/path-a/b/c language) | when drafting §2 |
| O3 | How to phrase "Toward" hedge in abstract without sounding weak | when drafting abstract |
| O4 | Whether to include a system-block diagram in §1 (Franka pipeline overview) | when drafting §1 |

## 10. Companion paper (Appendix K → catching)

Deferred. Rough early read:

- Catching is **more conference-ready** than manipulation (tighter, single capture theorem λ₁ : 0 → 3, hardware platform Flexiv Rizon 4 already named).
- Kakeya duality is K's centerpiece — it should not bleed into J.
- K will require its **own** γ self-contained framework section, since "sword" concept is needed there (object has autonomous actuation = gravity) and we dropped it for J.
- Recommended cadence: lock J's spec → draft J §2 → start K brainstorm in parallel once J §2 is stable.

This will be picked up in a separate brainstorming session.

## 11. Brainstorm provenance

This spec is the outcome of a brainstorming session on 2026-04-28, with the following resolved decisions in order:

1. Q1 (venue) → **(E)** open / not committed at brainstorm start
2. Q2 (thesis) → **A + B** (staircase as method + architecture as contribution)
3. Q3 (title) → **B** *Toward Interface Elimination in Robotic Manipulation: A Five-Phase Architecture from Force to Vision*
4. Q4 (self-containment) → **(γ)** fully self-contained, no main-manuscript cite
5. Q5 (terminology table) → approved
6. Q6 (venue final) → **IJRR** (long-form, no page limit)
7. Q7 (arXiv timing) → not urgent; gated by grjl4 sim-complete
8. Q8 (section structure) → **方案 2** functional grouping
9. Q9 (rules) → conclusion empty; no experimental claims anywhere
10. Q10 (stage naming) → **Scheme A** (interface as primary)
11. Q11 (housekeeping) → no codebase rename; three-body as Easter egg; G-action early in §3
