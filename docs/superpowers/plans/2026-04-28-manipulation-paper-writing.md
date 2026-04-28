# Manipulation Paper Writing Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Spin off `appendices/manipulation.tex` (Appendix J of agentic-theory main manuscript) into a fully self-contained IJRR paper titled *Toward Interface Elimination in Robotic Manipulation: A Five-Phase Architecture from Force to Vision*.

**Architecture:** New isolated LaTeX project at `papers/manipulation/`, independent from the main manuscript. Theory body §1–§8 is freezable now; §9 experiments and §10 conclusion stay as placeholders until grjl4 lands. All theorems re-stated and re-proved in §2 (no main-manuscript citation per spec rule). Appendices A/B/C absorb material that would bloat the main flow (stochastic FOV, deployment pipeline details, deferred proofs).

**Tech Stack:** LaTeX (article class for development; sage IJRR template swap deferred), BibTeX, latexmk, TikZ for the §1 system block diagram.

**Spec reference:** `docs/superpowers/specs/2026-04-28-manipulation-paper-design.md` (v2)

---

## Verification model (paper analog of TDD)

Each substantive task ends with a **spec-compliance check** before commit:

1. **Terminology check:** No dropped term appears in the new text (sword, king, U_r, viability, 夏虫运冰, 顿开金绳, 玉锁, 庖丁解牛, Chu triad, Kakeya, Reach(κ), Obs, RANK/NULL). Retained terms match spec §6.2.
2. **Claim check:** No experimental claim. No completed-tense success language. Future-tense or declarative-architectural language only. (Applies to §1, §9, §10 strictly.)
3. **Self-containment check:** No reference to "the main manuscript", `[in preparation]`, `[arXiv:to-appear]` for the agentic-theory main paper.
4. **Proof location check:** Substantive proofs live in Appendix C, not inline. §2 statements have proofs deferred via `\cref{app:proofs}`.
5. **Notation check:** Every newly-introduced symbol is added to the §2.8 notation table.
6. **Build check:** `latexmk -pdf main.tex` returns 0 with no `Undefined reference` or `Citation undefined` warnings (other than `[CITATION-NEEDED]` placeholders).

When a step says "verify", run all six checks unless a narrower subset is specified.

---

## Phase 0 — Project skeleton

### Task 0.1: Create paper directory and LaTeX scaffold

**Files:**
- Create: `papers/manipulation/main.tex`
- Create: `papers/manipulation/preamble.tex`
- Create: `papers/manipulation/macros.tex`
- Create: `papers/manipulation/bib.bib`
- Create: `papers/manipulation/.gitignore`
- Create directory: `papers/manipulation/sections/`
- Create directory: `papers/manipulation/figures/`
- Create directory: `papers/manipulation/appendices/`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p papers/manipulation/sections
mkdir -p papers/manipulation/figures
mkdir -p papers/manipulation/appendices
```

- [ ] **Step 2: Write `papers/manipulation/main.tex`**

```latex
\documentclass[11pt,letterpaper]{article}
\input{preamble}
\input{macros}

\title{Toward Interface Elimination in Robotic Manipulation:\\
       A Five-Phase Architecture from Force to Vision}
\author{Jianghan Zhang}
\date{}

\begin{document}
\maketitle

\begin{abstract}
% [DRAFT-LATER, after §1 is written]
\end{abstract}

\input{sections/01-introduction}
\input{sections/02-framework}
\input{sections/03-phase-cycle}
\input{sections/04-hierarchical}
\input{sections/05-perception}
\input{sections/06-plan-and-training}
\input{sections/07-curriculum}
\input{sections/08-sim-to-real}
\input{sections/09-experiments}
\input{sections/10-conclusion}

\appendix
\input{appendices/A-stochastic-fov}
\input{appendices/B-deployment-pipeline}
\input{appendices/C-deferred-proofs}

\bibliographystyle{plainnat}
\bibliography{bib}
\end{document}
```

- [ ] **Step 3: Write `papers/manipulation/preamble.tex`**

```latex
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english]{babel}
\usepackage{amsmath, amssymb, amsthm, mathtools}
\usepackage{graphicx}
\usepackage{tikz}
\usepackage{booktabs}
\usepackage{enumitem}
\usepackage{cleveref}
\usepackage[round,authoryear]{natbib}
\usepackage{hyperref}

\theoremstyle{plain}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}

\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{remark}[theorem]{Remark}
\newtheorem{example}[theorem]{Example}
```

- [ ] **Step 4: Write `papers/manipulation/macros.tex` with notation symbols**

```latex
% Order parameter and switching
\newcommand{\rcontact}{\rho}
\newcommand{\swsurf}{\Sigma}
\newcommand{\specgap}{\lambda_1}

% Workspaces and observation
\newcommand{\Wreach}{\mathcal{W}_{\mathrm{reach}}}
\newcommand{\obsmap}{h}

% Phase operators
\newcommand{\phaseop}[1]{T_{#1}}

% RLMD risk lock
\newcommand{\risk}{\hat{R}}
\newcommand{\rlock}{\delta}

% Generic placeholders
\newcommand{\todo}[1]{\textcolor{red}{[TODO: #1]}}
\newcommand{\citep}[1]{[CITATION-NEEDED: #1]} % temp until bib populated
```

- [ ] **Step 5: Write `papers/manipulation/.gitignore`**

```
*.aux
*.log
*.out
*.toc
*.fdb_latexmk
*.fls
*.synctex.gz
*.bbl
*.blg
*.pdf
```

- [ ] **Step 6: Create empty section stub files**

For each of the 14 section/appendix files referenced in `main.tex`, create an empty file with a single `\section` (or `\subsection` for appendices) header line.

```bash
for f in 01-introduction 02-framework 03-phase-cycle 04-hierarchical \
         05-perception 06-plan-and-training 07-curriculum 08-sim-to-real \
         09-experiments 10-conclusion; do
  echo "% $f" > papers/manipulation/sections/$f.tex
done

for f in A-stochastic-fov B-deployment-pipeline C-deferred-proofs; do
  echo "% $f" > papers/manipulation/appendices/$f.tex
done
```

Add a single `\section{...}` header line in each file matching the spec's section title.

- [ ] **Step 7: Commit**

```bash
git add papers/manipulation/
git commit -m "scaffold: manipulation paper LaTeX project skeleton"
```

---

### Task 0.2: Verify the build

**Files:**
- Verify: `papers/manipulation/main.pdf` builds

- [ ] **Step 1: Run latexmk**

```bash
cd papers/manipulation && latexmk -pdf main.tex
```

Expected: PDF produced. Warnings about empty bibliography and undefined references are fine; **no errors**.

- [ ] **Step 2: Open PDF and verify front matter**

PDF should show: title, author, empty abstract, empty section headers (matching spec section list), no body content yet.

- [ ] **Step 3: Document build command in a README**

Create `papers/manipulation/README.md`:

```markdown
# Manipulation Paper (IJRR spinoff of Appendix J)

## Build

```bash
cd papers/manipulation
latexmk -pdf main.tex
```

## Codebase mapping

The four experimental stages reference codebase directories at the
agentic-theory repo root:

- Stage I  — Force Interface          ↔ `grjl/`
- Stage II — Continuous-ρ Interface   ↔ `grjl2/`
- Stage III — Kinematic Interface     ↔ `grjl3/`
- Stage IV — Visual Interface         ↔ `grjl4/`

Codebase directories retain their original names per spec.
```

- [ ] **Step 4: Commit**

```bash
git add papers/manipulation/README.md
git commit -m "docs: add manipulation paper build instructions and codebase mapping"
```

---

## Phase 1 — Notation table (§2.8)

Notation must come first because every other subsection consumes it.

### Task 1.1: Draft §2.8 notation table

**Files:**
- Modify: `papers/manipulation/sections/02-framework.tex`
- Modify: `papers/manipulation/macros.tex` (add any newly-discovered symbols)

**Spec reference:** Spec §4 §2.8 ("Notation table"); §6.2 ("Retained" terminology).

- [ ] **Step 1: Draft the notation subsection**

Open `02-framework.tex`. Add a `\subsection{Notation}\label{sec:notation}` block at the **end** of the file (it belongs at the end of §2 in the paper but is written first in our process). Include a `tabular` listing every symbol the paper will use:

| Symbol | Meaning | First introduced |
|---|---|---|
| ρ | Contact order parameter | §2.1 |
| Σ | Switching surface {ρ = 1} | §2.3 |
| λ₁ | Spectral gap of contact graph Laplacian | §2.2 |
| g(x,u) | Margin function (positive = safe) | §6.4 |
| h(·) | Observation map | §2.7 |
| 𝒲_reach | Robot reachable workspace | §2.7 |
| T₀..T₄ | Phase operators (pick/load/use/unload/place) | §3.2 |
| G | Reflection group {z↦−z, g↦−g, F↦−F} | §3.3 |
| π_φ | Velocity-field policy (CFM-trained) | §6.2 |
| A_ψ | Actuator residual net | §6.4 / §8.2 |
| δ | Risk-lock threshold (RLMD) | §6.4 |
| 𝓡̂ | Soft-surrogate failure probability | §6.4 |

(Subsequent tasks may extend this table when introducing new symbols. The introducing task must update both this table and `macros.tex`.)

- [ ] **Step 2: Spec-compliance check**

Verify (1) terminology: no dropped term appears; (2) all symbols have macro definitions in `macros.tex`.

- [ ] **Step 3: Build**

```bash
cd papers/manipulation && latexmk -pdf main.tex
```

Expected: build succeeds, notation table appears in PDF.

- [ ] **Step 4: Commit**

```bash
git add papers/manipulation/sections/02-framework.tex papers/manipulation/macros.tex
git commit -m "framework: §2.8 notation table"
```

---

## Phase 2 — §2 Framework (γ self-contained)

All eight subsections of §2 are written in the order they appear. Each ends with proof statements deferred to Appendix C; only the **statements** of theorems live in §2.

### Task 2.1: §2.1 Contact order parameter ρ

**Files:**
- Modify: `papers/manipulation/sections/02-framework.tex`
- Possibly modify: `papers/manipulation/appendices/C-deferred-proofs.tex`

**Spec reference:** Spec §4 §2.1.

**Required content (declarative outline):**

- One paragraph motivating ρ as the **interface variable** the paper builds (without yet using "interface elimination" — that lands in §1).
- Definition: ρ = (contact force normal to surface) / (force required for static equilibrium); i.e., ρ ∈ [0, ∞), ρ = 1 is the static-equilibrium threshold, ρ < 1 means slipping/no-contact, ρ > 1 means firm contact.
- Two grounding citations: ρ generalizes the contact-mode indicator used in hybrid systems literature (Brogliato 2016 or similar), and the friction-cone-margin literature (Murray, Li, Sastry 1994).
- A single example (parallel-jaw gripper grasping a box): write down ρ explicitly in terms of grip force and weight.
- No theorems in this subsection.

- [ ] **Step 1: Draft text** following the outline above (target length: 1 page).

- [ ] **Step 2: Spec-compliance check**

  - Terminology: no dropped term.
  - Claim: no experimental claim (the example is illustrative, not a result).
  - Self-containment: no reference to main manuscript.
  - Notation: ρ already in §2.8 notation table; if a new symbol appears (e.g., friction coefficient μ), add it.

- [ ] **Step 3: Build**

```bash
cd papers/manipulation && latexmk -pdf main.tex
```

Expected: build succeeds, §2.1 renders.

- [ ] **Step 4: Commit**

```bash
git add papers/manipulation/sections/02-framework.tex \
        papers/manipulation/macros.tex
git commit -m "framework: §2.1 contact order parameter ρ"
```

---

### Task 2.2: §2.2 Spectral gap λ₁ of the contact graph

**Files:**
- Modify: `papers/manipulation/sections/02-framework.tex`

**Required content:**

- Define the **contact graph** $G_c$: nodes = bodies in contact; edges weighted by contact stiffness (or equivalently, contact-force magnitudes).
- Define the **Laplacian** $L_c = D - W$ in the standard spectral-graph sense.
- Define $\lambda_1$ as the second-smallest eigenvalue (Fiedler value), which for our case is the algebraic connectivity of the contact subgraph.
- State the **interpretation lemma** (proof in App C): $\lambda_1 = 0$ iff the contact graph is disconnected (i.e., at least one body is unsupported); $\lambda_1 > 0$ iff every body is part of a connected support structure.
- Cite spectral graph theory (Chung 1997).
- One example: the contact Laplacian of a 2-block stack — write out $L_c$ explicitly; show $\lambda_1 > 0$.

- [ ] **Step 1: Draft text and lemma statement** (target: 1 page).
- [ ] **Step 2: Add proof skeleton to `appendices/C-deferred-proofs.tex`**

```latex
\subsection{Proof of \cref{lem:spec-gap-interp}}
% [PROOF-DRAFT]: standard result; cite Chung 1997 Thm 1.1.
% Sketch:
% (⇐) ...
% (⇒) ...
```

- [ ] **Step 3: Spec-compliance check.**
- [ ] **Step 4: Build.**
- [ ] **Step 5: Commit.**

```bash
git commit -m "framework: §2.2 spectral gap λ₁"
```

---

### Task 2.3: §2.3 Switching surface Σ and the two-crossing lemma

**Files:**
- Modify: `papers/manipulation/sections/02-framework.tex`
- Modify: `papers/manipulation/appendices/C-deferred-proofs.tex`

**Required content:**

- Define the **switching surface** $\Sigma = \{\rho = 1\}$ in the ρ-state space.
- State the **two-crossing lemma**: any valid pick-place trajectory must cross Σ exactly twice — once upward (contact establishment) and once downward (contact release). (Spec hard rule: this lemma must NOT use sword/path-a/b/c language. Re-derive purely from continuity of ρ + the boundary conditions of a pick-place task: object initially at rest on a passive support, finally at rest on a different passive support.)
- Proof: by continuity and intermediate value theorem; deferred to App C.
- Corollary: this two-crossing structure forces the 5-phase decomposition that follows in §3.

- [ ] **Step 1: Draft text + lemma statement.**
- [ ] **Step 2: Write the proof in App C.** (Concrete enough that a future agent can fill prose: continuity of ρ as a function of time; boundary conditions $\rho(0) < 1$ and $\rho(T) < 1$; any continuous path that passes through $\rho > 1$ must cross $\rho = 1$ an even number of times; minimum is 2.)
- [ ] **Step 3: Spec-compliance check** — particular emphasis on **no sword language**.
- [ ] **Step 4: Build.**
- [ ] **Step 5: Commit.**

```bash
git commit -m "framework: §2.3 switching surface Σ and two-crossing lemma"
```

---

### Task 2.4: §2.4 Three-term control decomposition

**Files:**
- Modify: `papers/manipulation/sections/02-framework.tex`

**Required content:**

- State the three-term decomposition of any optimal pick-place control input: $u = u_g + u_a + u_s$ where $u_g$ is the gravity-compensation term, $u_a$ is the least-action (interior) term, and $u_s$ is the spectral-kick (boundary) term active only at Σ-crossings.
- Cite Pontryagin's Maximum Principle for the bang-singular structure (Pontryagin et al. 1962; Bryson & Ho 1975).
- State the **decomposition theorem** (proof in App C): for the OCP $\min \int L\,dt + \Psi(x_T)$ subject to the contact constraint, the optimal control admits the three-term form, with $u_s$ supported on $\{t : x(t) \in \Sigma\}$.
- Remark: phases 1, 5 are pure-singular (no $u_s$); phases 2, 4 are bang (active $u_s$ at Σ); phase 3 is singular with spectral maintenance ($\lambda_1 \ge \varepsilon$ enforced).

- [ ] **Step 1: Draft text + theorem statement.**
- [ ] **Step 2: Write proof skeleton in App C.**
- [ ] **Step 3: Spec-compliance check.**
- [ ] **Step 4: Build.**
- [ ] **Step 5: Commit.**

```bash
git commit -m "framework: §2.4 three-term control decomposition"
```

---

### Task 2.5: §2.5 Task-space / null-space decomposition

**Files:**
- Modify: `papers/manipulation/sections/02-framework.tex`

**Required content:**

- Standard task-space / null-space decomposition of the manipulator Jacobian: given task Jacobian $J(q) \in \mathbb{R}^{m \times n}$ with $m < n$, decompose joint velocity $\dot q = J^+ \dot x + (I - J^+ J)\eta$ where $J^+$ is the pseudo-inverse and $\eta$ parameterizes self-motion.
- Cite Khatib 1987 (operational space formulation), Nakamura 1991 (advanced robotics).
- State that this is what the original "RANK/NULL decomposition" terminology in the source appendix refers to (drop the original name per spec §6.1).
- Define the **commutator** $[J^+, (I - J^+J)] = J^+(I - J^+J) - (I - J^+J)J^+$ as the dexterity measure (with brief geometric interpretation: how much task-space motion is induced by self-motion modulation).

- [ ] **Step 1: Draft text + commutator definition.**
- [ ] **Step 2: Spec-compliance check** — confirm no "RANK/NULL" appears.
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "framework: §2.5 task-space/null-space decomposition"
```

---

### Task 2.6: §2.6 Bi-level optimization scaffold

**Files:**
- Modify: `papers/manipulation/sections/02-framework.tex`

**Required content:**

- Bi-level optimization in standard form: outer level minimizes a trajectory cost over $X(t)$ subject to a continuity equation; inner level maximizes $\lambda_1(L_G(f))$ over contact forces $f$ subject to friction cone constraints.
- Cite Colson et al. 2007 (bilevel optimization survey), Stengle 1973 (bilinear programming).
- Note that this is the standard structure for **force-closure-aware trajectory optimization** in manipulation (cite Murray, Li, Sastry 1994; Park & Lynch 2013 for friction cone).
- State that grasping is the deliberate creation of a contact singularity at the boundary of the inner level — i.e., phase 2 (load) drives the inner solution to a constrained optimum.

- [ ] **Step 1: Draft text.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "framework: §2.6 bi-level optimization scaffold"
```

---

### Task 2.7: §2.7 Causal observability

**Files:**
- Modify: `papers/manipulation/sections/02-framework.tex`

**Required content:**

- Define **causal observability** as a special case of partial observability with delay constraints. Formal: an object $r$ is causally observable at time $t$ if $h(s_t)$ contains information sufficient to estimate $r$'s state with bounded delay $\tau$ such that the resulting estimate enters the controller before the relevant control deadline.
- Distinguish from "full observability" (no delay) and "marginal observability" (delay ≥ control deadline).
- Reading-bridge for reviewers: this is the manipulation analog of **partially observable Markov decision processes** (POMDPs; Kaelbling, Littman, Cassandra 1998) with explicit delay-aware horizon.
- Define the **cognitive boundary** of the wrist-mounted sensor: the set of states $s$ for which the camera FOV intersects the object trajectory before the deadline.

- [ ] **Step 1: Draft text + formal definitions.**
- [ ] **Step 2: Spec-compliance check** — confirm "Reach(κ)" → "𝒲_reach", "Obs" → "h(·)".
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "framework: §2.7 causal observability"
```

---

### Task 2.8: §2.8 Notation table — final pass

**Files:**
- Modify: `papers/manipulation/sections/02-framework.tex`

- [ ] **Step 1: Re-read every §2.x and confirm every symbol appears in the notation table.**

For any missing symbol, add a row.

- [ ] **Step 2: Build and verify table renders cleanly.**
- [ ] **Step 3: Commit.**

```bash
git commit -m "framework: §2.8 notation table — final pass after §2.1–§2.7"
```

---

## Phase 3 — §3 The five-phase cycle

### Task 3.1: §3.1 Phase structure

**Files:**
- Modify: `papers/manipulation/sections/03-phase-cycle.tex`

**Spec reference:** Spec §4 §3.1; sources: `appendices/manipulation.tex` lines 54–105 (current J §1).

**Required content:**

- Use \cref{lem:two-crossing} (from §2.3) to derive the 5-phase decomposition.
- Definition: phases 1 (pick/approach), 2 (load/contact), 3 (use/transport), 4 (unload/release), 5 (place/retreat), with arc types (singular/bang) and ρ/λ₁ ranges per the table in `manipulation.tex:71-87`.
- Remark: phases 1, 5 = pure singular; 2, 4 = bang (Σ active); 3 = singular with spectral maintenance.
- No "sword lifecycle" language — derive purely from §2.3 lemma.

- [ ] **Step 1: Draft text + phase table.**
- [ ] **Step 2: Spec-compliance check** — no path-a/b/c language.
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "phase-cycle: §3.1 phase structure (5 phases)"
```

---

### Task 3.2: §3.2 Operator algebra T₀..T₄

**Files:**
- Modify: `papers/manipulation/sections/03-phase-cycle.tex`

**Sources:** `appendices/manipulation.tex` lines 107–185 (current J §2).

**Required content:**

- Define the five phase operators on the joint-space state: $T_0$ pick, $T_1$ load, $T_2$ use, $T_3$ unload, $T_4$ place. Each has explicit domain/codomain in $(q, \dot q, \rho, \lambda_1)$ space.
- State that $T_4 \circ T_3 \circ T_2 \circ T_1 \circ T_0$ returns the robot to its home configuration (a loop in joint space) but **not** the object to its starting position — irreversibility lives in the object.
- Cite this as the hybrid-systems instance of operator factorization (Lygeros et al. 2003 for hybrid automata).
- Diagram (TikZ): the operator loop as a directed cycle with explicit $\rho$ trace.

- [ ] **Step 1: Draft text + operator definitions.**
- [ ] **Step 2: Draft TikZ figure** in `papers/manipulation/figures/operator-loop.tex` (or inline).
- [ ] **Step 3: Spec-compliance check.**
- [ ] **Step 4: Build.**
- [ ] **Step 5: Commit.**

```bash
git commit -m "phase-cycle: §3.2 operator algebra T₀..T₄"
```

---

### Task 3.3: §3.3 G-action and the dual-dribble setup

**Files:**
- Modify: `papers/manipulation/sections/03-phase-cycle.tex`
- Modify: `papers/manipulation/macros.tex` (G-action symbols)

**Required content (key originality claim):**

- Define the discrete reflection group $G = \{e, g\}$ acting on $(z, \mathbf g_{\mathrm{grav}}, F)$ by $g\colon z \mapsto -z, \mathbf g_{\mathrm{grav}} \mapsto -\mathbf g_{\mathrm{grav}}, F \mapsto -F$.
- State the **G-equivariance lemma** of the 5-phase cycle: the operator factorization $T_4 \circ \cdots \circ T_0$ commutes with $G$ in the sense that $g \cdot (T_4 \circ \cdots \circ T_0)(s) = (T_4 \circ \cdots \circ T_0)(g \cdot s)$.
- Geometric reading: dribbling-down (𝒛↓) and juggling-up (𝒛↑) are the same controller modulo $G$ — sets up Stage III in §9.3.
- Proof: by direct computation of each operator's covariance under $G$. Defer formal proof to App C.

- [ ] **Step 1: Draft text + G-action definition + equivariance lemma statement.**
- [ ] **Step 2: Write proof skeleton in App C.**
- [ ] **Step 3: Spec-compliance check.**
- [ ] **Step 4: Build.**
- [ ] **Step 5: Commit.**

```bash
git commit -m "phase-cycle: §3.3 G-action and equivariance lemma"
```

---

## Phase 4 — §4 Hierarchical decomposition

### Task 4.1: §4.1 Task-space / null-space at each phase

**Files:**
- Modify: `papers/manipulation/sections/04-hierarchical.tex`

**Sources:** `appendices/manipulation.tex` lines 186–260 (current J §3); spec §6.1 rename row.

**Required content:**

- Per-phase specialization of the task-space/null-space decomposition from §2.5:
  - Phases 1, 5: task = end-effector pose, null = redundant joint configuration.
  - Phases 2, 4: task = contact-force vector, null = wrist orientation.
  - Phase 3: task = object pose, null = redundant gripper trajectory.
- Define the **dexterity commutator** instantiated per phase.

- [ ] **Step 1: Draft text + per-phase tables.**
- [ ] **Step 2: Spec-compliance check** — no "RANK/NULL".
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "hierarchical: §4.1 task-space/null-space at each phase"
```

---

### Task 4.2: §4.2 Bi-level structure

**Files:**
- Modify: `papers/manipulation/sections/04-hierarchical.tex`

**Sources:** `appendices/manipulation.tex` lines 261–455 (current J §4).

**Required content:**

- Concrete bi-level structure for the pick-place cycle:
  - Outer: trajectory optimization $\min_{v_\theta} \mathbb{E}\!\left[\int L(X,v)dt + \Psi(X_T)\right]$ subject to continuity equation and $\lambda_1^*(t) \ge \varepsilon$ for all $t \in [t_1, t_4]$.
  - Inner: force closure maintenance $\max_f \lambda_1(L_G(f))$ subject to friction cone $|f_t| \le \mu f_n$.
- Friction modeled as subdifferential inclusion (cite Stewart 2000; Brogliato 2016).
- State that the inner solution feeds back to the outer constraint via the spectral maintenance condition.

- [ ] **Step 1: Draft text + bi-level formulation.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "hierarchical: §4.2 bi-level structure"
```

---

### Task 4.3: §4.3 The commutator as dexterity measure

**Files:**
- Modify: `papers/manipulation/sections/04-hierarchical.tex`

**Required content:**

- Formal claim: the commutator $[J^+, I - J^+ J]$ is a quantitative dexterity measure: its Frobenius norm is bounded by the maximum tangent-space curvature induced by self-motion.
- State the **dexterity bound theorem** (proof in App C).
- Remark: this connects to the classical Yoshikawa manipulability index (Yoshikawa 1985) — our commutator is a more refined invariant.

- [ ] **Step 1: Draft text + theorem statement.**
- [ ] **Step 2: Write proof skeleton in App C.**
- [ ] **Step 3: Spec-compliance check.**
- [ ] **Step 4: Build.**
- [ ] **Step 5: Commit.**

```bash
git commit -m "hierarchical: §4.3 commutator as dexterity measure"
```

---

## Phase 5 — §5 Perception under causal observability

### Task 5.1: §5.1 Cognitive boundary

**Files:**
- Modify: `papers/manipulation/sections/05-perception.tex`

**Sources:** `appendices/manipulation.tex` lines 456–528 (current J §5.1–§5.2).

**Required content:**

- Define the wrist-mounted camera's FOV cone and reachable workspace intersection as the cognitive boundary.
- State that observation is **causally observable** (per §2.7) iff the FOV cone, advanced by sensor latency, intersects the object's trajectory before the relevant control deadline.

- [ ] **Step 1: Draft text + cognitive boundary definition.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "perception: §5.1 cognitive boundary of wrist-mounted sensor"
```

---

### Task 5.2: §5.2 Observation–action coupling

**Files:**
- Modify: `papers/manipulation/sections/05-perception.tex`

**Sources:** `appendices/manipulation.tex` lines 499–549.

**Required content:**

- Coupling: action moves the FOV; therefore observation depends on prior actions (closed-loop perception).
- Formal: define the observation-action operator $\mathcal{O}_t = h(s_t \mid u_{0:t-1})$ and characterize its sensitivity.
- Cite Bajcsy 1988 (active perception); Aloimonos et al. 1988.

- [ ] **Step 1: Draft text.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "perception: §5.2 observation-action coupling"
```

---

### Task 5.3: §5.3 Information timeliness

**Files:**
- Modify: `papers/manipulation/sections/05-perception.tex`

**Sources:** `appendices/manipulation.tex` lines 530–549.

**Required content:**

- Information value decays with time-to-deadline.
- State the **timeliness inequality**: an observation has positive control value iff $\tau_{\mathrm{sensor}} + \tau_{\mathrm{compute}} < \tau_{\mathrm{deadline}}$.

- [ ] **Step 1: Draft text + inequality.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "perception: §5.3 information timeliness"
```

---

### Task 5.4: §5.4 Three sensory modalities

**Files:**
- Modify: `papers/manipulation/sections/05-perception.tex`

**Sources:** `appendices/manipulation.tex` lines 550–573.

**Required content:**

- Vision (camera), proprioception (joint encoders), haptics (joint torques / contact forces).
- Per-modality observation map specialization.
- Note: the **stochastic FOV field** discussion is deferred to Appendix A (per spec §8 Out of scope).

- [ ] **Step 1: Draft text.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "perception: §5.4 three sensory modalities"
```

---

## Phase 6 — §6 Plan generation and training

### Task 6.1: §6.1 Plans, feasibility, two-level architecture

**Files:**
- Modify: `papers/manipulation/sections/06-plan-and-training.tex`

**Sources:** `appendices/manipulation.tex` lines 892–1007 (current J §6).

**Required content:**

- Define a **plan** as an ordered DAG of pick-place operations satisfying the geometric constraints (mortise-tenon mating, layer-stability prerequisites).
- Two-level architecture: upper = MPPI sample over plans (discrete, stochastic); lower = trajectory optimization per plan.
- Cite Williams et al. 2017 (MPPI).

- [ ] **Step 1: Draft text + plan / DAG definition.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "plan-and-training: §6.1 plans and two-level architecture"
```

---

### Task 6.2: §6.2 Training: CFM with measure-matching reward

**Files:**
- Modify: `papers/manipulation/sections/06-plan-and-training.tex`

**Sources:** `appendices/manipulation.tex` lines 1008–1104.

**Required content:**

- Conditional flow matching for the velocity field $v_\theta$ (Lipman et al. 2023).
- The **measure-matching** reward (MMD-only, no shaped reward): match the distribution of policy rollouts to the target distribution of successful trajectories. Cite Gretton et al. 2012 (MMD).
- Explicit claim: no per-step reward engineering; the only training signal is distributional.

- [ ] **Step 1: Draft text + loss formulation.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "plan-and-training: §6.2 CFM with MMD-only reward"
```

---

### Task 6.3: §6.3 Phase-conditioned MLP

**Files:**
- Modify: `papers/manipulation/sections/06-plan-and-training.tex`

**Sources:** `appendices/manipulation.tex` lines 1105–1158.

**Required content:**

- Network architecture: phase-conditioned MLP. Input: $(q, \dot q, \mathrm{phase\_id})$; output: $\dot q$.
- Phase ID is an embedded one-hot of $\{0,1,2,3,4\}$ for $T_0..T_4$.
- Detailed deployment / inference flow deferred to Appendix B.

- [ ] **Step 1: Draft text + architecture summary.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "plan-and-training: §6.3 phase-conditioned MLP"
```

---

### Task 6.4: §6.4 RLMD for sim-to-real transfer (grounded)

**Files:**
- Modify: `papers/manipulation/sections/06-plan-and-training.tex`
- Modify: `papers/manipulation/bib.bib` (add Chow & Ghavamzadeh 2014; Achiam et al. 2017)

**Sources:** `appendices/manipulation.tex` lines 1159–1221.

**Required content:**

- **First sentence**: *"Risk-Locked Mirror Descent (RLMD) is an instance of chance-constrained policy optimization \citep{ChowGhavamzadeh2014, Achiam2017} augmented with curriculum gating."*
- Algorithm body: soft-surrogate $\hat R = \tfrac{1}{N}\sum_i \sigma(-m_i / \beta)$, mirror-descent update on $\hat J(\phi) = \hat R(\phi) + \lambda \hat S(\phi)$ subject to $\hat R \le \delta$.
- **Curriculum gating** is the originality claim: training advances perturbation level $\varepsilon_k \to \varepsilon_{k+1}$ only when the lock has held for several consecutive epochs.
- Actuator residual net $A_\psi$ for sim-to-real.

- [ ] **Step 1: Add bib entries** for Chow & Ghavamzadeh 2014 (Risk-Sensitive and Robust Decision-Making, NeurIPS) and Achiam 2017 (Constrained Policy Optimization, ICML).

```bibtex
@inproceedings{ChowGhavamzadeh2014,
  author = {Chow, Yinlam and Ghavamzadeh, Mohammad},
  title  = {Algorithms for {CVaR} optimization in {MDPs}},
  booktitle = {NeurIPS},
  year   = {2014}
}
@inproceedings{Achiam2017,
  author = {Achiam, Joshua and Held, David and Tamar, Aviv and Abbeel, Pieter},
  title  = {Constrained Policy Optimization},
  booktitle = {ICML},
  year   = {2017}
}
```

- [ ] **Step 2: Draft text** with the grounding sentence as the first line.
- [ ] **Step 3: Spec-compliance check** — confirm grounding sentence, RLMD as branded name, curriculum gating identified as originality claim.
- [ ] **Step 4: Build.**
- [ ] **Step 5: Commit.**

```bash
git commit -m "plan-and-training: §6.4 RLMD grounded in chance-constrained PO"
```

---

## Phase 7 — §7 Curriculum

### Task 7.1: §7.1 Four orthogonal axes

**Files:**
- Modify: `papers/manipulation/sections/07-curriculum.tex`

**Sources:** `appendices/manipulation.tex` lines 1437–1490 (current J §8); spec §4.

**Required content:**

- Four orthogonal axes per spec: stack layers ($L$), block count ($N$), block types ($K_{\mathrm{type}}$), adversarial wind ($F_{\max}$).
- Each axis: range, what it tests, what observable governs it.

- [ ] **Step 1: Draft text + axes table.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "curriculum: §7.1 four orthogonal axes"
```

---

### Task 7.2: §7.2 Wind as the sole external perturbation

**Files:**
- Modify: `papers/manipulation/sections/07-curriculum.tex`

**Sources:** `appendices/manipulation.tex` lines 1491–end.

**Required content:**

- Wind is the only external adversary; without it, the task reduces to pure kinematics.
- Wind couples to $\lambda_1^{\mathrm{eff}} = \lambda_1 - \|F_{\mathrm{wind},\perp}\| / (m_i g)$.
- A tower is stable iff $\lambda_1^{\mathrm{eff}}(i) \ge \varepsilon$ for every block $i$.

- [ ] **Step 1: Draft text + stability criterion.**
- [ ] **Step 2: Spec-compliance check** — no "we demonstrate that wind robustness holds".
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "curriculum: §7.2 wind and stability criterion"
```

---

## Phase 8 — §8 Sim-to-real bridge

### Task 8.1: §8.1 What sim-to-real has to transfer

**Files:**
- Modify: `papers/manipulation/sections/08-sim-to-real.tex`

**Required content:**

- Three transfer concerns: state model (rigid body + contact), perception (camera intrinsics + lighting), control (motor dynamics + latency).
- Where each is addressed in our pipeline.

- [ ] **Step 1: Draft text + transfer table.**
- [ ] **Step 2: Spec-compliance check.**
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "sim-to-real: §8.1 transfer concerns"
```

---

### Task 8.2: §8.2 RLMD as the bridge mechanism

**Files:**
- Modify: `papers/manipulation/sections/08-sim-to-real.tex`

**Required content:**

- Cross-reference §6.4 for the RLMD definition; do not redefine.
- Discuss specifically: how the actuator residual net $A_\psi$ closes the sim-to-real gap concentrated in the actuator channel.
- State that the risk lock $\hat R \le \delta$ is preserved across the sim → real boundary by construction, since $A_\psi$ is constrained in amplitude (safety) and roughness (Nyquist).

- [ ] **Step 1: Draft text.**
- [ ] **Step 2: Spec-compliance check** — no experimental claim about sim-to-real success.
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "sim-to-real: §8.2 RLMD as the bridge mechanism"
```

---

### Task 8.3: §8.3 Anticipated failure modes

**Files:**
- Modify: `papers/manipulation/sections/08-sim-to-real.tex`

**Required content:**

- **Declarative only**: list failure modes the architecture is designed to handle (slippage during transport, mortise-tenon misalignment, wind-induced loss of $\lambda_1^{\mathrm{eff}}$).
- For each, state the architectural component that addresses it.
- **No measured numbers, no claimed success rates.**

- [ ] **Step 1: Draft text + failure-mode table.**
- [ ] **Step 2: Spec-compliance check** — confirm no numbers, no claims of success.
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "sim-to-real: §8.3 anticipated failure modes (declarative)"
```

---

## Phase 9 — §1 Introduction (depends on §2–§8)

### Task 9.1: §1 prose + thesis statement

**Files:**
- Modify: `papers/manipulation/sections/01-introduction.tex`

**Required content:**

- Open with a 1–2 sentence statement of the manipulation problem domain.
- Introduce the **interface elimination** thesis: manipulation pipelines can be staged so that each stage eliminates one layer of interface dependency (force → smoothed force → kinematic → vision).
- State the paper's contributions:
  1. A self-contained five-phase architecture forced by ρ crossing Σ exactly twice.
  2. An interface-elimination staircase (Stages I–IV) as a verification methodology.
  3. RLMD with curriculum gating for sim-to-real transfer.
- Close with paper organization (forward references to §2–§10).

- [ ] **Step 1: Draft text.**
- [ ] **Step 2: Spec-compliance check** — strict on "Toward" hedge; no "we demonstrate that…"; only "we propose / we present / we will validate".
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "intro: §1 prose + thesis"
```

---

### Task 9.2: §1 system block diagram (TikZ)

**Files:**
- Create: `papers/manipulation/figures/pipeline.tex`
- Modify: `papers/manipulation/sections/01-introduction.tex`

**Required content:**

TikZ figure: boxes labeled `Camera`, `Observer h(·)`, `Plan generator`, `Controller v_θ`, `Inverse dynamics 𝒟`, `Franka arm`, with arrows showing the pipeline. Shows the interface variable changing along the way (pixels → poses → torques).

- [ ] **Step 1: Write `figures/pipeline.tex`** as a standalone TikZ picture (with `\input` from `01-introduction.tex`).

```latex
\begin{figure}[t]
\centering
\begin{tikzpicture}[node distance=1.4cm, every node/.style={draw, rectangle, rounded corners, minimum height=0.7cm, minimum width=2.0cm, font=\footnotesize}]
  \node (cam) {Camera};
  \node (obs) [right=of cam] {Observer $h(\cdot)$};
  \node (plan) [right=of obs] {Plan gen.};
  \node (ctrl) [below=of plan] {Controller $v_\theta$};
  \node (id) [left=of ctrl] {Inv.\ dyn.\ $\mathcal{D}$};
  \node (arm) [left=of id] {Franka};
  \draw[->] (cam) -- (obs);
  \draw[->] (obs) -- (plan);
  \draw[->] (plan) -- (ctrl);
  \draw[->] (ctrl) -- (id);
  \draw[->] (id) -- (arm);
  \draw[->] (arm) -- (cam);
\end{tikzpicture}
\caption{Pipeline overview. The architecture forms a closed loop: camera observation $\to$ observer $\to$ plan generation $\to$ controller $\to$ inverse dynamics $\to$ Franka actuation $\to$ scene change $\to$ camera. The interface variable transforms along the loop: pixels $\to$ pose estimates $\to$ joint velocities $\to$ joint torques $\to$ contact wrenches.}
\label{fig:pipeline}
\end{figure}
```

- [ ] **Step 2: Reference the figure** from §1 prose.
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "intro: §1 pipeline overview figure (TikZ)"
```

---

### Task 9.3: Abstract draft

**Files:**
- Modify: `papers/manipulation/main.tex` (abstract block)

**Required content:**

- 150–250 words.
- States: (1) the manipulation problem, (2) the interface-elimination thesis, (3) the five-phase architecture, (4) the staircase methodology, (5) RLMD as the sim-to-real bridge, (6) **future-tense statement that experimental validation is in progress**.
- **No completed-tense success claims.**

- [ ] **Step 1: Draft abstract.**
- [ ] **Step 2: Spec-compliance check** — strict on "Toward" hedge.
- [ ] **Step 3: Build.**
- [ ] **Step 4: Commit.**

```bash
git commit -m "intro: abstract draft (Toward-hedge enforced)"
```

---

## Phase 10 — §9, §10, Appendices A/B/C placeholders

### Task 10.1: §9 Experiments — Stage I–IV scope and verification placeholders

**Files:**
- Modify: `papers/manipulation/sections/09-experiments.tex`

**Required content per Stage subsection (§9.1–§9.4):**

For each Stage:

```latex
\subsection{Stage I — Force Interface}
\label{sec:exp-stage1}

\paragraph{Scope.}
% [DECLARATIVE] What this stage exercises in the architecture.
% Interface: force F, discrete contact modes.
% Tasks: parallel-jaw grasp; gravitational three-body damper (supplementary).

\paragraph{Verification (planned).}
% [FUTURE-TENSE] What this stage will validate once experiments land.
% E.g.: "This stage will validate that the three-term decomposition
% (\cref{thm:three-term}) governs grip force in a discrete-contact regime."

% NO RESULTS, FIGURES, OR TABLES UNTIL EXPERIMENTS LAND.
```

Repeat the same template for Stages II, III, IV with the appropriate interface variable and task descriptions per spec §5.

- [ ] **Step 1: Draft scope and verification paragraphs for all four stages.**
- [ ] **Step 2: Add Easter-egg remark** for Stages I, II, III pointing to a supplementary three-body sub-experiment (one line each).
- [ ] **Step 3: Spec-compliance check** — strict: no figures, no tables, no numbers.
- [ ] **Step 4: Build.**
- [ ] **Step 5: Commit.**

```bash
git commit -m "experiments: Stage I-IV scope and verification placeholders (no results)"
```

---

### Task 10.2: §10 Conclusion placeholder

**Files:**
- Modify: `papers/manipulation/sections/10-conclusion.tex`

**Required content:**

```latex
\section{Discussion and conclusion}
\label{sec:conclusion}

% [PLACEHOLDER, per spec hard rule #2]
% Conclusion will be drafted only after the IJRR submission gate is met
% (grjl4 reproduces simulation result on real Franka with vision under wind).
% Until then, this section is intentionally empty.
```

- [ ] **Step 1: Write the placeholder block.**
- [ ] **Step 2: Build.**
- [ ] **Step 3: Commit.**

```bash
git commit -m "conclusion: §10 placeholder per spec hard rule"
```

---

### Task 10.3: Appendix A — Stochastic FOV field

**Files:**
- Modify: `papers/manipulation/appendices/A-stochastic-fov.tex`

**Sources:** `appendices/manipulation.tex` lines 574–891 (current J §5.5).

**Required content:**

- Move the entire stochastic-FOV-field discussion from the source appendix into Appendix A.
- Mark as speculative: include a one-paragraph note that this section presents an active-perception extension whose empirical validation is left to future work.

- [ ] **Step 1: Port content from source.**
- [ ] **Step 2: Apply terminology de-metaphorization** per spec §6.1.
- [ ] **Step 3: Spec-compliance check.**
- [ ] **Step 4: Build.**
- [ ] **Step 5: Commit.**

```bash
git commit -m "appendix: A stochastic FOV field (ported from source)"
```

---

### Task 10.4: Appendix B — Detailed deployment pipeline

**Files:**
- Modify: `papers/manipulation/appendices/B-deployment-pipeline.tex`

**Sources:** `appendices/manipulation.tex` lines 1222–1436 (current J §7.5–§7.6 deployment + inference flow).

**Required content:**

- Detailed deployment / inference flow: camera image in, torque out.
- Pseudocode for the end-to-end pipeline.
- Latency budget table.

- [ ] **Step 1: Port content from source.**
- [ ] **Step 2: Apply terminology de-metaphorization.**
- [ ] **Step 3: Spec-compliance check.**
- [ ] **Step 4: Build.**
- [ ] **Step 5: Commit.**

```bash
git commit -m "appendix: B detailed deployment pipeline"
```

---

### Task 10.5: Appendix C — Deferred proofs

**Files:**
- Modify: `papers/manipulation/appendices/C-deferred-proofs.tex`

- [ ] **Step 1: Consolidate proof skeletons** drafted in Tasks 2.2, 2.3, 2.4, 3.3, 4.3 into Appendix C.
- [ ] **Step 2: Each proof has a section header** matching the theorem label, and a `\proof` block.
- [ ] **Step 3: Where proof skeleton is incomplete, mark `\todo{...}` with a precise description of what is missing.**
- [ ] **Step 4: Spec-compliance check.**
- [ ] **Step 5: Build.**
- [ ] **Step 6: Commit.**

```bash
git commit -m "appendix: C consolidated deferred proofs"
```

---

## Phase 11 — Final pass

### Task 11.1: Spec-compliance audit

**Files:**
- Read: every file in `papers/manipulation/sections/` and `papers/manipulation/appendices/`

- [ ] **Step 1: Run terminology check** — grep for dropped terms and confirm zero hits:

```bash
cd papers/manipulation
for term in "sword" "lifecycle" "king" "Reach(\\\\kappa)" "Obs(" "RANK/NULL" \
            "夏虫" "金绳" "玉锁" "庖丁" "Chu triad" "Kakeya" "viability" "U_r"; do
  hits=$(grep -rn "$term" sections appendices main.tex 2>/dev/null | wc -l)
  echo "$term: $hits"
done
```

Any non-zero hit is a violation; fix and re-commit.

- [ ] **Step 2: Run claim check** — grep for completed-tense success language:

```bash
grep -rn "we demonstrate\|we show that.*succeeds\|results show\|achieves a success rate\|outperforms" sections appendices
```

Expected: zero hits. If any exist, rephrase to future-tense or declarative.

- [ ] **Step 3: Run self-containment check** — confirm no main-manuscript reference:

```bash
grep -rn "main manuscript\|in preparation\|arXiv:to-appear\|companion paper\|catching paper" sections appendices main.tex
```

Expected: zero hits.

- [ ] **Step 4: Run build check** — ensure clean build:

```bash
latexmk -pdf main.tex 2>&1 | grep -E "Warning|Error" | grep -v "[CITATION-NEEDED]"
```

Expected: no Warning or Error lines (CITATION-NEEDED placeholders are tolerated until bib is fully populated).

- [ ] **Step 5: Run notation check** — every symbol used in body has a row in §2.8 table.

Manually scan §2.8 table against actual usage. Add missing rows.

- [ ] **Step 6: Commit any fixes.**

```bash
git commit -m "compliance: spec audit pass — terminology, claims, self-containment, notation"
```

---

### Task 11.2: Theory-freeze commit

**Files:**
- All of `papers/manipulation/`

- [ ] **Step 1: Tag the theory freeze.**

```bash
git tag manipulation-paper-theory-frozen
```

This tag marks the §1–§8 theory body as frozen per spec hard rule. Subsequent edits to §1–§8 require explicit unfreeze rationale (e.g., reviewer feedback) — §9 and §10 may continue rolling.

- [ ] **Step 2: Push tag.**

```bash
# Only when ready
# git push origin manipulation-paper-theory-frozen
```

(Push is deferred to user discretion.)

---

## Self-review (executed before user review)

Spec coverage scan:

| Spec section | Covered by task |
|---|---|
| §1 Identity (title, venue, hedge, γ self-containment) | Task 0.1 (title), 9.1 (hedge in intro), 11.1 (compliance audit) |
| §2 Submission timeline gates | Out of scope for the writing plan (gates are external milestones, not writing tasks) |
| §3 Hard rules | Enforced throughout via verification model + Task 11.1 audit |
| §4 Section structure | Phases 1–10 implement every numbered section and appendix |
| §5 Stage naming (Scheme A) | Task 10.1 (Stage I–IV subsections) |
| §6 Terminology drop/retain | Task 11.1 grep audit |
| §7 Housekeeping (no codebase rename, three-body Easter egg, G-action early) | README mapping (Task 0.2), Easter-egg remarks (Task 10.1), G-action in §3.3 (Task 3.3) |
| §8 Out of scope (FOV → A, deployment → B, K paper) | Tasks 10.3, 10.4; K paper not in plan (correct, per spec) |
| §9 Open items O1, O2, O3 | O1 epigraph: surfaced when drafting §1 (Task 9.1, optional); O2 two-crossing lemma phrasing: handled in Task 2.3; O3 abstract phrasing: handled in Task 9.3 |
| §10 Companion paper | Out of scope for this plan (correct, per spec deferral) |
| §12 Changelog (v2 adjustments) | RLMD grounding enforced in Task 6.4; pipeline figure in Task 9.2; rules unchanged |

No gaps identified.

Placeholder scan: each task contains either complete code/text blocks or a precise drafting outline. The outlines (e.g., "draft 1 page covering ρ definition, motivation, parallel-jaw example") are deliberately not pre-written prose — that is the work the executor performs. They are precise enough that an executor knows exactly what to produce.

Type/symbol consistency: phase operators consistently named `T₀..T₄` (not `T_1..T_5`); risk lock consistently `δ`; soft-surrogate failure rate consistently `R̂`; macros centralized in `macros.tex` with `\rcontact`, `\specgap`, `\swsurf`, `\Wreach`, `\obsmap`, `\phaseop`, `\risk`, `\rlock`. No drift across tasks.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-28-manipulation-paper-writing.md`. Two execution options:

**1. Subagent-Driven (recommended)** — A fresh subagent per task, review between tasks, fast iteration. Strong fit for this plan because each task is mostly self-contained and the spec compliance check is mechanical.

**2. Inline Execution** — Execute tasks in this session using executing-plans. Lower overhead but the user must context-switch between writing prose and reviewing.

For the **start of §2** that the user specifically requested (task `b` from the brainstorm session), the natural unit is **Phase 1 (§2.8 notation table) + Task 2.1 (§2.1 contact order parameter)**. After those land, the remaining §2 subsections follow the same rhythm.
