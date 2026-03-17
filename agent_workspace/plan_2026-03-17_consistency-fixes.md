# Consistency Fix Chain Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 8 consistency issues from the 2026-03-17 self-symbolic consistency check, ordered by dependency.

**Architecture:** The issues form a locked chain C1→C1b→C1c→C2 (sign/safety cluster), plus 4 independent fixes (C3, S1, S2, S3). The sign fix (C1) must land first because it changes the acquisition formula referenced everywhere. All edits are LaTeX-only — no code changes.

**Tech Stack:** LaTeX (xelatex), amsart document class, algorithm/algpseudocode packages.

---

## File Structure

| File | Responsibility | Tasks |
|------|---------------|-------|
| `sections/optimal-cycle.tex` | Core algorithms + propositions + remarks | Tasks 1-5 |
| `sections/articulated.tex` | Quadruped Algorithm 3 + narrative | Task 3, 6 |
| `sections/riccati.tex` | Riccati compression remark | Task 6 |
| `sections/chu-duality.tex` | Chu duality + linear logic | Task 6 |
| `sections/lie-group-intro.tex` | Part II introduction | Task 6 |

All paths relative to `/Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory/`.

---

## Chunk 1: The Locked Chain (C1 → C1b → C1c → C2)

### Task 1: C1 — Fix acquisition sign (cost minimization convention)

**Problem:** `argmax[μ + √β̄σ]` is GP-UCB for reward maximization, but J is cost to minimize. Need GP-LCB: `argmin[μ − √β̄σ]`.

**Design decision:** We negate the acquisition to preserve the argmin/cost-minimization convention throughout:
- Acquisition: `β_n = argmin_{β ∈ S_n} [μ_{n-1}(β) − √β̄_n σ_{n-1}(β)]` (GP-LCB)
- The "anti-attention" interpretation survives: LCB = attention MINUS anti-attention, so the algorithm selects points where low expected cost OVERCOMES exploration uncertainty.

**Files:**
- Modify: `sections/optimal-cycle.tex:262-273` (eq:gp-ucb + text)
- Modify: `sections/optimal-cycle.tex:361-370` (Algorithm 2, Phase 2 acquisition)
- Modify: `sections/optimal-cycle.tex:649-657` (rmk:attention, anti-attention equation)
- Modify: `sections/optimal-cycle.tex:831-833` (rmk:sigma-algebra, UCB item)
- Modify: `sections/optimal-cycle.tex:882` (rmk:sigma-algebra, "argmax of UCB")
- Modify: `sections/articulated.tex:1086-1091` (Algorithm 3 acquisition)

- [ ] **Step 1: Fix eq:gp-ucb and surrounding text** (`optimal-cycle.tex:262-273`)

Change:
```latex
% OLD (lines 262-273):
\begin{equation}\label{eq:gp-ucb}
\textcolor{AcqColor}{
  u_n(\beta)
  = \mu_{n-1}(\beta)
    + \sqrt{\bar\beta_n}\;\sigma_{n-1}(\beta)
}
\end{equation}
...
selects $\beta_n = \arg\max_{\beta \in S_n} u_n(\beta)$, yielding the
```

To:
```latex
% NEW:
\begin{equation}\label{eq:gp-ucb}
\textcolor{AcqColor}{
  \ell_n(\beta)
  = \mu_{n-1}(\beta)
    - \sqrt{\bar\beta_n}\;\sigma_{n-1}(\beta)
}
\end{equation}
...
selects $\beta_n = \arg\min_{\beta \in S_n} \ell_n(\beta)$, yielding the
```

Note: rename `u_n` → `ℓ_n` (for "lower confidence bound") to signal the change in convention.

- [ ] **Step 2: Fix Algorithm 2 Phase 2 acquisition** (`optimal-cycle.tex:366-369`)

Change:
```latex
      \displaystyle\arg\max_{\beta \in S_n}\bigl[
        \mu_{n-1}(\beta) + \sqrt{\bar\beta_n}\;\sigma_{n-1}(\beta)
      \bigr] & n > 2d{+}1
        \quad\textcolor{AcqColor}{\text{\small(GP-UCB)}}
```

To:
```latex
      \displaystyle\arg\min_{\beta \in S_n}\bigl[
        \mu_{n-1}(\beta) - \sqrt{\bar\beta_n}\;\sigma_{n-1}(\beta)
      \bigr] & n > 2d{+}1
        \quad\textcolor{AcqColor}{\text{\small(GP-LCB)}}
```

- [ ] **Step 3: Fix rmk:attention anti-attention equation** (`optimal-cycle.tex:649-662`)

Change:
```latex
\textcolor{AcqColor}{
  u_n(\beta)
  = \underbrace{\mu_n(\beta)}_{\text{attention (exploit)}}
  + \sqrt{\bar\beta_n}\;
    \underbrace{\sigma_n(\beta)}_{\text{anti-attention (explore)}}.
}
```

To:
```latex
\textcolor{AcqColor}{
  \ell_n(\beta)
  = \underbrace{\mu_n(\beta)}_{\text{attention (exploit)}}
  - \sqrt{\bar\beta_n}\;
    \underbrace{\sigma_n(\beta)}_{\text{anti-attention (explore)}}.
}
```

Also update line 649: `\eqref{eq:gp-ucb} adds an` → keep (the label is unchanged).

And update the narrative at lines 659-662:
```latex
% OLD:
The posterior variance~$\sigma_n$ is maximal where the kernel
``attends least''---precisely the unexplored regions---so the
UCB balances attending to known-good gaits against anti-attending
to explore unknown ones.
```
To:
```latex
% NEW:
The posterior variance~$\sigma_n$ is maximal where the kernel
``attends least''---precisely the unexplored regions---so the
LCB selects where low expected cost overcomes exploration
uncertainty: known-good gaits minus the penalty for the unknown.
```

- [ ] **Step 4: Fix rmk:sigma-algebra UCB item** (`optimal-cycle.tex:831-833`)

Change:
```latex
\item \emph{UCB} $= \mathbb{E}[J \mid \cF_n]
  + \sqrt{\bar\beta_n}\;\|J - \mathbb{E}[J \mid \cF_n]\|
  $: optimistic projection, known plus calibrated unknown.
```

To:
```latex
\item \emph{LCB} $= \mathbb{E}[J \mid \cF_n]
  - \sqrt{\bar\beta_n}\;\|J - \mathbb{E}[J \mid \cF_n]\|
  $: optimistic projection for cost, known minus calibrated unknown.
```

- [ ] **Step 5: Fix rmk:sigma-algebra "argmax of UCB"** (`optimal-cycle.tex:882`)

Change:
```latex
  $\arg\max$ of UCB).
```

To:
```latex
  $\arg\min$ of LCB).
```

- [ ] **Step 6: Fix Algorithm 3 acquisition** (`articulated.tex:1086-1091`)

Change:
```latex
  \State $\varphi_n \gets
    \arg\max_{\varphi \in S_n}\bigl[
      \mu_{n-1}(\varphi)
      + \sqrt{\bar\beta_n}\;\sigma_{n-1}(\varphi)
    \bigr]$
    \hfill\textcolor{AcqColor}{\small GP-UCB}
```

To:
```latex
  \State $\varphi_n \gets
    \arg\min_{\varphi \in S_n}\bigl[
      \mu_{n-1}(\varphi)
      - \sqrt{\bar\beta_n}\;\sigma_{n-1}(\varphi)
    \bigr]$
    \hfill\textcolor{AcqColor}{\small GP-LCB}
```

- [ ] **Step 7: Verify — compile**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex`
Expected: Compiles without errors. Check that `\eqref{eq:gp-ucb}` still resolves (label unchanged).

---

### Task 2: C1b — Unify safe set signs

**Problem:** S₁ uses UCB ≤ c_max (μ+σ ≤ c_max), S_{n+1} uses LCB ≤ c_max (μ−σ ≤ c_max). For safety (ensuring J(β) ≤ c_max w.h.p.), both should use UCB ≤ c_max (pessimistic about cost).

**Design decision:** Unify to UCB: S_n = {β : μ_{n-1}(β) + √β̄_n σ_{n-1}(β) ≤ c_max}. This is the pessimistic criterion — a point is safe only if even the worst-case cost is below threshold.

**Files:**
- Modify: `sections/optimal-cycle.tex:387-390` (Algorithm 2, S_{n+1})
- Modify: `sections/optimal-cycle.tex:437-443` (prop:safe-gp proof sketch)
- Modify: `sections/optimal-cycle.tex:583-587` (rmk:mpc, "LCB-based update")
- Modify: `sections/articulated.tex:1078-1081` (Algorithm 3, S₁ — already correct, verify)
- Modify: `sections/articulated.tex:1146-1150` (Algorithm 3, S_{n+1})

- [ ] **Step 1: Fix Algorithm 2 S_{n+1}** (`optimal-cycle.tex:387-390`)

Change:
```latex
  \State $S_{n+1} \gets \bigl\{\beta :
    \mu_n(\beta) - \sqrt{\bar\beta_n}\,\sigma_n(\beta)
    \leq c_{\max}\bigr\}$
    \hfill\textcolor{ConColor}{\small Safe GP-UCB \cite{SuiSafeOpt}}
```

To:
```latex
  \State $S_{n+1} \gets \bigl\{\beta :
    \mu_n(\beta) + \sqrt{\bar\beta_n}\,\sigma_n(\beta)
    \leq c_{\max}\bigr\}$
    \hfill\textcolor{ConColor}{\small pessimistic safe set
    \cite{SuiSafeOpt}}
```

- [ ] **Step 2: Fix prop:safe-gp proof sketch** (`optimal-cycle.tex:437-443`)

Change:
```latex
The safe set $S_{n+1}$ (line~7) uses the lower confidence bound
$\mathrm{lcb}_n(\beta)
= \mu_n(\beta) - \sqrt{\bar\beta_n}\,\sigma_n(\beta)
\leq c_{\max}$, so any $\beta \in S_{n+1}$ satisfies
$g(\beta) \leq 0$ w.h.p.\ by the GP confidence
interval~\cite{SuiSafeOpt,BerkenkampSafeMPC}.
```

To:
```latex
The safe set $S_{n+1}$ (line~7) uses the upper confidence bound
$\mathrm{ucb}_n(\beta)
= \mu_n(\beta) + \sqrt{\bar\beta_n}\,\sigma_n(\beta)
\leq c_{\max}$, so any $\beta \in S_{n+1}$ satisfies
$J(\beta) \leq c_{\max}$ w.h.p.\ by the GP confidence
interval~\cite{SuiSafeOpt,BerkenkampSafeMPC}.
```

- [ ] **Step 3: Fix rmk:mpc recursive feasibility** (`optimal-cycle.tex:583-587`)

Change:
```latex
the LCB-based update (line~7) and Lipschitz continuity of~$g$
ensure $S_{n+1} \supseteq S_n \cap B_\epsilon(\beta_n)$
```

To:
```latex
the UCB-based update (line~7) and Lipschitz continuity of~$g$
ensure $S_{n+1} \supseteq S_n \cap B_\epsilon(\beta_n)$
```

- [ ] **Step 4: Fix Algorithm 3 S_{n+1}** (`articulated.tex:1146-1150`)

Change:
```latex
  \State $S_{n+1} \gets \bigl\{\varphi :
    \mu_n(\varphi)
    - \sqrt{\bar\beta_n}\,\sigma_n(\varphi)
    \leq c_{\max}\bigr\}$
    \hfill\textcolor{ConColor}{\small safe GP-UCB}
```

To:
```latex
  \State $S_{n+1} \gets \bigl\{\varphi :
    \mu_n(\varphi)
    + \sqrt{\bar\beta_n}\,\sigma_n(\varphi)
    \leq c_{\max}\bigr\}$
    \hfill\textcolor{ConColor}{\small pessimistic safe set}
```

- [ ] **Step 5: Verify — compile**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex`
Expected: Clean compilation.

---

### Task 3: C1c — Phase 1 sigma-point safety

**Problem:** During Phase 1 (n ≤ 2d+1), sigma points are used without checking membership in S_n. Prop 9.9 claims safety for all n ≥ 1.

**Design decision:** Constrain sigma points to S₁. Add intersection: compute sigma points from prior covariance, then filter to those in S₁. This is the minimal fix. Also weaken prop:safe-gp to clarify Phase 1 safety depends on the prior width.

**Files:**
- Modify: `sections/optimal-cycle.tex:351-354` (Algorithm 2, line 1 sigma points)
- Modify: `sections/optimal-cycle.tex:429-434` (prop:safe-gp statement)

- [ ] **Step 1: Constrain sigma points to safe set** (`optimal-cycle.tex:351-354`)

Change:
```latex
\State $\{\beta^{(j)}\}_{j=1}^{2d+1} \gets$ sigma points from
  $(\mu_0, \Sigma_0)$ in~$\Theta$
  \hfill\textcolor{CycleColor}{\small unscented
  (\cref{rmk:unscented}, Level~3)}
```

To:
```latex
\State $\{\beta^{(j)}\}_{j=1}^{2d+1} \gets$ sigma points from
  $(\mu_0, \Sigma_0)$ in~$\Theta \cap S_1$
  \hfill\textcolor{CycleColor}{\small unscented
  (\cref{rmk:unscented}, Level~3)}
```

- [ ] **Step 2: Clarify prop:safe-gp** (`optimal-cycle.tex:429-434`)

Change:
```latex
\begin{proposition}[Per-step safety]
\label{prop:safe-gp}
Define the constraint $g(\beta) = J(\beta) - c_{\max}$.
Under Lipschitz continuity of~$g$,
\cref{alg:recycle} ensures $g(\beta_n) \leq 0$ for all $n \geq 1$
with probability at least $1-\delta$.
\end{proposition}
```

To:
```latex
\begin{proposition}[Per-step safety]
\label{prop:safe-gp}
Define the constraint $g(\beta) = J(\beta) - c_{\max}$.
Under Lipschitz continuity of~$g$ and with sigma points
drawn from~$S_1$,
\cref{alg:recycle} ensures $g(\beta_n) \leq 0$ for all $n \geq 1$
with probability at least $1-\delta$.
\end{proposition}
```

- [ ] **Step 3: Verify — compile**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex`
Expected: Clean compilation.

---

### Task 4: C2 — Add Phase 1 sigma-point warm start to Algorithm 3

**Problem:** Algorithm 3 (alg:quadruped) has only GP-UCB acquisition (no sigma-point Phase 1), making it unfaithful to Algorithm 2's two-phase structure.

**Files:**
- Modify: `sections/articulated.tex:1066-1091` (Algorithm 3, before For loop + acquisition line)

- [ ] **Step 1: Add sigma-point computation before For loop** (`articulated.tex`)

After the `\Statex` for S₁ initialization (line 1081) and before `\For` (line 1082), insert:
```latex
\State $\{\varphi^{(j)}\}_{j=1}^{2d+1} \gets$ sigma points from
  $(\mu_0, \Sigma_0)$ in~$\Theta \cap S_1$
  \hfill\textcolor{CycleColor}{\small Phase~1 warm start}
```

- [ ] **Step 2: Change acquisition to cases statement** (`articulated.tex:1086-1091`)

Change:
```latex
  \State $\varphi_n \gets
    \arg\min_{\varphi \in S_n}\bigl[
      \mu_{n-1}(\varphi)
      - \sqrt{\bar\beta_n}\;\sigma_{n-1}(\varphi)
    \bigr]$
    \hfill\textcolor{AcqColor}{\small GP-LCB}
```

To:
```latex
  \State $\varphi_n \gets
    \begin{cases}
      \varphi^{(n)} & n \leq 2d{+}1
        \quad\textcolor{CycleColor}{\text{\small(sigma-point)}}
        \\[3pt]
      \displaystyle\arg\min_{\varphi \in S_n}\bigl[
        \mu_{n-1}(\varphi)
        - \sqrt{\bar\beta_n}\;\sigma_{n-1}(\varphi)
      \bigr] & n > 2d{+}1
        \quad\textcolor{AcqColor}{\text{\small(GP-LCB)}}
    \end{cases}$
```

Note: This uses the ALREADY-FIXED sign from Task 1 Step 6. Task 1 MUST complete before this step.

- [ ] **Step 3: Update line references in rem:arithmetic-complete** (`articulated.tex:1164-1178`)

After adding the sigma-point line, Algorithm 3's line numbering shifts by +1. Check and update:
- Old "lines 2--13" → new "lines 3--14" (or verify; depends on exact numbering)
- Old "lines 6--7" → new "lines 7--8"

To determine correct numbers: count all `\State` and `\For` lines in the restructured Algorithm 3.

- [ ] **Step 4: Verify — compile**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex`
Expected: Clean compilation.

---

## Chunk 2: Independent Fixes (C3, S1, S2, S3)

### Task 5: C3 + S1 — Fix sufficiency overclaim + G⊥F_n independence

**Problem (C3):** "Minimal generators of a sufficient σ-algebra" overclaims; contradicts V_{n+1} < V_n. Also, the equation in rmk:unscented Level 3 (lines 754-757) incorrectly includes sigma-point weights w^{(j)}.

**Problem (S1):** "G is independent of F_n" is false; J_n ∈ σ(G) ∩ F_n.

**Files:**
- Modify: `sections/optimal-cycle.tex:836-854` (rmk:sigma-algebra, "Sigma points as generators")
- Modify: `sections/optimal-cycle.tex:870-878` (rmk:sigma-algebra, "Randomness structure")
- Modify: `sections/optimal-cycle.tex:751-757` (rmk:unscented Level 3, fix equation)

- [ ] **Step 1: Fix "Sigma points as generators" paragraph** (`optimal-cycle.tex:836-854`)

Change:
```latex
\smallskip\noindent\emph{Sigma points as generators.}
For Gaussian measures, the $\sigma$-algebra generated by
$2d{+}1$ sigma-point evaluations captures all second-order
information:
\[
  \textcolor{CycleColor}{
  \cF_{2d+1}^{\mathrm{UT}}
  = \sigma\!\bigl(J(\beta^{(1)}), \ldots, J(\beta^{(2d+1)})\bigr),
  \qquad
  \mathbb{E}[J(\beta) \mid \cF_{2d+1}^{\mathrm{UT}}]
  = \mu_{\mathrm{GP}}(\beta),
  }
\]
as shown in Level~3 of \cref{rmk:unscented}.
The sigma points are the \emph{minimal generators} of a
sufficient $\sigma$-algebra for the Gaussian prior.
Phase~1 of \cref{alg:recycle} constructs
$\cF_{2d+1}^{\mathrm{UT}}$; Phase~2 refines it:
$\cF_{2d+1} \subset \cF_{2d+2} \subset \cdots \subset \cF_T$.
```

To:
```latex
\smallskip\noindent\emph{Sigma points as optimal initialization.}
For a Gaussian prior over $\Theta \subseteq \R^d$, the
$2d{+}1$ sigma points are the \emph{optimal batch design}
for recovering the first two moments of any function
pushed through the prior:
\[
  \textcolor{CycleColor}{
  \cF_{2d+1}^{\mathrm{UT}}
  = \sigma\!\bigl(J(\beta^{(1)}), \ldots, J(\beta^{(2d+1)})\bigr),
  \qquad
  \mu_{2d+1}(\beta)
  = \mathbb{E}[J(\beta) \mid \cF_{2d+1}^{\mathrm{UT}}],
  }
\]
where $\mu_{2d+1}$ is the GP posterior conditioned on these
$2d{+}1$ observations (Level~3 of \cref{rmk:unscented}).
This is a finite-dimensional approximation, not
function-space sufficiency: $V_{2d+2} < V_{2d+1}$
(\cref{rmk:mpc}), so further observations always improve
the posterior.
Phase~1 of \cref{alg:recycle} constructs
$\cF_{2d+1}^{\mathrm{UT}}$ as the best batch initialization;
Phase~2 refines it adaptively:
$\cF_{2d+1} \subset \cF_{2d+2} \subset \cdots \subset \cF_T$.
```

- [ ] **Step 2: Fix rmk:unscented Level 3 equation** (`optimal-cycle.tex:751-757`)

Change:
```latex
The sigma-point statistics recover the GP posterior exactly:
\[
\textcolor{PostColor}{
  \mu_{\mathrm{UT}}(\beta)
  = \sum_{j} w^{(j)}\, k(\beta, \beta^{(j)})\,
    (K + \sigma^2_{\mathrm{noise}} I)^{-1}\, \mathbf{J}
  = \mu_{\mathrm{GP}}(\beta),
}
\]
```

To:
```latex
The GP posterior conditioned on these $2d{+}1$ evaluations is:
\[
\textcolor{PostColor}{
  \mu_{2d+1}(\beta)
  = \mathbf{k}(\beta)^\top\,
    (K + \sigma^2_{\mathrm{noise}} I)^{-1}\, \mathbf{J},
}
\]
where $\mathbf{k}(\beta)_j = k(\beta, \beta^{(j)})$ and
$K_{ij} = k(\beta^{(i)}, \beta^{(j)})$.
The sigma points provide the optimal query locations for
this batch: they are chosen to capture the prior covariance
structure, so $\mu_{2d+1}$ is the best $2d{+}1$-point GP
approximation.
```

- [ ] **Step 3: Fix G⊥F_n independence claim** (`optimal-cycle.tex:870-878`)

Change:
```latex
\item \emph{Injective randomness}
  $\mathcal{G} = \sigma(\theta^{(1)}, \ldots, \theta^{(M)})$:
  domain-randomized parameters (\cref{rem:domain-rand}),
  deliberate noise for robustness.
  Its effect is absorbed into $\sigma^2_{\mathrm{noise}}$
  in the GP likelihood.
  $\mathcal{G}$ is independent of~$\cF_n$---the injected noise
  does not leak into the acquisition decisions.
```

To:
```latex
\item \emph{Injective randomness.}
  At each iteration~$n$, fresh domain-randomized parameters
  $\mathcal{G}_n = \sigma(\theta_n^{(1)}, \ldots, \theta_n^{(M)})$
  (\cref{rem:domain-rand}) are drawn independently of the
  observation history~$\cF_{n-1}$.
  Their effect is absorbed into $\sigma^2_{\mathrm{noise}}$
  in the GP likelihood: the noise realization affects~$J_n$
  (and hence enters~$\cF_n$), but the acquisition
  $\beta_{n+1}$ was determined from~$\cF_n$ before
  $\mathcal{G}_{n+1}$ is realized.
```

- [ ] **Step 4: Verify — compile**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex`
Expected: Clean compilation.

---

### Task 6: S2 — Fix MPPI terminology drift in 3 files

**Problem:** `riccati.tex`, `chu-duality.tex`, `lie-group-intro.tex` still use "MPPI outer loop" / "dual ascent on ε" / "MPPI temperature schedule" while the algorithm sections have migrated to GP-UCB.

**Files:**
- Modify: `sections/riccati.tex:8-16`
- Modify: `sections/chu-duality.tex:269-277`
- Modify: `sections/chu-duality.tex:311-313`
- Modify: `sections/chu-duality.tex:326-332`
- Modify: `sections/lie-group-intro.tex:9`

- [ ] **Step 1: Fix riccati.tex** (`riccati.tex:8-16`)

Change:
```latex
The MPPI estimator of \cref{prop:forward-only} supplies the
improvement half: sample $N$ trajectories, assign Boltzmann weights
$w^{(i)} \propto \exp\!\bigl(-J^{(i)}/\varepsilon\bigr)$, and compute
the weighted average.
The Boltzmann reweighting is exactly the exponential bridge applied to
the path measure---it converts the uniform (prior) measure over
trajectories to the optimal (posterior) measure, with the cost
functional $J$ playing the role of the negative log-likelihood.
Convergence at $O(N^{-1/2})$ is guaranteed by the CLT
(\cref{thm:add-clt,thm:mult-clt}), independently of $\dim G$.
```

To:
```latex
The forward estimator of \cref{prop:forward-only} supplies the
inner evaluation: for a given gait parameter~$\beta$, sample $M$
domain-randomized trajectories and average to obtain $J(\beta)$
(\cref{alg:riccati-eval}).
The Boltzmann target
$\pi(\beta) \propto \exp\!\bigl(-J(\beta)/\varepsilon\bigr)$
converts the uniform (prior) measure over trajectories to the
optimal (posterior) measure, with the cost functional $J$
playing the role of the negative log-likelihood.
The re-cycle outer loop (\cref{alg:recycle}) replaces the
Monte Carlo convergence rate $O(N^{-1/2})$ with the
information-theoretic rate $R_T/T \to 0$ via
$\gamma_T$ (\cref{prop:gp-regret}).
```

- [ ] **Step 2: Fix chu-duality.tex outer loop references** (`chu-duality.tex:269-277`)

Change:
```latex
The MPPI outer loop optimizes the B-spline coefficients
$c_{k,j} \in \R$---the ``tuning-free'' log-domain
representation---while the Riccati inner solve computes optimal gains
from the resulting $\sigma_k(t)$---the physical-domain trajectory.
The MPPI outer loop, viewed as a path integral over log-space contact
schedules (\S\ref{sec:articulated}), makes this Chu duality
computational: the forward map $\beta \to x(T)$ evaluates the Chu
pairing, while the Boltzmann-weighted inverse (path-integral mean)
is the adjunction condition.
```

To:
```latex
The re-cycle outer loop (\cref{alg:recycle}) optimizes the B-spline
coefficients $c_{k,j} \in \R$---the ``tuning-free'' log-domain
representation---while the Riccati inner solve computes optimal gains
from the resulting $\sigma_k(t)$---the physical-domain trajectory.
The re-cycle, viewed as Bayesian quadrature over log-space contact
schedules (\S\ref{sec:articulated}), makes this Chu duality
computational: the forward map $\beta \to x(T)$ evaluates the Chu
pairing, while the GP posterior mean (conditional expectation) is
the adjunction condition.
```

- [ ] **Step 3: Fix chu-duality.tex dual ascent** (`chu-duality.tex:311-313`)

Change:
```latex
The dual ascent on $\varepsilon$ (\S\ref{sec:cycle}) is the
\emph{dereliction} map $!A \to A$: each iteration tightens the
barrier, consuming one layer of the exponential modality.
```

To:
```latex
The barrier schedule $\varepsilon \to 0$ (\S\ref{sec:cycle}) is the
\emph{dereliction} map $!A \to A$: each tightening step consumes
one layer of the exponential modality.
```

- [ ] **Step 4: Fix chu-duality.tex dereliction remark** (`chu-duality.tex:328`)

Change:
```latex
In the dual ascent $\varepsilon \to 0$:
```

To:
```latex
In the barrier schedule $\varepsilon \to 0$:
```

- [ ] **Step 5: Fix lie-group-intro.tex** (`lie-group-intro.tex:9`)

Change the relevant clause:
```latex
provides the MPPI temperature schedule---the noise level $\varepsilon$
in the path-integral sampler corresponds to the effective $\nu$ of
the sampling distribution.
```

To:
```latex
provides the re-cycle temperature schedule---the barrier parameter
$\varepsilon$ corresponds to the effective $\nu$ of the exploration
distribution (\cref{rmk:mpc}).
```

- [ ] **Step 6: Verify — compile**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex`
Expected: Clean compilation.

---

### Task 7: S3 — Fix Algorithm 3 line-range in rem:arithmetic-complete

**Problem:** "lines 2-13" may exclude the safety line after numbering changes.

**NOTE:** This task depends on Task 4 completing first (Algorithm 3 restructure shifts line numbers).

**Files:**
- Modify: `sections/articulated.tex:1164-1178` (rem:arithmetic-complete)

- [ ] **Step 1: Recount Algorithm 3 line numbers after Task 4**

After Task 4 adds a sigma-point line, recount all numbered lines. Then update:
- "lines N--M" range to include all lines inside the For loop through safety
- "lines X--Y" for backward solve

- [ ] **Step 2: Update rem:arithmetic-complete accordingly**

(Exact values depend on Task 4 line count — executor must verify.)

- [ ] **Step 3: Verify — compile**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex`
Expected: Clean compilation, zero undefined references on second pass.

---

## Chunk 3: Final Verification

### Task 8: Full compilation + grep audit

- [ ] **Step 1: Double-pass compile**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex && xelatex -interaction=nonstopmode main.tex`
Expected: Zero undefined references, zero missing citations.

- [ ] **Step 2: Grep for any remaining sign inconsistencies**

Run:
```bash
cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory
grep -n 'arg\\\\max.*mu.*sigma\|argmax.*mu.*sigma' sections/*.tex
grep -n 'arg\\\\max.*\\\\mu.*\\\\sigma' sections/*.tex
```
Expected: Zero matches (all argmax[μ+σ] should be converted to argmin[μ−σ]).

- [ ] **Step 3: Grep for remaining "MPPI outer loop" references**

Run:
```bash
grep -n 'MPPI outer\|MPPI loop\|MPPI sample\|dual ascent on' sections/*.tex
```
Expected: Zero matches in narrative text. Only acceptable remaining "MPPI" references: bibliography citation `\cite{WilliamsMPPI}`, historical comparisons ("GP-UCB replaces MPPI's..."), and `mppi.tex` section header/theoretical content.

- [ ] **Step 4: Verify safe set sign consistency**

Run:
```bash
grep -n 'mu.*-.*sqrt.*sigma.*c_.*max\|mu.*+.*sqrt.*sigma.*c_.*max' sections/*.tex
```
Expected: All safe set definitions use `μ + √β̄σ ≤ c_max` (UCB form). No LCB form in safe set definitions.
