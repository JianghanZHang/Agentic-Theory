# Plan: Algorithm 2 Restructure + σ-Algebraic Connective Remark

## Summary

Two coupled changes to `sections/optimal-cycle.tex`:

**Change A:** Restructure Algorithm 2 (`alg:recycle`) — add sigma-point initialization as Phase 1 of a single algorithm. Phase 1 IS Phase 2 with sigma-point query strategy for the first $2d{+}1$ iterations.

**Change B:** New remark (`rmk:sigma-algebra`) — connective σ-algebraic remark unifying `rmk:attention`, `rmk:unscented`, and `rmk:mpc` via conditional expectation and filtration theory.

---

## Change A: Algorithm 2 Restructure

### Current Algorithm 2 line numbering

| Line | Content |
|------|---------|
| 1 | `\For{n=1,...,T}` |
| 2 | β_n ← argmax UCB (acquisition) |
| 3 | J_n ← RiccatiEval (evaluate) |
| 4 | D_n ← D_{n-1} ∪ {(β_n, J_n)} |
| 5 | GP update: μ_n, σ_n |
| 6 | S_{n+1} ← safe set |
| 7 | Return β*, (μ_T, σ_T) |

### New Algorithm 2 line numbering

| Line | Content | Note |
|------|---------|------|
| **1** | **Compute 2d+1 sigma points from (μ₀, Σ₀)** | **NEW** |
| 2 | `\For{n=1,...,T}` | was line 1 |
| 3 | β_n ← cases{σ-point if n≤2d+1, UCB if n>2d+1} | was line 2, now conditional |
| 4 | J_n ← RiccatiEval | was line 3 |
| 5 | D_n ← D_{n-1} ∪ ... | was line 4 |
| 6 | GP update | was line 5 |
| 7 | S_{n+1} ← safe set | was line 6 |
| 8 | Return | was line 7 |

### Line reference mapping (old → new)

All references shift by +1:

| Old ref | New ref | Locations |
|---------|---------|-----------|
| line 2 | line 3 | cycle-connection (383), rmk:svgd-ilqr (586), articulated (838, 1085) |
| line 3 | line 4 | — (no explicit refs to old line 3) |
| lines 4--5 | lines 5--6 | cycle-connection (386), rem:domain-rand (681), articulated (1138) |
| line 5 | line 6 | prop:scalable proof (522) |
| line 6 | line 7 | prop:safe-gp proof (420), cycle-connection (388), rmk:mpc (569), articulated (1145) |

### Exact edits to Algorithm 2 (optimal-cycle.tex lines 335–377)

Replace lines 335–377 with:

```latex
\begin{algorithm}[ht]
\caption{Re-cycle: GP-UCB gait optimization with sigma-point initialization}
\label{alg:recycle}
\begin{algorithmic}[1]
\Require Prior $\GP(\mu_0,k)$, seed point $\beta_0$ with
         $J(\beta_0) \leq c_{\max}$, dimension $d = \dim\Theta$,
         threshold $c_{\max}$, horizon~$T$
\Ensure Optimized gait $\beta^*$, posterior $(\mu_T,\sigma_T)$
\Statex \textcolor{CycleColor}{$\triangleright$
  \textbf{Phase~1} ($n \leq 2d{+}1$): sigma-point warm start;\;
  \textbf{Phase~2} ($n > 2d{+}1$): UCB refinement}
\State $\{\beta^{(j)}\}_{j=1}^{2d+1} \gets$ sigma points from
  $(\mu_0, \Sigma_0)$ in~$\Theta$
  \hfill\textcolor{CycleColor}{\small unscented
  (\cref{rmk:unscented}, Level~3)}
\Statex \textcolor{ConColor}{$\triangleright$
  $S_1 \gets \{\beta : \mu_0(\beta) + \sqrt{\bar\beta_1}\,\sigma_0(\beta)
  \leq c_{\max}\}$, seeded from~$\beta_0$}
\For{$n = 1, \ldots, T$}
  \Statex \hspace{\algorithmicindent}%
    \textcolor{AcqColor}{$\triangleright$ \textbf{Acquisition}}
  \State $\beta_n \gets
    \begin{cases}
      \beta^{(n)} & n \leq 2d{+}1
        \quad\textcolor{CycleColor}{\text{\small(sigma-point)}} \\[3pt]
      \displaystyle\arg\max_{\beta \in S_n}\bigl[
        \mu_{n-1}(\beta) + \sqrt{\bar\beta_n}\;\sigma_{n-1}(\beta)
      \bigr] & n > 2d{+}1
        \quad\textcolor{AcqColor}{\text{\small(GP-UCB)}}
    \end{cases}$
  \Statex \hspace{\algorithmicindent}%
    \textcolor{ConColor}{$\triangleright$ \textbf{Evaluate
    (\cref{alg:riccati-eval})}}
  \State $J_n,\, K_n(t),\, k_n(t) \gets
    \textsc{RiccatiEval}(\beta_n, M)$
    \hfill\textcolor{ConColor}{\small \cref{alg:riccati-eval}}
  \Statex \hspace{\algorithmicindent}%
    \textcolor{PostColor}{$\triangleright$ \textbf{Posterior update
    (Bayesian)}}
  \State $\mathcal{D}_n \gets \mathcal{D}_{n-1}
    \cup \{(\beta_n, J_n)\}$
  \State Update GP: $\mu_n, \sigma_n \mid \mathcal{D}_n$
    \hfill\textcolor{PostColor}{\small $\cO(\gamma_n^3)$ via MINI-META
    \cite{CalandrielloMINIMETA}}
  \Statex \hspace{\algorithmicindent}%
    \textcolor{ConColor}{$\triangleright$ \textbf{Safety \& contraction}}
  \State $S_{n+1} \gets \bigl\{\beta :
    \mu_n(\beta) - \sqrt{\bar\beta_n}\,\sigma_n(\beta)
    \leq c_{\max}\bigr\}$
    \hfill\textcolor{ConColor}{\small Safe GP-UCB \cite{SuiSafeOpt}}
\EndFor
\State \Return $\beta^* = \arg\min_{n} J_n$,\;
  $(\mu_T, \sigma_T)$
\end{algorithmic}
\end{algorithm}
```

### Line reference updates in optimal-cycle.tex

1. **Cycle connection** (line ~383):
   - `Line~2` → `Line~3`
   - `Lines~4--5` → `Lines~5--6`
   - `Line~6` → `Line~7`

2. **prop:safe-gp proof** (line ~420):
   - `line~6` → `line~7`

3. **prop:scalable proof** (line ~522):
   - `line~5` → `line~6`

4. **rmk:mpc** (line ~569):
   - `line~6` → `line~7`

5. **rmk:svgd-ilqr** (line ~586):
   - `line~2` → `line~3`

6. **rem:domain-rand** (line ~681):
   - `lines~4--5 of \cref{alg:recycle}` → `lines~5--6 of \cref{alg:recycle}`

### Line reference updates in articulated.tex

7. **line 838**: `line~2` → `line~3`
8. **line 1085**: `line~2` → `line~3`
9. **line 1138**: `lines~4--5` → `lines~5--6`
10. **line 1145**: `line~6` → `line~7`

### Update rmk:omd-algorithm intro (line ~305-314)

Add mention of Phase 1/Phase 2 structure to the intro remark.

### Update rmk:unscented Level 3 (line ~720-752)

Level 3 currently says "the GP posterior is recoverable from sigma-point evaluations" but doesn't reference Algorithm 2's Phase 1. Update to explicitly reference Phase 1 (line 1) of Algorithm 2.

### Update Algorithm 3 (articulated.tex)

Algorithm 3 line 1 currently references `\cref{alg:recycle}, line~2`. Need to check if it should now say `line~3` and mention the sigma-point / UCB choice.

---

## Change B: σ-Algebraic Connective Remark

### Placement

After `rmk:unscented` (line 766), before the section end. This is the capstone remark that requires the reader to have seen rmk:attention, rmk:mpc, and rmk:unscented.

### Label

`rmk:sigma-algebra`

### Content structure

```latex
\begin{remark}[Measure-theoretic unification:
$\sigma$-algebra, attention, and the unscented transform]
\label{rmk:sigma-algebra}

[Intro: The three preceding remarks — kernel attention
(rmk:attention), MPC interpretation (rmk:mpc), and constrained
unscented GP (rmk:unscented) — are manifestations of a single
measure-theoretic structure: the filtration generated by
GP observations.]

\smallskip\noindent\emph{The observation filtration.}
[Define F_n = σ(D_n) = σ(β_1,J_1,...,β_n,J_n), the
σ-algebra generated by n observations. F_0 ⊂ F_1 ⊂ ... ⊂ F_T
is a filtration. Each iteration of Algorithm 2 refines F_n
by one observation.]

\smallskip\noindent\emph{Conditional expectation as GP posterior.}
[E[J(β)|F_n] = μ_n(β) exactly — the GP posterior mean IS the
conditional expectation. The posterior variance is
Var(J(β)|F_n) = σ²_n(β). This is not an approximation but an
identity: for Gaussian processes, conditional expectation and
posterior mean coincide by definition.]

\smallskip\noindent\emph{Attention as projection.}
[The conditional expectation E[·|F_n] is the L²-orthogonal
projection onto F_n-measurable functions. This identifies:
- attention (rmk:attention): μ_n(β) = E[J(β)|F_n] = projection
  onto "what is known"
- anti-attention: σ_n(β) = √Var(J(β)|F_n) = norm of the
  projection onto F_n^⊥ = "what is unknown"
- UCB: u_n(β) = E[J(β)|F_n] + √β̄_n · ‖J(β) - E[J(β)|F_n]‖
  = known + calibrated unknown
The GP-UCB acquisition is the optimistic projection:
argmax of (projection + scaled residual norm).]

\smallskip\noindent\emph{Sigma points as generators.}
[For Gaussian measures, the σ-algebra generated by 2d+1
sigma-point evaluations {J(β^(j))} captures all second-order
information. That is:
F_{2d+1}^{UT} = σ(J(β^(1)),...,J(β^(2d+1)))
and E[J(β)|F_{2d+1}^{UT}] = μ_UT(β) = μ_GP(β) (Level 3 of
rmk:unscented). The sigma points are the *minimal generators*
of a sufficient σ-algebra for the Gaussian prior.
Phase 1 of Algorithm 2 constructs F_{2d+1}^{UT}; Phase 2
refines it: F_{2d+1} ⊂ F_{2d+2} ⊂ ... ⊂ F_T.]

\smallskip\noindent\emph{MPC as filtration dynamics.}
[The MPC interpretation (rmk:mpc) becomes: the state
s_n = (μ_n, Σ_n) is the conditional law of J given F_n.
The Lyapunov function V_n = tr(Σ_n) measures the "size" of
F_n^⊥ — the unexplained variance. Each observation shrinks
F_n^⊥ by a rank-1 projection, giving V_{n+1} < V_n. The
cycle closes when F_T = F_∞, i.e., all uncertainty is resolved.]

\smallskip\noindent\emph{Randomness structure.}
[Two independent sources of randomness, living in disjoint
σ-algebras:
(i) Injective randomness G = σ(θ^(1),...,θ^(M)):
    domain-randomized parameters (rem:domain-rand). This is
    *deliberate* noise for robustness. Its effect is absorbed
    into σ²_noise in the GP likelihood.
(ii) Process randomness: none. The acquisition β_n is a
    deterministic function of (μ_{n-1}, σ_{n-1}, S_n). The
    algorithm has NO inductive randomness — every decision is
    a deterministic function of F_{n-1}. This is a categorical
    distinction from MPPI, where the sampling distribution
    introduces inductive randomness that cannot be replayed.]
\end{remark}
```

### Cross-references to add

The remark should `\cref` to:
- `rmk:attention` (attention/anti-attention)
- `rmk:mpc` (MPC, Lyapunov)
- `rmk:unscented` (sigma points, Level 3)
- `alg:recycle` (Phase 1, Phase 2)
- `rem:domain-rand` (injective randomness)

### No new bibliography entries needed

All cited results (conditional expectation = L² projection, σ-algebra generation) are standard measure theory. Billingsley is already in the bibliography.

---

## Execution Order

1. **Edit Algorithm 2** in optimal-cycle.tex (lines 335–377)
2. **Update all 10 line references** (6 in optimal-cycle.tex, 4 in articulated.tex)
3. **Update rmk:omd-algorithm** intro text
4. **Update rmk:unscented Level 3** to reference Phase 1
5. **Insert rmk:sigma-algebra** after rmk:unscented (line 767)
6. **Compile** (`xelatex main.tex && xelatex main.tex`)
7. **Verify** zero undefined references, correct line numbers in PDF

---

## Blast radius

- `optimal-cycle.tex`: Algorithm 2 rewrite + 6 line-ref edits + rmk:omd-algorithm update + rmk:unscented Level 3 update + new remark insertion
- `articulated.tex`: 4 line-ref edits only
- `bibliography.tex`: no changes
- `main.tex`: no changes
