# FONC/SOSC Section: Prior and Posterior Riccati

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the FONC/SOSC framework to the Riccati section (riccati.tex), establishing four connections that the paper currently states separately: (1) GN-exactness for the centroidal model, (2) GP-LCB avoidance of the sensitivity problem, (3) prior/posterior Hessian interpretation, (4) holonomy convergence to the FONC = SOSC regime.

**Architecture:** Expand `sections/riccati.tex` (currently 48 lines / 1 remark) with an introduction paragraph, two remarks, and one labeled equation (~60 lines). Add two one-sentence cross-references in `sections/articulated.tex` to connect the existing GN-exactness and policy-level BO passages back to the new framework. Add one bibliography entry for Frey et al.

**Tech Stack:** LaTeX (xelatex), cleveref for cross-references.

---

## Dependency Graph

```
Task 1 (bibliography: FreyDiffMPC)  ──┐
Task 2 (riccati.tex: 60-line insert) ──┼──→ Task 4 (compile + verify)
Task 3 (articulated.tex: 2 sentences) ─┘
```

Tasks 1–3 are fully independent (different files). Task 4 depends on all three.

---

## File Map

| File | Line | Action |
|------|------|--------|
| `bibliography.tex` | Before `\end{thebibliography}` | Add `FreyDiffMPC` entry (6 lines) |
| `sections/riccati.tex:47` | After `\end{remark}` | Insert intro paragraph + `rem:fonc-sosc` + `rem:fonc-recycle` (~60 lines) |
| `sections/articulated.tex:792` | After "not an approximation." | Insert 2-line FONC=SOSC cross-reference |
| `sections/articulated.tex:807` | After `(\cref{prop:gp-regret}).` | Insert 2-line GP-avoids-SOSC cross-reference |

All paths relative to `/Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory/`.

---

## Mathematical Framework (reference)

**Core decomposition (stage-wise Riccati):**

Q^SOSC_uu = [ℓ_uu + f_u^T V'_xx f_u] + λ*_{t+1}^T ∇²_uu f_t
           = Q^FONC_uu (≥ 0 always)  + dynamics curvature (no sign)

Same for Q_xx, Q_ux with corresponding second derivatives.

**Key facts used:**
1. At optimality, V'_x = λ*_{t+1} (costate = value gradient)
2. FONC (iLQR): drops dynamics curvature → Q_uu^FONC ≥ 0 unconditionally
3. SOSC (DDP): retains dynamics curvature → needs Q_uu^feas = Q_uu - Q_ux Q_xx^{-1} Q_xu ≻ 0 (reachable subspace)
4. Linear dynamics: ∇²f = 0 → FONC = SOSC identically
5. Frey et al. Thm 2: QP and NLP sensitivities coincide iff Lagrangian Hessian exact (i.e., ∇²f = 0)

**Connections to existing paper content:**
- "GN approximation is exact" (articulated.tex:789-792) = FONC = SOSC for f_xx = 0
- "policy-level Bayesian optimization" (articulated.tex:797-807) = GP avoids ∂z*/∂θ
- "prior → posterior" (riccati.tex:14-15) = measure-level analogue of Hessian prior/posterior
- "H(f) → 0" (prop:student-convergence, optimal-cycle.tex:149) = convergence to FONC = SOSC regime
- "two-level contraction" (prop:unconditional, optimal-cycle.tex:547) = holds without SOSC

---

## Task 1: Add Bibliography Entry

**Files:**
- Modify: `bibliography.tex` — insert before `\end{thebibliography}`

- [ ] **Step 1: Insert FreyDiffMPC entry**

Insert before the `\end{thebibliography}` line:

```latex

\bibitem{FreyDiffMPC}
J.~Frey, K.~Baumg\"artner, G.~Frison, D.~Reinhardt,
J.~Hoffmann, L.~Fichtner, S.~Gros, and M.~Diehl,
Differentiable nonlinear model predictive control,
\emph{arXiv preprint arXiv:2505.01353}, 2025.
```

---

## Task 2: Expand riccati.tex with FONC/SOSC Framework

**Files:**
- Modify: `sections/riccati.tex` — insert after line 47 (`\end{remark}`)

**Context:** riccati.tex is currently 48 lines containing one remark on GPI and Riccati compression. The existing remark (lines 13-16) already uses prior/posterior language for the Boltzmann measure. The new content extends this prior/posterior framing to the Hessian level.

**Forward references:** The new content references labels defined in files input AFTER riccati.tex (articulated.tex). These are forward references, resolved on xelatex second pass. Labels used: `alg:riccati-eval` (optimal-cycle.tex, backward ref OK), `alg:recycle` (optimal-cycle.tex, backward ref OK), `alg:quadruped` (articulated.tex, forward ref), `alg:action-rate` (articulated.tex, forward ref), `prop:unconditional` (optimal-cycle.tex, backward ref OK), `prop:student-convergence` (optimal-cycle.tex, backward ref OK).

- [ ] **Step 1: Insert the FONC/SOSC content block**

Insert the following after line 47 (`\end{remark}`), before the end of file:

```latex

\medskip\noindent\textbf{FONC and SOSC: prior and posterior Riccati.}
The Boltzmann prior-to-posterior conversion above
(uniform measure $\to$ $\pi \propto e^{-J/\varepsilon}$)
has an exact counterpart in the backward pass.
Two variants of the Riccati recursion arise, distinguished by
their treatment of dynamics curvature---the second-order terms
$V'_x \cdot f_{xx}$ in the Q-function expansion.

\begin{remark}[FONC and SOSC backward passes]
\label{rem:fonc-sosc}
The DDP backward pass expands
$Q(x_t, u_t) = \ell_t + V_{t+1}(f_t)$ to second order.
The $Q_{uu}$ block decomposes as
\begin{equation}\label{eq:fonc-sosc}
Q_{uu}^{\mathrm{SOSC}}
= \underbrace{\ell_{uu} + f_u^\top V'_{xx}\, f_u}_{%
    Q_{uu}^{\mathrm{FONC}} \;\succeq\; 0}
  \;+\; \underbrace{\lambda^{*\top}_{t+1}\,\nabla^2_{uu} f_t}_{%
    \text{dynamics curvature}},
\end{equation}
where $V'_x = \lambda^*_{t+1}$ at optimality
(similarly for $Q_{xx}$ and $Q_{ux}$).
The \emph{first-order necessary conditions} (FONC) backward pass
drops the dynamics curvature, recovering
iLQR~\cite{TassaErezTodorov,MastalliCrocoddyl}:
$Q_{uu}^{\mathrm{FONC}} \succeq 0$ unconditionally---a
\emph{prior} on the cost landscape that ignores
how nonlinear the dynamics are.
The \emph{second-order sufficient conditions} (SOSC) backward pass
retains it, updating the prior with the dynamics Lagrangian Hessian
$\lambda^{*\top}\nabla^2 f$---a \emph{posterior} that is
positive-definite only on the dynamically reachable subspace
(the reduced Hessian
$Q_{uu}^{\mathrm{feas}}
= Q_{uu} - Q_{ux}\,Q_{xx}^{-1}\,Q_{xu} \succ 0$).
For \emph{linear} dynamics, $\nabla^2 f = 0$ and the prior
equals the posterior: FONC $=$ SOSC.
Frey et al.~\cite{FreyDiffMPC} prove the converse:
the QP (FONC) and NLP (SOSC) sensitivities
$\partial z^\star/\partial\theta$ coincide \emph{if and only if}
the Lagrangian Hessian is exact---equivalently, $\nabla^2 f = 0$.
For nonlinear dynamics, FONC sensitivities can be
``completely off''~\cite[Section~5.1]{FreyDiffMPC}.
\end{remark}

\begin{remark}[Implications for the re-cycle]
\label{rem:fonc-recycle}
The FONC/SOSC decomposition \eqref{eq:fonc-sosc} has three
consequences for the re-cycle architecture.
\begin{enumerate}[label=(\roman*),nosep]
\item \emph{Centroidal model.}
  The dynamics $\dot x = A(\sigma)\,x + B(\sigma)\,u + c$ is
  affine in $(x, u)$ for frozen contact~$\sigma$, so
  $\nabla^2 f = 0$ and FONC $=$ SOSC\@.
  The iLQR backward pass (\cref{alg:riccati-eval}) gives
  exact NLP sensitivities, not approximate ones---for
  both \cref{alg:quadruped} ($13$-state) and
  \cref{alg:action-rate} ($17$-state augmented).
\item \emph{GP-LCB architecture.}
  The re-cycle (\cref{alg:recycle}) evaluates $J(\theta)$
  as a black box: the GP posterior provides Bayesian
  ``sensitivities'' $(\mu_n, \sigma_n)$ through function
  evaluations, without computing
  $\partial z^\star/\partial\theta$ via the implicit function
  theorem.
  The two-level contraction (\cref{prop:unconditional})
  therefore holds unconditionally---it does not require
  the SOSC backward pass at either level.
\item \emph{Holonomy convergence.}
  The re-cycle converges to $H(f) = 0$
  (\cref{prop:student-convergence}), the Gaussian regime
  where the dynamics curvature correction vanishes and
  FONC $=$ SOSC\@.
  The distinction between prior and posterior Riccati
  dissolves at the fixed point.
\end{enumerate}
\end{remark}
```

- [ ] **Step 2: Verify label uniqueness**

Run: `grep -rn 'rem:fonc-sosc\|rem:fonc-recycle\|eq:fonc-sosc' sections/`

Expected: Each label appears exactly once (the new definitions). No prior definitions.

---

## Task 3: Add Cross-References in articulated.tex

**Files:**
- Modify: `sections/articulated.tex:792` and `sections/articulated.tex:807`

**Context:** Two existing passages already state the FONC = SOSC and GP-avoidance results informally. These edits add one-sentence cross-references to the new framework in riccati.tex.

- [ ] **Step 1: Add FONC = SOSC cross-reference after line 792**

Current text (articulated.tex:789-792):
```latex
In the centroidal model, the dynamics is \emph{exactly} linear
($f_{xx} = 0$), so the Gauss--Newton approximation is
exact---the Joseph form \eqref{eq:joseph-form} is the true
Hessian, not an approximation.
```

Replace with (adding two lines after "not an approximation."):
```latex
In the centroidal model, the dynamics is \emph{exactly} linear
($f_{xx} = 0$), so the Gauss--Newton approximation is
exact---the Joseph form \eqref{eq:joseph-form} is the true
Hessian, not an approximation.
Equivalently, the FONC and SOSC backward passes coincide
(\cref{rem:fonc-sosc}): the iLQR sensitivity is the
exact NLP sensitivity~\cite{FreyDiffMPC}.
```

- [ ] **Step 2: Add GP-avoids-SOSC cross-reference after line 807**

Current text (articulated.tex:804-807):
```latex
The Riccati compression of \S\ref{sec:riccati} applies exactly within
each gait evaluation; the non-Riccati part (gait mode selection) achieves
the information-theoretic rate $R_T/T \to 0$ via $\gamma_T$
(\cref{prop:gp-regret}).
```

Replace with (adding two lines):
```latex
The Riccati compression of \S\ref{sec:riccati} applies exactly within
each gait evaluation; the non-Riccati part (gait mode selection) achieves
the information-theoretic rate $R_T/T \to 0$ via $\gamma_T$
(\cref{prop:gp-regret}).
Because the GP evaluates $J(\theta)$ as a black box, the outer
loop avoids the SOSC backward pass entirely
(\cref{rem:fonc-recycle}).
```

---

## Task 4: Compile and Verify

**Files:** All `.tex` files (read-only verification)

**Depends on:** Tasks 1–3

- [ ] **Step 1: Double-pass compilation**

Run:
```bash
cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory
xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex
```

Expected: "Output written on main.pdf" with ~104–105 pages. Zero errors.

- [ ] **Step 2: Check for undefined references**

Run: `grep -i 'undefined' main.log | grep -v 'Underfull'`

Expected: No output. All new labels (rem:fonc-sosc, rem:fonc-recycle, eq:fonc-sosc) and the new citation (FreyDiffMPC) must resolve.

- [ ] **Step 3: Verify new labels resolve**

Run: `grep -rn 'rem:fonc-sosc\|rem:fonc-recycle\|eq:fonc-sosc' sections/`

Expected:
- `rem:fonc-sosc`: 1 definition (riccati.tex) + 1 \cref (articulated.tex) = 2 matches
- `rem:fonc-recycle`: 1 definition (riccati.tex) + 1 \cref (articulated.tex) = 2 matches
- `eq:fonc-sosc`: 1 definition (riccati.tex) + 1 \eqref (riccati.tex) = 2 matches

- [ ] **Step 4: Verify new citation resolves**

Run: `grep -n 'FreyDiffMPC' sections/*.tex bibliography.tex`

Expected: 1 definition in bibliography.tex + 2 citations in riccati.tex + 1 citation in articulated.tex = 4 matches.

- [ ] **Step 5: Verify no stale text remains**

Run: `grep -n 'not an approximation\.' sections/articulated.tex`

Expected: One match, followed by the new FONC/SOSC sentence on the next line.

- [ ] **Step 6: Verify forward references from riccati.tex**

Run: `grep -n 'alg:quadruped\|alg:action-rate' sections/riccati.tex`

Expected: Both appear in rem:fonc-recycle item (i). These are forward references to articulated.tex, resolved on second xelatex pass.

---

## Label Inventory

| Label | File | Status | Type |
|-------|------|--------|------|
| `sec:riccati` | riccati.tex:1 | KEEP (unchanged) | section |
| `rem:fonc-sosc` | riccati.tex (new) | NEW | remark |
| `rem:fonc-recycle` | riccati.tex (new) | NEW | remark |
| `eq:fonc-sosc` | riccati.tex (new) | NEW | equation |
| `FreyDiffMPC` | bibliography.tex (new) | NEW | bibitem |

No existing labels modified or removed.

---

## Cross-Reference Network (new connections)

```
riccati.tex                     optimal-cycle.tex              articulated.tex
────────────                    ──────────────────             ────────────────
rem:fonc-sosc ──────────────────────────────────────── ← \cref (line ~794)
  ├─ cites TassaErezTodorov     alg:riccati-eval ←──── \cref in rem:fonc-recycle(i)
  ├─ cites MastalliCrocoddyl    alg:recycle ←────────── \cref in rem:fonc-recycle(ii)
  └─ cites FreyDiffMPC          prop:unconditional ←── \cref in rem:fonc-recycle(ii)
                                prop:student-conv. ←── \cref in rem:fonc-recycle(iii)
rem:fonc-recycle ───────────────────────────────────── ← \cref (line ~810)
  ├─ \cref alg:quadruped ──────────────────────────────→ articulated.tex:1061
  └─ \cref alg:action-rate ────────────────────────────→ articulated.tex:1243
```

---

## Summary

| Task | Content | Lines added | Risk |
|------|---------|-------------|------|
| 1 | FreyDiffMPC bibliography entry | 6 | Zero |
| 2 | FONC/SOSC framework in riccati.tex | ~60 | Low — standard decomposition, cites existing results |
| 3 | Two cross-reference sentences in articulated.tex | 5 | Zero — one sentence each |
| 4 | Compile + verify | 0 | Zero |

**Total insertion:** ~70 lines (~1 page). Expected page count: ~104.

**riccati.tex grows from 48 → ~110 lines** — now a proper section rather than a single remark.
