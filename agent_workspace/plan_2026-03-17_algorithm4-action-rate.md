# Algorithm 4: Action-Rate Re-Cycle Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Algorithm 4 (action-rate re-cycle) to articulated.tex — the co-optimized contact-and-locomotion variant where the Riccati inner solve produces both locomotion gains K_u(t) and contact-rate gains K_a(t) in one shot.

**Architecture:** Insert a contiguous block (exposition paragraph + equation + algorithm float + remark) after rem:arithmetic-complete (line 1197) and before section (F) Lie-Poisson duality (line 1199). Update rem:action-driven (line 1054) to reference Algorithm 4 instead of deferring. All edits in `sections/articulated.tex`.

**Tech Stack:** LaTeX (xelatex), algpseudocode for algorithm float.

---

## Dependency Graph

```
Task 1 (exposition + equation)  ──→ Task 2 (Algorithm 4) ──→ Task 3 (remark)
                                                                    │
Task 4 (update rem:action-driven)  ────────────────────────────────┘
                                                                    │
                                            Task 5 (compile + verify) ◄──┘
```

Tasks 1→2→3 are sequential (contiguous text block). Task 4 is independent. Task 5 depends on all.

---

## File Map

| File | Line | Action |
|------|------|--------|
| `sections/articulated.tex:1197` | After rem:arithmetic-complete | Insert exposition + eq:augmented-dynamics |
| `sections/articulated.tex:1197` | Same insertion point | Insert Algorithm 4 (alg:action-rate) |
| `sections/articulated.tex:1197` | Same insertion point | Insert rem:action-rate-recovery |
| `sections/articulated.tex:1054` | rem:action-driven | Replace "defer" sentence with Algorithm 4 reference |

All paths relative to `/Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory/`.

---

## Mathematical Framework (reference for all tasks)

**Existing system (Algorithm 3):**
- State: x = (p, v, phi, omega, theta) in R^13
- Control: u in R^12 (four-foot force)
- Dynamics: x-dot = A(sigma)x + B(sigma)u + c, exactly linear for frozen sigma
- Re-cycle queries: phi in T^3 (B-spline coefficients)

**Augmented system (Algorithm 4):**
- State: z = (x, beta) in R^17 = R^13 x R^4
- Control: v = (u, a) in R^16 = R^12 x R^4
- Dynamics (frozen sigma):

```
A-tilde = [A(sigma)  0    ]    B-tilde = [B(sigma)  0 ]    c-tilde = [c]
          [0         0    ]              [0         I4]              [0]
```

- Cost: Q-tilde = diag(Q, 0_4), R-tilde = diag(R_u, R_a I_4)
- Re-cycle queries: theta = (beta(0), log R_a) in R^5 (d=5, 2d+1=11 sigma points)
- Pair A (Riccati decides): (u, a) with costs (R_u, R_a)
- Pair B (re-cycle decides): (beta(0), R_a) as initial/static conditions
- Recovery: R_a -> infinity recovers Algorithm 3 (contact frozen)

---

## Task 1: Exposition Paragraph + Augmented Dynamics Equation

**Files:**
- Modify: `sections/articulated.tex` — insert after line 1197 (`\end{remark}` of rem:arithmetic-complete)

**Context:** This paragraph motivates the augmented system and defines eq:augmented-dynamics. It goes between rem:arithmetic-complete and the new Algorithm 4.

- [ ] **Step 1: Insert the exposition block**

Insert the following text after line 1197 (after `\end{remark}` of rem:arithmetic-complete), before the existing `\medskip\noindent\textbf{(F) Lie--Poisson`:

```latex

\medskip\noindent\emph{Action-rate formulation.}
The B-spline parameterization (\cref{alg:quadruped}) treats
the contact schedule $\sigma_k(t) = \mathrm{sigmoid}(\beta_k(t))$ as
\emph{predetermined}: the re-cycle optimizes the spline coefficients
$c_{k,j}$, and the Riccati inner solve takes $\sigma_k(t)$ as given.
\cref{rem:action-driven} observes that promoting $\beta_k$ to a
\emph{dynamical state} with $\dot\beta_k = a_k$ yields an augmented
system that is still exactly linear for frozen~$\sigma$:
\begin{equation}\label{eq:augmented-dynamics}
\dot{z} = \tilde{A}(\sigma)\,z + \tilde{B}(\sigma)\,v + \tilde{c},
\qquad
z = \begin{pmatrix} x \\ \beta \end{pmatrix}\!\in \R^{17},
\quad
v = \begin{pmatrix} u \\ a \end{pmatrix}\!\in \R^{16},
\end{equation}
\[
\tilde{A} = \begin{pmatrix} A(\sigma) & 0 \\ 0 & 0 \end{pmatrix}\!,
\quad
\tilde{B} = \begin{pmatrix} B(\sigma) & 0 \\ 0 & I_4 \end{pmatrix}\!,
\quad
\tilde{c} = \begin{pmatrix} c \\ 0 \end{pmatrix}\!,
\quad
\tilde{Q} = \begin{pmatrix} Q & 0 \\ 0 & 0 \end{pmatrix}\!,
\quad
\tilde{R} = \begin{pmatrix} R_u & 0 \\ 0 & R_a I_4 \end{pmatrix}\!.
\]
The Riccati framework applies to the $17$-state system:
the backward solve produces joint feedback
$K_z(t) \in \R^{16 \times 17}$ and feedforward $k_z(t) \in \R^{16}$,
co-optimizing locomotion forces $u(t)$ and contact rates $a(t)$ in
one shot.
The re-cycle queries $\theta = (\beta(0),\, \log R_a) \in \R^5$,
where $\beta(0)$ sets the initial contact configuration and
$R_a > 0$ controls the cost of reshaping the schedule
(\cref{rem:action-driven}):
\begin{itemize}[nosep]
\item $R_a \to \infty$: contact frozen, recovers
  \cref{alg:quadruped};
\item $R_a \to 0$: contact fully co-optimized with locomotion.
\end{itemize}
```

- [ ] **Step 2: Verify equation label is unique**

Run: `grep -n 'eq:augmented-dynamics' sections/articulated.tex`

Expected: Exactly one match (the new label). No prior definition.

---

## Task 2: Algorithm 4 Float

**Files:**
- Modify: `sections/articulated.tex` — insert immediately after the Task 1 block

**Context:** Algorithm 4 follows the same structural pattern as Algorithm 3 but with augmented state/control and the (beta(0), R_a) search space.

- [ ] **Step 1: Insert Algorithm 4**

Insert immediately after the Task 1 text (before `\medskip\noindent\textbf{(F) Lie--Poisson`):

```latex

\begin{algorithm}[H]
\caption{Action-rate re-cycle: co-optimized contact and locomotion
  via augmented Riccati (\cref{rem:action-driven})}
\label{alg:action-rate}
\begin{algorithmic}[1]
\Require Robot model as in \cref{alg:quadruped};\;
  GP prior $\GP(\mu_0, k)$ over
  $\theta = (\beta_0, \log R_a) \in \R^5$;\;
  seed $\theta_0$ with $J(\theta_0) \leq c_{\max}$;\;
  barrier $\varepsilon$
\Ensure Optimized $\theta^*$, augmented feedback
  $(K_z(t), k_z(t))$, posterior $(\mu_T, \sigma_T)$
\Statex \textcolor{CycleColor}{$\triangleright$
  \textbf{Phase~1} ($n \leq 11$): sigma-point warm start;\;
  \textbf{Phase~2} ($n > 11$): LCB refinement}
\State $\{\theta^{(j)}\}_{j=1}^{11} \gets$ sigma points from
  $(\mu_0, \Sigma_0)$ in~$\R^5 \cap S_1$
  \hfill\textcolor{CycleColor}{\small $d = 5$}
\Statex \textcolor{ConColor}{$\triangleright$
  $S_1 \gets \{\theta : \mu_0(\theta)
  + \sqrt{\bar\beta_1}\,\sigma_0(\theta) \leq c_{\max}\}$}
\For{$n = 1, \ldots, T$}
  \Statex \hspace{\algorithmicindent}%
    \textcolor{AcqColor}{$\triangleright$ \textbf{Acquisition}
    (\cref{alg:recycle}, line~3)}
  \State $\theta_n \gets
    \begin{cases}
      \theta^{(n)} & n \leq 11
        \quad\textcolor{CycleColor}{\text{\small(sigma-point)}}
        \\[3pt]
      \displaystyle\arg\min_{\theta \in S_n}\bigl[
        \mu_{n-1}(\theta)
        - \sqrt{\bar\beta_n}\;\sigma_{n-1}(\theta)
      \bigr] & n > 11
        \quad\textcolor{AcqColor}{\text{\small(GP-LCB)}}
    \end{cases}$
  \State $(\beta_0^{(n)},\, R_a^{(n)}) \gets \theta_n$
    \hfill\textcolor{CycleColor}{\small unpack}
  \Statex \hspace{\algorithmicindent}%
    \textcolor{ConColor}{$\triangleright$ \textbf{Augment \& freeze}
    \eqref{eq:augmented-dynamics}}
  \State $\sigma_k(t) \gets \mathrm{sigmoid}(\beta_k(t))$
    from prior trajectory;\;
    build $\tilde{A}(t), \tilde{B}(t)$
  \State $\tilde{Q} \gets \mathrm{diag}(Q, 0_4)$;\;
    $\tilde{R} \gets \mathrm{diag}(R_u,\, R_a^{(n)} I_4)$
  \Statex \hspace{\algorithmicindent}%
    \textcolor{ConColor}{$\triangleright$ \textbf{Backward solve}
    ($17$-state Riccati)}
  \State $\tilde{P}_H \gets \tilde{P}_\infty$
    via DARE \eqref{eq:dare-terminal} on
    $(\bar{\tilde{A}}_d,\, \bar{\tilde{B}}_d,\,
    \tilde{Q},\, \tilde{R})$
  \State Riccati \eqref{eq:riccati-tvlqr}
    on $(\tilde{A}_d(t),\, \tilde{B}_d(t))$
    $\to K_{z,t} \in \R^{16 \times 17}$,\;
    $k_{z,t} \in \R^{16}$,\;
    $t = H{-}1, \ldots, 0$
  \Statex \hspace{\algorithmicindent}%
    \textcolor{ConColor}{$\triangleright$ \textbf{Forward simulate}}
  \For{$m = 1, \ldots, M$}
    \hfill\textcolor{ConColor}{\small domain-rand
    \cref{rem:domain-rand}}
    \For{$t = 0, \ldots, H{-}1$}
      \State $[u_t;\, a_t] \gets k_{z,t}
        - K_{z,t}(z_t - z_t^{\mathrm{ref}})$;\;
        project support floor
      \State $x_{t+1} \gets e^{A(t)\Delta t}\,x_t
        + V(t)(B(t)\,u_t + c)$;\;
        $\beta_{t+1} \gets \beta_t + a_t\,\Delta t$
      \State $\sigma_k \gets \mathrm{sigmoid}(\beta_k)$;\;
        $h_k \gets \varepsilon\,e^{-\beta_k}$
        \hfill\textcolor{ConColor}{\small update contact}
    \EndFor
  \EndFor
  \State $J_n \gets \frac{1}{M}\sum_{m=1}^{M}
    \bigl[\sum_t (\|x_t^{(m)}\!-\!x^{\mathrm{ref}}_t\|_Q^2
    + \|u_t^{(m)}\|_{R_u}^2
    + \|a_t^{(m)}\|_{R_a}^2
    - \varepsilon\sum_k\!\log(h_k\!+\!\varepsilon))\Delta t
    + \Phi(x_H^{(m)})\bigr]$
  \Statex \hspace{\algorithmicindent}%
    \textcolor{PostColor}{$\triangleright$ \textbf{Posterior update}
    (\cref{alg:recycle}, lines~5--6)}
  \State $\mathcal{D}_n \gets \mathcal{D}_{n-1}
    \cup \{(\theta_n, J_n)\}$;\;
    update GP: $\mu_n, \sigma_n \mid \mathcal{D}_n$
    \hfill\textcolor{PostColor}{\small Bayesian}
  \Statex \hspace{\algorithmicindent}%
    \textcolor{ConColor}{$\triangleright$ \textbf{Safety \&
    contraction} (\cref{alg:recycle}, line~7)}
  \State $S_{n+1} \gets \bigl\{\theta :
    \mu_n(\theta)
    + \sqrt{\bar\beta_n}\,\sigma_n(\theta)
    \leq c_{\max}\bigr\}$
    \hfill\textcolor{ConColor}{\small pessimistic safe set}
\EndFor
\State \Return $\theta^* = \arg\min_n J_n$,\;
  $(K_z(t),\, k_z(t))$,\;
  $(\mu_T, \sigma_T)$
\end{algorithmic}
\end{algorithm}
```

- [ ] **Step 2: Verify label is unique**

Run: `grep -n 'alg:action-rate' sections/articulated.tex`

Expected: Exactly one match (the new label).

---

## Task 3: Connecting Remark

**Files:**
- Modify: `sections/articulated.tex` — insert immediately after the Algorithm 4 float

**Context:** A brief remark analogous to rem:arithmetic-complete, noting the key properties of Algorithm 4.

- [ ] **Step 1: Insert remark**

Insert immediately after the Algorithm 4 `\end{algorithm}`:

```latex

\begin{remark}[Properties of \cref{alg:action-rate}]
\label{rem:action-rate-recovery}
\begin{enumerate}[label=(\roman*),nosep]
\item \emph{Recovery.}
  As $R_a \to \infty$, the augmented Riccati forces $a_t \to 0$
  and $\beta(t) \equiv \beta(0)$: the contact schedule is
  frozen and \cref{alg:action-rate} reduces to
  \cref{alg:quadruped} with $\varphi = \mathrm{sigmoid}(\beta(0))$.
\item \emph{Arithmetic completeness.}
  The augmented system \eqref{eq:augmented-dynamics} preserves
  the $(\exp, \log, \text{linear algebra})$ closure of
  \cref{rem:arithmetic-complete}: the only new operation is the
  integrator $\beta_{t+1} = \beta_t + a_t\Delta t$ (linear).
\item \emph{Dimension.}
  State $17 \times 17$ vs.\ $13 \times 13$; control $16 \times 16$
  vs.\ $12 \times 12$.
  The Riccati cost per backstep grows as $O(n^3)$,
  so the overhead is $(17/13)^3 \approx 2.2\times$.
  The GP search dimension increases from $d = 3$ to $d = 5$
  ($2d{+}1 = 11$ sigma points vs.\ $7$).
\item \emph{Feasibility defects.}
  The contact budget \eqref{eq:contact-budget} need not hold
  pointwise during iteration; the GP posterior contraction
  (\cref{rmk:mpc}) closes feasibility defects progressively,
  analogous to multiple-shooting continuity closure.
\end{enumerate}
\end{remark}
```

---

## Task 4: Update rem:action-driven

**Files:**
- Modify: `sections/articulated.tex:1054`

**Context:** rem:action-driven currently ends with "We defer the implementation to future work." Replace with a forward reference to Algorithm 4.

- [ ] **Step 1: Replace the deferral sentence**

Current text (articulated.tex:1054):
```latex
We defer the implementation to future work.
```

Replace with:
```latex
\cref{alg:action-rate} implements this formulation.
```

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

Expected: Output written on main.pdf. Zero errors. Page count ~103 (was 101).

- [ ] **Step 2: Check for undefined references**

Run: `grep 'undefined' main.log`

Expected: No output.

- [ ] **Step 3: Verify new labels resolve**

Run: `grep -n 'alg:action-rate\|eq:augmented-dynamics\|rem:action-rate-recovery' sections/articulated.tex`

Expected: Each label appears at least twice (definition + reference).

- [ ] **Step 4: Verify rem:action-driven updated**

Run: `grep -n 'defer.*future\|defer.*implementation' sections/articulated.tex`

Expected: No output (the old deferral is gone).

- [ ] **Step 5: Verify sign consistency in new algorithm**

Run: `grep -n 'arg.min\|arg.max' sections/articulated.tex`

Expected: All instances are `\arg\min` (cost minimization). Zero `\arg\max`.

- [ ] **Step 6: Verify safe set uses UCB (plus sign)**

Visually confirm in the new algorithm: `\mu_n(\theta) + \sqrt{\bar\beta_n}\,\sigma_n(\theta) \leq c_{\max}` (plus, pessimistic).

---

## Summary

| Task | Content | Lines added | Risk |
|------|---------|-------------|------|
| 1 | Exposition + eq:augmented-dynamics | ~30 | Low — standard block-diagonal augmentation |
| 2 | Algorithm 4 (alg:action-rate) | ~75 | Medium — follows Algorithm 3 pattern precisely |
| 3 | rem:action-rate-recovery | ~20 | Low — properties are mechanical |
| 4 | Update rem:action-driven | 1 line | Zero |
| 5 | Compile + verify | 0 | Zero |

**Total insertion:** ~125 lines (~1.5 pages). Expected page count: 103.
