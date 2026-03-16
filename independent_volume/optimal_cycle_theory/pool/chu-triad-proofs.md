# Chu Tensor Product Proofs for Seven Fano Plane Triads

## Framework

For a Chu bilinear map $\mathcal{C}_1 \otimes \mathcal{C}_2 \to \mathcal{C}_3$, construct:
1. Forward map $f: A_1 \otimes A_2 \to A_3$
2. Left backward $g_1: A_2 \otimes X_3 \to X_1$
3. Right backward $g_2: A_1 \otimes X_3 \to X_2$

Triple adjunction condition:
$$r_3(f(a_1, a_2), x_3) = r_1(a_1, g_1(a_2, x_3)) = r_2(a_2, g_2(a_1, x_3))$$

## Eight Chu Objects

| Basis | Object | $A$ (forward) | $X$ (backward) | $r(A,X)$ |
|---|---|---|---|---|
| $e_1$ | BB (Barrier-Boltzmann) | $C(Q)$: barrier $V=-\varepsilon\log h$ | $\mathcal{P}(Q)$: Boltzmann $w$ | $\mathbb{E}_w[V]$ |
| $e_2$ | Ri (Riccati) | $\mathrm{Sym}^+_n$: cost $P$ | $\mathrm{Sym}^+_n$: covariance $\Sigma$ | $\mathrm{tr}(P\Sigma)$ |
| $e_3$ | LP (Lie-Poisson) | $\mathfrak{g}$: velocity $\xi$ | $\mathfrak{g}^*$: momentum $\mu$ | $\langle\mu,\xi\rangle$ |
| $e_4$ | HC (Hopf-Cole) | $C^\infty(G)$: value $V$ | $C^\infty_{>0}(G)$: $\psi=e^{-V/(2\varepsilon)}$ | $\int\psi e^{V/(2\varepsilon)}d\mu_G$ |
| $e_5$ | Ha (Hardy) | $H^2(\mathbb{T})$: causal $f_+$ | $(H^2)^\perp$: anti-causal $f_-$ | $\int f_+\bar{f}_- d\theta$ |
| $e_6$ | PW (Peter-Weyl) | $V_\rho$: rep space | $V_\rho^*$: contragredient | $v^*(v)$ |
| $e_7$ | AS (Action-State) | $\mathbb{R}$: log-contact $\beta$ | $(0,1)$: contact $\sigma$ | $\beta\sigma$ |

---

## T1: $e_1 \cdot e_2 = e_3$ (BB × Ri = LP) — Contact Jacobian

**Status: COMPLETE (in paper + Gemini proof)**

### Maps
- $f(\sigma, f_k) = \mu = \sum_k \sigma_k(r_k \times f_k) \in \mathfrak{g}^*$
- $g_1(f_k, \xi) = W_{\sigma_k} = \langle r_k \times f_k, \xi\rangle$
- $g_2(\sigma, \xi) = \delta x_k = \sigma_k(\xi \times r_k)$

### Verification
$$r_3(\mu,\xi) = \sum_k\sigma_k\langle r_k\times f_k,\xi\rangle = r_1(\sigma, W_\sigma) = r_2(f_k, \delta x_k)$$

Uses scalar triple product cyclicity: $\langle f, \xi\times r\rangle = \langle r\times f, \xi\rangle$.

### Key identity: D'Alembert's virtual work principle. Q.E.D.

---

## T2: $e_1 \cdot e_4 = e_5$ (BB × HC = Ha) — Feynman-Kac Projection

**Status: Tier B (strong construction)**

### Physical intuition
Barrier potential (BB) + Hopf-Cole linearization (HC) → causal spectral structure (Ha).
The Feynman-Kac path integral is inherently causal (forward-time), so its spectral
content naturally lives in $H^2$. The relationship is the Szego outer function factorization.

### Setup
For gait spectral density $f > 0$ on $\mathbb{T}$, decompose:
$$\log f(\theta) = c_0 + \sum_{k\geq 1} c_k e^{2\pi ik\theta} + \sum_{k\geq 1}\bar{c}_k e^{-2\pi ik\theta}$$

Three components map to three Chu objects:
- DC: $c_0 = \int\log f\,d\theta$, geometric mean $G(f) = e^{c_0}$ → **HC**
- Causal AC: $(\log f)_+ = \sum_{k\geq 1}c_k e^{2\pi ik\theta} \in H^2$ → **Ha**
- Total density: $f = \exp(c_0 + (\log f)_+ + (\log f)_-)$ → **BB** (via Toeplitz)

### Maps
**Forward** $f: C(Q) \otimes C^\infty(G) \to H^2$

Given barrier $V_\mathrm{bar}$ (determines $f = e^{-V_\mathrm{bar}/\varepsilon}$) and value function $V$
(via Hopf-Cole: $\psi = e^{-V/(2\varepsilon)}$), the Szego-Kolmogorov outer function:
$$f(V_\mathrm{bar}, V) = h \in H^2, \quad h(z) = \exp\!\left(\frac{c_0}{2} + \sum_{k\geq 1}c_k z^k\right)$$
satisfying $f = |h|^2$ on $\mathbb{T}$.

**Left backward** $g_1: C^\infty(G) \otimes (H^2)^\perp \to \mathcal{P}(Q)$

Boltzmann measure determined by outer function decomposition:
$dw \propto |h|^2 \cdot e^{-V/\varepsilon}\,d\theta = f \cdot e^{-V/\varepsilon}\,d\theta$

**Right backward** $g_2: C(Q) \otimes (H^2)^\perp \to C^\infty_{>0}(G)$

$\psi = \exp(-c_0/2)\cdot \exp(-(\log f)_-)$

### Adjunction verification — Strong Szego Limit Theorem

$$\underbrace{\log D_n(f)}_{\text{BB: Toeplitz det}} = \underbrace{n\cdot \int_\mathbb{T}\log f\,d\theta}_{\text{HC: geometric mean }G(f)^n} + \underbrace{\sum_{k\geq 1}k|c_k|^2}_{\text{Ha: holonomy }H(f)} + o(1)$$

The weight $k$ in $H(f) = \sum k|c_k|^2$ arises from the Toeplitz matrix structure
(mode $k$ appears in $n-k$ matrix entries), not from the Hardy pairing itself.

### Key identity: Strong Szego Limit Theorem = T2 Chu adjunction.

---

## T3: $e_1 \cdot e_7 = e_6$ (BB × AS = PW) — Gait Spectral Analysis

**Status: Tier C (construction reasonable, needs function space lifting)**

### Physical intuition
Barrier (BB) modulates contact schedule (AS); the Fourier decomposition of the
resulting periodic gait function gives Peter-Weyl coefficients (PW).
Mediator: Fourier sign.

### Maps
Periodic gait function $F(\theta) = \sigma(\beta(\theta))\cdot e^{-V_\mathrm{bar}(\theta)/\varepsilon}$.

**Forward** $f(V_\mathrm{bar}, \beta) = \hat{F}(n) = \int_\mathbb{T}\sigma(\beta(\theta))e^{-V_\mathrm{bar}/\varepsilon}e^{-2\pi in\theta}d\theta$

**Left backward** $g_1(\beta, v_n^*) = w$ where $dw(\theta) = \bar{v}_n^*\sigma(\beta(\theta))e^{-2\pi in\theta}d\theta$

**Right backward** $g_2(V_\mathrm{bar}, v_n^*) = \sigma_n = \bar{v}_n^*e^{-V_\mathrm{bar}/\varepsilon}e^{-2\pi in\theta}$

### Adjunction
Uses $V_\mathrm{bar} = \varepsilon(\beta + \log\varepsilon^{-1})$ (barrier-logit identity).
For $n \neq 0$, the constant $\log\varepsilon^{-1}$ vanishes under Fourier projection.

### Key identity: Fourier inversion + barrier-logit identity $V_\mathrm{bar} = \varepsilon(\beta + \mathrm{const})$.

### Technical gap: AS object needs lifting from scalar $(\beta, \sigma)$ to $L^2(\mathbb{T})$.

---

## T4: $e_2 \cdot e_4 = e_6$ (Ri × HC = PW) — Riccati Spectral Decomposition

**Status: Tier B- (needs lifting argument)**

### Physical intuition
HJB on compact Lie group $G$ block-diagonalizes via Peter-Weyl. In each irreducible
$\rho$, Casimir acts as scalar $\lambda_\rho$. For left-invariant quadratic cost, each
block yields an independent finite-dimensional Riccati equation. Hopf-Cole linearizes
each block to a linear eigenvalue problem.
Mediator: symplectic $J$.

### Maps
**Forward** $f(P, V) = v_\rho = \hat{V}_\rho \cdot P_\rho^{1/2} \in V_\rho$

**Left backward** $g_1(V, v^*_\rho) = \Sigma_\rho$ via Schur orthogonality

**Right backward** $g_2(P, v^*_\rho)(g) = v^*_\rho(\rho(g)P_\rho^{-1/2})$

### Adjunction
In LQR specialization ($V_\rho = x^T P_\rho x$, $\psi_\rho = e^{-x^T P_\rho x/(2\varepsilon)}$):
$$\mathrm{tr}(P_\rho\Sigma_\rho) = \frac{d_\rho}{2}\varepsilon$$
(equipartition: each degree of freedom contributes $\varepsilon/2$)

### Key identity: Schur orthogonality + LQR equipartition theorem.

---

## T5: $e_2 \cdot e_5 = e_7$ (Ri × Ha = AS) — Causal Feedback → Contacts

**Status: Tier C (construction reasonable, needs function space lifting)**

### Physical intuition
Riccati optimal feedback (Ri) + causal spectral structure (Hardy) → optimal contact
schedule (AS). The causal component of the Riccati gain $K(\theta)$ encodes "predictable
future gains"; the contact schedule $\sigma(\theta)$ is determined by the causal prediction.
Mediator: spectral factor sign.

### Maps
**Forward** $f(P, f_+) = \beta(\theta) = \mathrm{logit}(\langle K(\theta), f_+(\theta)\rangle / \|K(\theta)\|)$

**Left backward** $g_1(f_+, \sigma) = \Sigma_\mathrm{obs} = \int\sigma(\theta)f_+(\theta)f_+(\theta)^*d\theta$
(Kalman-Bucy observation Gramian)

**Right backward** $g_2(P, \sigma) = P_-[K(\theta)\cdot\sigma(\theta)] \in (H^2)^\perp$

### Key identity: Szego-Kolmogorov spectral factorization + Kalman observation Gramian.

### Technical gap: AS lifting from scalar to $L^2(\mathbb{T})$.

---

## T6: $e_3 \cdot e_4 = e_7$ (LP × HC = AS) — Momentum Linearization

**Status: Tier B (strong construction)**

### Physical intuition
Lie-Poisson momentum (LP) + Hopf-Cole linearization (HC) → optimal contact schedule (AS).
This is the Pontryagin maximum principle on contact variables.
Mediator: Lie bracket $[\cdot,\cdot]$.

### Maps
**Forward** $f(\xi, V) = \beta_k = \langle u^*, S_k\rangle = 2\varepsilon\langle\nabla_\mathfrak{g}\log\psi, S_k\rangle$
(optimal control projected onto joint axis $k$)

**Left backward** $g_1(V, \sigma) = \mu = d_\mathfrak{g}V = -2\varepsilon d_\mathfrak{g}\log\psi$
(costate / momentum)

**Right backward** $g_2(\xi, \sigma) = \psi$ satisfying:
$\partial_t\psi + \mathcal{L}_\xi\psi = -(q(\sigma)/(2\varepsilon))\psi$
(transport + killing)

### Adjunction verification
$$r_7(\beta_k, \sigma_k) = 2\varepsilon\langle\nabla_\mathfrak{g}\log\psi, S_k\rangle\cdot\sigma_k$$
$$r_3(\xi, \mu) = \langle\mu, \xi\rangle = \langle d_\mathfrak{g}V, \xi\rangle = -2\varepsilon\frac{\mathcal{L}_\xi\psi}{\psi}$$

Under joint-space reduction ($\xi$ decomposed to $\{S_k\}$):
$$\langle\mu,\xi\rangle = \sum_k\langle\mu,S_k\rangle\cdot\sigma_k\langle\xi,S_k\rangle$$

$r_4(V,\psi) = \int\psi e^{V/(2\varepsilon)}d\mu_G = \mathrm{vol}(G)$ (normalization).

### Key identity: Pontryagin maximum principle + Hopf-Cole chain rule $V = -2\varepsilon\log\psi$.

---

## T7: $e_3 \cdot e_6 = e_5$ (LP × PW = Ha) — Coadjoint Orbit Causality

**Status: Tier B- (needs lifting argument)**

### Physical intuition
Lie-Poisson momentum (LP) + Peter-Weyl spectral decomposition (PW) → Hardy causal
structure (Ha). The heat kernel on compact $G$ is inherently causal: Peter-Weyl
coefficients $e^{-\lambda_\rho t}$ decay exponentially for $t > 0$, which is the
defining feature of $H^2$ (positive frequency = forward time = causal).
Mediator: conjugation (adjoint action $\mathrm{Ad}_g$).

### Maps
**Forward** $f(\xi, v) = P_+[\sum_\rho d_\rho v^*(\rho(e^{\xi\theta})v)] \in H^2$
(matrix coefficient of flow along $\xi$, causal projection)

**Left backward** $g_1(v, f_-) = \mu$ defined by:
$\langle\mu, Y\rangle = \int_\mathbb{T} f_-(\theta)\cdot v^*(d\rho(Y)v)d\theta \quad \forall Y \in \mathfrak{g}$

**Right backward** $g_2(\xi, f_-) = v^* = \int_\mathbb{T} f_-(\theta)\cdot\rho^*(e^{-\xi\theta})d\theta$

### Adjunction verification
Two classical results combine:
1. **Schur orthogonality**: $\int_G\rho_{ij}(g)\overline{\rho'_{kl}(g)}d\mu_G = \delta_{\rho\rho'}\delta_{ik}\delta_{jl}/d_\rho$
2. **Heat kernel causality**: $e^{-\lambda_\rho t}$ supported on positive half-line → Hardy space

### Key identity: Schur orthogonality + heat semigroup causality (Laplace support on half-plane).

---

## Rigor Summary

| Triad | Key Identity | Tier | Status |
|-------|-------------|------|--------|
| T1 BB×Ri=LP | D'Alembert virtual work | A (complete) | In paper |
| T2 BB×HC=Ha | Strong Szego limit theorem | B (strong) | Ready to write |
| T6 LP×HC=AS | Pontryagin + Hopf-Cole chain rule | B (strong) | Ready to write |
| T4 Ri×HC=PW | Schur orthogonality + LQR equipartition | B- (needs lifting) | Needs details |
| T7 LP×PW=Ha | Schur orthogonality + heat causality | B- (needs lifting) | Needs details |
| T3 BB×AS=PW | Fourier inversion + barrier-logit | C (reasonable) | Needs func. space |
| T5 Ri×Ha=AS | Spectral factorization + Kalman Gramian | C (reasonable) | Needs func. space |

## Recommended paper strategy
1. **Immediately writable**: T1 (done) + T2 + T6 → three fully constructed triads
2. **Short-term**: T4 + T7 → lift finite-dim Schur orthogonality to gait space
3. **Needs more work**: T3 + T5 → AS scalar-to-function-space lifting is key obstacle
