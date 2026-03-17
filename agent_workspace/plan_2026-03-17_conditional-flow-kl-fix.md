# Conditional Flow KL Fix — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the 12 consistency-check issues by rewriting the GP-UCB section through the lens of conditional flow matching on Gaussian measures, where the GP posterior update IS the conditional flow and the Bakry-Émery log-Sobolev inequality provides the contraction rate.

**Architecture:** The GP is reframed from a generative model ($J \sim \mathrm{GP}(0,k)$) to a transport model ($\mathrm{GP}(\mu_0, k)$ defines a conditional flow from prior to truth). The KL contraction proposition is rewritten with precise definitions: $\alpha = 1/\|k\|_{\mathrm{op}}$ (Bakry-Émery), $\eta_n = \sigma^2_{n-1}(\beta_n)/(\sigma^2_{n-1}(\beta_n) + \sigma^2_{\mathrm{noise}})$ (per-step information ratio). The information gain $\gamma_T$ becomes the unifying quantity controlling both regret and KL contraction.

**Tech Stack:** XeLaTeX, amsart document class

**Files (all relative to `/Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory/`):**
- Modify: `bibliography.tex` (add 1 entry)
- Modify: `sections/optimal-cycle.tex` (11 targeted edits)

---

## Chunk 1: Foundation Fixes

### Task 1: Add Bakry-Émery bibliography entry

**Files:**
- Modify: `bibliography.tex` — add entry before `\end{thebibliography}`

- [ ] **Step 1: Add bibliography entry**

Insert before the line `\bibitem{SrinivasGPUCB}`:

```latex
\bibitem{BakryEmery}
D.~Bakry and M.~\'Emery,
Diffusions hypercontractives,
in \emph{S\'eminaire de Probabilit\'es~XIX},
Lecture Notes in Math., vol.~1123, Springer, 1985, pp.~177--206.
```

- [ ] **Step 2: Compile check**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex 2>&1 | grep -c "undefined"`
Expected: 0 (or small number that resolves on second pass)

---

### Task 2: Unify `\mathrm{KL}` → `\KL` in Prop 9.7

**Files:**
- Modify: `sections/optimal-cycle.tex:231,237,247`

- [ ] **Step 1: Replace 3 occurrences**

Line 231 — change `D_{\mathrm{KL}}` → `D_{\KL}` in:
```
\emph{Bregman divergence:} $D_\varphi(\theta' \| \theta) = D_{\mathrm{KL}}(q_{\theta'} \| q_\theta)$.
```

Line 237 — change `D_{\mathrm{KL}}` → `D_{\KL}` in:
```
q_{n+1} = \arg\min_q \bigl\{\langle \hat{\nabla}\ell_n, q\rangle + \tfrac{1}{\varepsilon_n}\, D_{\mathrm{KL}}(q \,\|\, q_n)\bigr\}
```

Line 247 — change `D_{\mathrm{KL}}` → `D_{\KL}` in:
```
The minimizer of $\langle g, q\rangle + \frac{1}{\eta} D_{\mathrm{KL}}(q \| p)$
```

Use `replace_all` with `D_{\mathrm{KL}}` → `D_{\KL}` across the file.

---

### Task 3: Fix `q_n` notation collision — eliminate dictionary-size variable

**Files:**
- Modify: `sections/optimal-cycle.tex:332,441,451-453`

The symbol `q_n` is used for both the GP posterior distribution (Prop 9.10) and the MINI-META dictionary size (Algorithm 1 line 8, Prop 9.12). Fix by writing dictionary-size bounds directly in terms of $\gamma_n$ (the information gain, already defined).

- [ ] **Step 1: Fix Algorithm 1 line 8 annotation**

Old (line 332):
```latex
    \hfill\textcolor{PostColor}{\small $\cO(q_n^3)$ via MINI-META
    \cite{CalandrielloMINIMETA}}
```

New:
```latex
    \hfill\textcolor{PostColor}{\small $\cO(\gamma_n^3)$ via MINI-META
    \cite{CalandrielloMINIMETA}}
```

- [ ] **Step 2: Fix Prop 9.12 statement**

Old (lines 440-441):
```latex
Using the MINI-META sparse approximation~\cite{CalandrielloMINIMETA}
with effective dictionary size $q_n = \cO((\log n)^{d+1})$,
```

New:
```latex
Using the MINI-META sparse approximation~\cite{CalandrielloMINIMETA}
with effective dictionary size bounded by $\gamma_n = \cO((\log n)^{d+1})$,
```

- [ ] **Step 3: Fix Prop 9.12 proof sketch**

Old (lines 451-453):
```latex
Each GP update (line~8) costs $\cO(q_n^3)$ via MINI-META, where
$q_n \leq \gamma_n = \cO((\log n)^{d+1})$.
Summing: $\sum_{n=1}^T q_n^3 = \cO(T\,(\log T)^{3(d+1)})$.
```

New:
```latex
Each GP update (line~8) costs $\cO(\gamma_n^3)$ via MINI-META, where
$\gamma_n = \cO((\log n)^{d+1})$ for the SE kernel.
Summing: $\sum_{n=1}^T \gamma_n^3 = \cO(T\,(\log T)^{3(d+1)})$.
```

---

### Task 4: Define dimension $d$, clarify $|\Theta|$, define constraint $g$

**Files:**
- Modify: `sections/optimal-cycle.tex:252-254,265,380-381`

- [ ] **Step 1: Add dimension $d$ in rmk:omd-regret**

Old (lines 253-254):
```latex
$k(\beta,\beta') = \exp\!\bigl(-\tfrac{\|\beta-\beta'\|^2}{2\ell^2}\bigr)$.
```

New (adds $d = \dim\Theta$):
```latex
$k(\beta,\beta') = \exp\!\bigl(-\tfrac{\|\beta-\beta'\|^2}{2\ell^2}\bigr)$,
where $d = \dim\Theta$ is the gait parameter dimension.
```

- [ ] **Step 2: Clarify $|\Theta|$ in GP-UCB coefficient**

Old (line 265):
```latex
$\bar\beta_n = 2\log(|\Theta|\,n^2\pi^2/6\delta)$)
```

New:
```latex
$\bar\beta_n = 2\log(|\Theta|\,n^2\pi^2/6\delta)$,
with $|\Theta|$ the cardinality of a finite cover of~$\Theta$)
```

- [ ] **Step 3: Define constraint function $g$ in prop:safe-gp**

Old (lines 380-381):
```latex
Under Lipschitz continuity of the constraint function~$g$,
\cref{alg:recycle} ensures $g(\beta_n) \leq 0$ for all $n \geq 1$
```

New:
```latex
Define the constraint $g(\beta) = J(\beta) - c_{\max}$.
Under Lipschitz continuity of~$g$,
\cref{alg:recycle} ensures $g(\beta_n) \leq 0$ for all $n \geq 1$
```

- [ ] **Step 4: Compile check**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex 2>&1 | tail -5`

---

## Chunk 2: Core Rewrite — GP Transport Model + KL Contraction

### Task 5: Reframe GP as transport model + add $S_1$ initialization

**Files:**
- Modify: `sections/optimal-cycle.tex:250-254` (rmk:omd-regret opening)
- Modify: `sections/optimal-cycle.tex:307-309` (Algorithm 1 \Require + \Ensure)
- Modify: `sections/optimal-cycle.tex:362` (prop:gp-regret RKHS assumption)

- [ ] **Step 1: Rewrite GP framing in rmk:omd-regret**

Old (lines 252-254, after Step 1 of Task 4):
```latex
Model the objective landscape as a draw from a Gaussian process,
$J \sim \GP(0, k)$, with squared-exponential kernel
$k(\beta,\beta') = \exp\!\bigl(-\tfrac{\|\beta-\beta'\|^2}{2\ell^2}\bigr)$,
where $d = \dim\Theta$ is the gait parameter dimension.
```

New:
```latex
Model the objective landscape with a Gaussian process surrogate
$\GP(\mu_0, k)$, where $\mu_0$ is a prior mean (e.g., the cost at a
known safe gait) and
$k(\beta,\beta') = \exp\!\bigl(-\tfrac{\|\beta-\beta'\|^2}{2\ell^2}\bigr)$
is the squared-exponential kernel in dimension $d = \dim\Theta$.
The GP is a \emph{transport model}: the posterior
$q_n = \GP(\mu_n, \Sigma_n \mid \mathcal{D}_n)$ defines a conditional
flow from prior to truth (\cref{prop:kl-contract}), not a generative
claim that $J$ was sampled from the GP.
```

- [ ] **Step 2: Update Algorithm 1 \Require to use $\GP(\mu_0, k)$ and seed $\beta_0$**

Old (lines 307-309):
```latex
\Require Prior $\GP(0,k)$, safe set $S_1$, threshold $c_{\max}$,
         $M$~domain-randomized copies, horizon~$T$
\Ensure Optimized gait $\beta^*$, posterior $(\mu_T,\sigma_T)$
```

New:
```latex
\Require Prior $\GP(\mu_0,k)$, seed point $\beta_0$ with
         $J(\beta_0) \leq c_{\max}$, threshold $c_{\max}$,
         $M$~domain-randomized copies, horizon~$T$
\Ensure Optimized gait $\beta^*$, posterior $(\mu_T,\sigma_T)$
\Statex \textcolor{ConColor}{$\triangleright$
  $S_1 \gets \{\beta : \mu_0(\beta) + \sqrt{\bar\beta_1}\,\sigma_0(\beta)
  \leq c_{\max}\}$, seeded from~$\beta_0$}
```

Note: This `\Statex` is unnumbered and appears before the `\For`, so it does NOT shift any line numbers.

- [ ] **Step 3: Update RKHS assumption in prop:gp-regret**

Old (line 362):
```latex
Suppose $J$ lies in the RKHS of the SE kernel with $\|J\|_k \leq B$.
```

New:
```latex
Suppose $J - \mu_0$ lies in the RKHS of the SE kernel with $\|J - \mu_0\|_k \leq B$.
```

---

### Task 6: Rewrite KL contraction proposition (prop:kl-contract) — THE CORE FIX

**Files:**
- Modify: `sections/optimal-cycle.tex:394-414`

This is the central fix. The old proposition cites an undefined log-Sobolev mechanism. The new one:
- Defines $\pi$ as the Boltzmann target (resolving "π undefined")
- Defines $\eta_n$ as the per-step signal-to-noise ratio (resolving "η undefined")
- Identifies $\alpha = 1/\|k\|_{\mathrm{op}}$ as the Bakry-Émery constant (resolving "α undefined")
- Notes that $\sigma^2_{\mathrm{noise}}$ enters through $\eta_n$ (resolving observation noise concern)
- Connects to $\gamma_T$ (unifying regret and contraction)

- [ ] **Step 1: Replace the full proposition + proof sketch**

Old (lines 394-414):
```latex
\begin{proposition}[KL contraction]
\label{prop:kl-contract}
Let $q_n$ denote the GP posterior at iteration~$n$ and $\pi$ the true
cost landscape. Then
\[
\textcolor{ConColor}{
  D_{\KL}(q_{n+1} \| \pi)
  \leq (1 - 2\alpha\eta)\,D_{\KL}(q_n \| \pi),
}
\]
where $\alpha$ is the log-Sobolev constant of the kernel~$k$
and $\eta$ is the GP update step size.
\end{proposition}

\begin{proof}[Proof sketch]
The GP posterior update is a Bayesian contraction in the
Fisher--Rao metric. By the log-Sobolev inequality
for the SE kernel~\cite{Ledoux}, the KL divergence to the
stationary distribution contracts at rate $1-2\alpha\eta$ per
update.
\end{proof}
```

New:
```latex
\begin{proposition}[KL contraction via conditional flow]
\label{prop:kl-contract}
The GP posterior sequence $q_0, q_1, \ldots$ from \cref{alg:recycle}
forms a conditional flow on the space of Gaussian measures.
Let $\pi(\beta) \propto \exp(-J(\beta)/\varepsilon)$ be the Boltzmann
target and define the per-step information ratio
\[
  \eta_n
  = \frac{\sigma^2_{n-1}(\beta_n)}
         {\sigma^2_{n-1}(\beta_n) + \sigma^2_{\mathrm{noise}}}.
\]
Then:
\begin{enumerate}[label=(\roman*)]
\item The mutual information satisfies
$I(J;\, \mathcal{D}_T) = \gamma_T
= \tfrac{1}{2}\sum_{n=1}^{T}
  \log\bigl(1 + \sigma^2_{n-1}(\beta_n)
  /\sigma^2_{\mathrm{noise}}\bigr)$.
\item The continuous-time KL contraction rate is
\[
\textcolor{ConColor}{
  \frac{d}{dt}\,D_{\KL}(q_t \| \pi)
  \leq -\frac{2}{\|k\|_{\mathrm{op}}}\,
       D_{\KL}(q_t \| \pi),
}
\]
where $\|k\|_{\mathrm{op}}$ is the operator norm of the kernel
and $1/\|k\|_{\mathrm{op}}$ is the Gaussian log-Sobolev constant
(Bakry--\'Emery~\cite{BakryEmery,Ledoux}).
\end{enumerate}
\end{proposition}

\begin{proof}[Proof sketch]
(i)~Standard GP information gain: each observation at $\beta_n$ with
noise $\sigma^2_{\mathrm{noise}}$ contributes
$\tfrac{1}{2}\log(1+\sigma^2_{n-1}(\beta_n)
/\sigma^2_{\mathrm{noise}})$
to the mutual information about~$J$.

(ii)~The GP prior $q_0 = \GP(\mu_0, k)$ is a Gaussian measure on
function space.
By the Bakry--\'Emery criterion~\cite{BakryEmery,Ledoux},
every Gaussian measure satisfies a log-Sobolev inequality with
constant $\alpha = \lambda_{\min}(k^{-1}) = 1/\|k\|_{\mathrm{op}}$.
Each posterior update $q_n \mapsto q_{n+1}$ is a rank-$1$
contraction of the covariance operator:
$\Sigma_{n+1} = \Sigma_n
  - k(\cdot,\beta_{n+1})\,k(\beta_{n+1},\cdot)
  /(\sigma^2_n(\beta_{n+1}) + \sigma^2_{\mathrm{noise}})$.
This is the Bures--Wasserstein optimal transport between
Gaussians, and the log-Sobolev inequality gives the
exponential KL decay along this conditional
flow~\cite{Ledoux}.
The observation noise $\sigma^2_{\mathrm{noise}}$ from
domain randomization (\cref{rem:domain-rand}) modulates the
per-step information through~$\eta_n$: larger noise slows
contraction but improves robustness.
\end{proof}
```

- [ ] **Step 2: Compile check**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex 2>&1 | tail -5`

---

### Task 7: Update prop:unconditional to use new KL formulation

**Files:**
- Modify: `sections/optimal-cycle.tex:467-472`

- [ ] **Step 1: Replace combined statement (iii)**

Old (lines 467-472):
```latex
\item \emph{Combined:} the KL divergence from the
iterate distribution to the optimal satisfies
$D_{\KL}(q_n \| \pi) \to 0$ at rate
$(1-2\alpha\eta)^n$ (\cref{prop:kl-contract}),
with total cost $\cO(T(\log T)^{3(d+1)})$
(\cref{prop:scalable}).
```

New:
```latex
\item \emph{Combined:} the information gain
$\gamma_T = I(J;\,\mathcal{D}_T)$ simultaneously
controls the regret
(\cref{prop:gp-regret}: $R_T \leq \cO(\sqrt{T\gamma_T\log T})$)
and the KL contraction rate
(\cref{prop:kl-contract}: exponential at rate
$2/\|k\|_{\mathrm{op}}$),
with total cost $\cO(T(\log T)^{3(d+1)})$
(\cref{prop:scalable}).
```

---

### Task 8: Strengthen holonomy connection in rmk:omd-regret

**Files:**
- Modify: `sections/optimal-cycle.tex:286-291`

- [ ] **Step 1: Rewrite holonomy connection paragraph**

Old (lines 286-291):
```latex
\item \emph{Holonomy connection.}
$R_T > 0$ iff $H(f) > 0$---the cycle has not closed.
Convergence $R_T/T \to 0$ means the holonomy vanishes
asymptotically, recovering the OMD interpretation of
\cref{prop:omd} with a sharper rate.
```

New:
```latex
\item \emph{Holonomy connection.}
The information gain $\gamma_T$ plays the role of the
holonomy $H(f)$: it measures how far the conditional flow
has transported the GP prior toward the truth
(\cref{prop:kl-contract}).
$R_T > 0$ iff $\gamma_T > 0$ iff the cycle has not closed.
Convergence $R_T/T \to 0$ means the holonomy vanishes
asymptotically, recovering the OMD interpretation of
\cref{prop:omd} with a sharper, information-theoretic rate.
```

---

## Chunk 3: Final Verification

### Task 9: Compile twice and verify all references

**Files:**
- All modified files

- [ ] **Step 1: First compile pass**

Run: `cd /Users/jianghanstudio/Workspace/Agentic-Theory/independent_volume/optimal_cycle_theory && xelatex -interaction=nonstopmode main.tex 2>&1 | tail -10`

- [ ] **Step 2: Second compile pass**

Run: `xelatex -interaction=nonstopmode main.tex 2>&1 | tail -10`

- [ ] **Step 3: Verify zero undefined references**

Run: `grep -c "undefined" main.log`
Expected: 0

- [ ] **Step 4: Verify all new labels resolve**

Run: `grep -E "newlabel\{(prop:kl-contract|prop:unconditional|eq:gp-ucb|alg:recycle)" main.aux`
Expected: All 4 labels present with correct numbers

- [ ] **Step 5: Verify new cite key resolves**

Run: `grep "BakryEmery" main.aux`
Expected: Entry present

- [ ] **Step 6: Verify no label-changed warning**

Run: `grep "Label.*changed" main.log`
Expected: No matches (after 2nd pass)

- [ ] **Step 7: Commit**

```bash
cd /Users/jianghanstudio/Workspace/Agentic-Theory
git add independent_volume/optimal_cycle_theory/sections/optimal-cycle.tex independent_volume/optimal_cycle_theory/bibliography.tex
git commit -m "paper: conditional flow KL contraction + 12 consistency fixes

Rewrite Prop 9.10 (KL contraction) with Bakry-Émery log-Sobolev
on Gaussian measures. GP reframed from generative model to
conditional flow transport model. Information gain γ_T unifies
regret bound and KL contraction rate.

Fixes: q_n notation collision, undefined g/π/α/η/d/|Θ|/S_1,
\KL macro unification, holonomy-regret connection via γ_T."
```

---

## Issue-to-Task Mapping

| Issue | Task | Fix |
|-------|------|-----|
| C1: KL contraction contradicted | Task 6 | Rewrite with Bakry-Émery + conditional flow |
| C2: GP model unverified | Task 5 | Reframe as transport model, $\mathrm{GP}(\mu_0, k)$ |
| C3: Holonomy-regret unjustified | Task 8 | Connect via $\gamma_T$ |
| C4: Constraint $g$ undefined | Task 4 | Define $g(\beta) = J(\beta) - c_{\max}$ |
| C5: $q_n$ collision | Task 3 | Replace with $\gamma_n$ |
| C6: $S_1$ unspecified | Task 5 | Add initialization in Algorithm 1 |
| C7: Dimension $d$ undefined | Task 4 | Define $d = \dim\Theta$ |
| S3: `\KL` vs `\mathrm{KL}` | Task 2 | Unify to `\KL` |
| P4: $\pi$ undefined | Task 6 | Define as Boltzmann target |
| P4: $\alpha$, $\eta$ undefined | Task 6 | Define precisely via Bakry-Émery |
| P4: $|\Theta|$ unexplained | Task 4 | Add "finite cover" clarification |
| P4: OMD→GP-UCB motivation | Task 8 | Strengthen via $\gamma_T$ narrative |
