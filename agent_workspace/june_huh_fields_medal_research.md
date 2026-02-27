# June Huh -- Fields Medal 2022: Technical Research

## Citation

> "For bringing the ideas of Hodge theory to combinatorics, the proof of the
> Dowling-Wilson conjecture for geometric lattices, the proof of the
> Heron-Rota-Welsh conjecture for matroids, the development of the theory
> of Lorentzian polynomials, and the proof of the strong Mason conjecture."

---

## 1. KEY PAPERS (with arXiv IDs)

| # | Paper | Authors | arXiv | Published |
|---|-------|---------|-------|-----------|
| 1 | Milnor numbers of projective hypersurfaces and the chromatic polynomial of graphs | Huh | [1008.4749](https://arxiv.org/abs/1008.4749) | JAMS 25(3), 907--927, 2012 |
| 2 | Log-concavity of characteristic polynomials and the Bergman fan of matroids | Huh, Katz | [1104.2519](https://arxiv.org/abs/1104.2519) | Math. Ann. 354, 1103--1116, 2012 |
| 3 | Hodge theory for combinatorial geometries | Adiprasito, Huh, Katz | [1511.02888](https://arxiv.org/abs/1511.02888) | Ann. Math. 188(2), 381--452, 2018 |
| 4 | Enumeration of points, lines, planes, etc. | Huh, Wang | [1609.05484](https://arxiv.org/abs/1609.05484) | Acta Math. 218(2), 297--317, 2017 |
| 5 | Combinatorial applications of the Hodge-Riemann relations | Huh | [1711.11176](https://arxiv.org/abs/1711.11176) | Proc. ICM 2018 |
| 6 | Hodge-Riemann relations for Potts model partition functions | Branden, Huh | [1811.01696](https://arxiv.org/abs/1811.01696) | 2018 |
| 7 | Lorentzian polynomials | Branden, Huh | [1902.03719](https://arxiv.org/abs/1902.03719) | Ann. Math. 192(3), 2020 |
| 8 | Singular Hodge theory for combinatorial geometries | Braden, Huh, Matherne, Proudfoot, Wang | [2010.06088](https://arxiv.org/abs/2010.06088) | 2020 |
| 9 | Hodge theory of matroids (survey) | Adiprasito, Huh, Katz | -- | Notices AMS 64(1), 26--30, 2017 |

**Related independent work on Mason's conjecture:**

| # | Paper | Authors | arXiv |
|---|-------|---------|-------|
| 10 | Log-Concave Polynomials III: Mason's Ultra-Log-Concavity Conjecture | Anari, Liu, Oveis Gharan, Vinzant | [1811.01600](https://arxiv.org/abs/1811.01600) |

---

## 2. THE FIVE MAIN RESULTS

### 2.1 Heron-Rota-Welsh Conjecture (log-concavity of characteristic polynomial)

**Conjecture (Heron 1972, Rota 1971, Welsh 1976).** For any matroid M of rank r
on ground set E, the absolute values of the coefficients of the characteristic
polynomial

    chi_M(q) = sum_{k=0}^{r} (-1)^k w_k q^{r-k}

form a log-concave sequence:

    w_k^2 >= w_{k-1} w_{k+1}   for all 0 < k < r.

The coefficients w_k are called the **Whitney numbers of the first kind**. They
are defined by

    w_k = sum_{F: rk(F)=k} |mu(hat{0}, F)|

where the sum is over rank-k flats and mu is the Mobius function of the lattice
of flats.

**History of proof:**
- 2010: Huh proved it for graphical matroids using Milnor numbers [1008.4749]
- 2012: Huh-Katz proved it for all realizable matroids via tropical geometry [1104.2519]
- 2015/2018: Adiprasito-Huh-Katz proved it for ALL matroids [1511.02888]

### 2.2 Dowling-Wilson Conjecture (top-heavy conjecture)

**Conjecture (Dowling-Wilson 1975).** For a matroid M of rank r, let W_k denote
the number of rank-k flats (Whitney numbers of the second kind). Then

    W_k <= W_{r-k}   for all k <= r/2.

That is, the lattice of flats is **top-heavy**: there are at least as many
high-rank flats as low-rank flats.

This generalizes the **de Bruijn-Erdos theorem**: n non-collinear points in the
plane determine at least n lines.

**Proof:**
- 2017: Huh-Wang proved it for all realizable matroids [1609.05484], using the
  decomposition theorem for l-adic intersection complexes.
- 2020: Braden-Huh-Matherne-Proudfoot-Wang proved it for ALL matroids
  [2010.06088], using singular Hodge theory and intersection cohomology of matroids.

### 2.3 Lorentzian Polynomials

**Definition (Branden-Huh 2019).** A homogeneous polynomial f in R[w_1,...,w_n]
of degree d is **Lorentzian** if:

1. All coefficients of f are nonneg.
2. For d = 2: the Hessian matrix H(f) has **exactly one positive eigenvalue**
   at every point of the positive orthant R^n_{>0}.
3. For d > 2: all first partial derivatives df/dw_i are Lorentzian (recursive).

Formally, Lorentzian polynomials L^n_d are closures of strictly Lorentzian
polynomials in the space H^n_d of degree-d homogeneous polynomials with
nonnegative coefficients.

**Key theorem:** The support of a Lorentzian polynomial is an **M-convex set**.
The **M-convexity** (Murota) requires: for any alpha, beta in the support J and
any index i with alpha_i > beta_i, there exists j with alpha_j < beta_j such that
alpha - e_i + e_j in J and beta - e_j + e_i in J.

**Matroid characterization:** Matroids and M-convex sets are characterized by
the Lorentzian property. Tropicalized Lorentzian polynomials coincide with
M-convex functions from discrete convex analysis.

### 2.4 Strong Mason Conjecture

**Mason's Conjecture (1972)** concerns the sequence {I_k(M)} where I_k(M) is
the number of independent sets of size k in a matroid M on n elements.

Three versions of increasing strength:

**Version I (Weak -- log-concavity):**

    I_k^2 >= I_{k-1} I_{k+1}

**Version II (Medium):**

    I_k^2 >= ((k+1)/k) I_{k-1} I_{k+1}

**Version III (Strong -- ultra-log-concavity):**

    I_k^2 / C(n,k)^2  >=  [I_{k-1} / C(n,k-1)] [I_{k+1} / C(n,k+1)]

Equivalently:

    I_k^2 >= ((k+1)/k) ((n-k+1)/(n-k)) I_{k-1} I_{k+1}

**Status:**
- Version I: proved by Adiprasito-Huh-Katz (2015) [1511.02888]
- Version II: proved by Huh-Schroter-Wang (June 2018)
- Version III: proved independently in November 2018 by:
  - Branden-Huh [1811.01696] via Lorentzian polynomials
  - Anari-Liu-Oveis Gharan-Vinzant [1811.01600] via completely log-concave polynomials

### 2.5 Hodge Theory for Combinatorial Geometries

This is the overarching framework. See Section 3 below.

---

## 3. THE KAHLER PACKAGE FOR MATROIDS

### 3.1 The Chow Ring A*(M)

Let M be a (loopless) matroid of rank r+1 on ground set E, with lattice of
flats L(M).

**Definition (Feichtner-Yuzvinsky).** The **Chow ring** is the quotient

    A*(M) = R[x_F : F a nonempty proper flat of M] / (I_M + J_M)

where:

**Linear relations I_M:** For each atom (rank-1 flat, i.e., each element) a in E:

    sum_{F : a in F} x_F  =  sum_{F : b in F} x_F    for all atoms a, b

Equivalently, fixing one atom a_0, for each atom a:

    sum_{F : a in F} x_F  -  sum_{F : a_0 in F} x_F  =  0

**Quadratic (Stanley-Reisner) relations J_M:** For incomparable flats F, F':

    x_F * x_{F'}  =  0   whenever F and F' are incomparable in L(M)

The Chow ring is a graded ring:

    A*(M) = A^0(M) + A^1(M) + ... + A^r(M)

where A^k(M) is spanned by degree-k monomials x_{F_1} x_{F_2} ... x_{F_k}
with F_1 <= F_2 <= ... <= F_k (a chain of flats).

**Origin:** When M is realizable over a field k, A*(M) is the Chow ring of
the **wonderful compactification** (De Concini-Procesi) of the hyperplane
arrangement complement in P^r.

### 3.2 Poincare Duality

There is a canonical **degree map**

    deg : A^r(M) --> R

such that for the top-degree component, deg is an isomorphism A^r(M) ~ R.

**Poincare duality:** The bilinear pairing

    A^k(M) x A^{r-k}(M) --> A^r(M) --deg--> R

is a **perfect pairing** (i.e., nondegenerate) for all 0 <= k <= r.

Consequence: the Hilbert function dim A^k(M) is **palindromic**:

    dim A^k(M) = dim A^{r-k}(M).

### 3.3 Hard Lefschetz Theorem

There exists an element ell in A^1(M) (an "ample class") such that
the multiplication map

    ell^{r-2k} : A^k(M) --> A^{r-k}(M)

is an **isomorphism** for all k <= r/2.

The ample class ell is of the form

    ell = sum_F c_F x_F

where the c_F are chosen to satisfy certain positivity conditions (a "strictly
convex piecewise-linear function on the Bergman fan of M").

**Consequence:** The sequence {dim A^k(M)} is **unimodal**:

    dim A^0 <= dim A^1 <= ... <= dim A^{floor(r/2)}

### 3.4 Hodge-Riemann Relations

Define the **primitive subspace**

    P^k(M) = ker(ell^{r-2k+1} : A^k(M) --> A^{r-k+1}(M))

for k <= r/2. The Hodge-Riemann relations state:

The bilinear form on P^k(M) defined by

    Q(a, b) = (-1)^k deg(a * ell^{r-2k} * b)

is **positive definite**.

**Why this implies log-concavity:** Let a_k = deg(ell^k * alpha^{r-k}) for
some element alpha in A^1(M). By the Hodge-Riemann relations (specifically
their consequence, the Khovanskii-Teissier inequality):

    a_k^2 >= a_{k-1} a_{k+1}.

When alpha is chosen appropriately, the a_k are (up to sign) the coefficients
w_k of the characteristic polynomial. This gives the Heron-Rota-Welsh
conjecture.

### 3.5 How the Characteristic Polynomial Arises

The characteristic polynomial of M is related to the Chow ring via the
**volume polynomial**. Specifically, for a "generic" ample class ell and a
specific element alpha in A^1(M):

    chi_M(q) = sum_{k=0}^{r} (-1)^k w_k q^{r-k}

where the w_k can be expressed as intersection numbers in A*(M):

    w_k = deg(alpha^k * ell^{r-k})

(up to signs and normalization). The Khovanskii-Teissier inequality from the
Hodge-Riemann relations then directly gives w_k^2 >= w_{k-1} w_{k+1}.

### 3.6 Summary: The Kahler Package

In classical algebraic geometry, for a smooth projective variety X of complex
dimension d with Kahler class omega:

| Property | Classical (X smooth proj. variety) | Matroid M (rank r+1) |
|----------|----------------------------------|---------------------|
| Ring | H*(X, R) (cohomology) | A*(M) (Chow ring) |
| Poincare duality | H^k(X) x H^{2d-k}(X) --> R perfect | A^k(M) x A^{r-k}(M) --> R perfect |
| Hard Lefschetz | omega^{d-2k}: H^k --> H^{2d-k} iso | ell^{r-2k}: A^k --> A^{r-k} iso |
| Hodge-Riemann | (-1)^k Q on P^k is positive definite | (-1)^k Q on P^k is positive definite |
| Ample class | Kahler form omega | ell = sum c_F x_F |

The remarkable achievement of Adiprasito-Huh-Katz is proving the entire
Kahler package for a purely combinatorial object (an arbitrary matroid) that
need not arise from any geometric space.

---

## 4. CONNECTION TO GRAPHS

### 4.1 Chromatic Polynomial = Characteristic Polynomial of Cycle Matroid

For a graph G = (V, E), the **cycle matroid** M(G) has:
- Ground set = E (edges of G)
- Independent sets = forests (acyclic edge subsets)
- Rank function: rk(S) = |V| - c(S), where c(S) = number of connected
  components of the subgraph (V, S)
- Flats = unions of connected components of induced subgraphs

**Key identity:** If G is a connected graph with cycle matroid M = M(G):

    P(G, q) = q * chi_M(q)

where P(G, q) is the chromatic polynomial (number of proper q-colorings)
and chi_M(q) is the characteristic polynomial of M.

More generally, if G has c connected components:

    P(G, q) = q^c * chi_M(q)

**Therefore:** The Heron-Rota-Welsh conjecture for the cycle matroid M(G)
directly implies log-concavity of the (absolute values of) coefficients of
the chromatic polynomial P(G, q).

### 4.2 The Tutte Polynomial

The **Tutte polynomial** of a matroid M on ground set E with rank function rk is:

    T_M(x, y) = sum_{A subseteq E} (x-1)^{rk(E) - rk(A)} (y-1)^{|A| - rk(A)}

**Specializations:**

    Characteristic polynomial:  chi_M(q)  = (-1)^{rk(M)} T_M(1-q, 0)

    Chromatic polynomial:       P(G, q)   = (-1)^{|V|-c(G)} q^{c(G)} T_G(1-q, 0)

    Flow polynomial:            F(G, q)   = (-1)^{|E|-|V|+c(G)} T_G(0, 1-q)

    Reliability polynomial:     R(G, p)   = (1-p)^{|E|-|V|+1} p^{|V|-1} T_G(1, 1/(1-p))

    # spanning trees:           tau(G)    = T_G(1, 1)

### 4.3 Log-Concavity and Graph Laplacians

The graph Laplacian L = D - A (D = degree matrix, A = adjacency matrix)
relates to the matroid through the Matrix-Tree theorem:

    Number of spanning trees = (1/n) lambda_1 lambda_2 ... lambda_{n-1}

where 0 = lambda_0 < lambda_1 <= ... <= lambda_{n-1} are the eigenvalues of L.

The chromatic polynomial P(G, q) and the Laplacian spectrum are related but
the connection is indirect:

- P(G, q) counts proper colorings; it depends on the matroid structure of G
- The Laplacian eigenvalues encode metric/spectral information
- For regular graphs of degree d: P(G, q) is related to det(qI - L) through
  the characteristic polynomial of L, but only via a substitution
- The log-concavity of coefficients of P(G, q) (Huh's result) is a purely
  matroidal statement; it cannot be derived from Laplacian spectral analysis

The conceptual link: both P(G, q) and the Laplacian capture the "combinatorial
geometry" of the graph, but via different algebraic encodings.

---

## 5. CONNECTION TO PHASE TRANSITIONS AND STATISTICAL MECHANICS

### 5.1 Potts Model Partition Function

The **q-state Potts model** on a graph G = (V, E) assigns to each vertex v
a spin sigma_v in {1, 2, ..., q}. At inverse temperature beta, the partition
function is:

    Z_Potts(G; q, beta) = sum_{sigma: V --> {1,...,q}} exp(beta * sum_{(u,v) in E} delta(sigma_u, sigma_v))

Setting v = e^beta - 1, we obtain:

    Z_Potts(G; q, v) = sum_{A subseteq E} q^{c(A)} v^{|A|}

where c(A) = number of connected components of subgraph (V, A).

### 5.2 Connection to Tutte Polynomial

The Potts partition function is a **reparametrization of the Tutte polynomial**:

    Z_Potts(G; q, v) = (v)^{|V|-c(G)} q^{c(G)} T_G(1 + q/v, 1 + v)

Or in terms of the **multivariate Tutte polynomial** (Sokal):

    Z_G(q, {w_e}) = sum_{A subseteq E} q^{c(A)} prod_{e in A} w_e

This is defined for arbitrary matroids, not just graphs.

### 5.3 Random Cluster Model (Fortuin-Kasteleyn)

The **random cluster model** with parameters q > 0 and p in [0,1] assigns
to each edge configuration A subseteq E the weight:

    phi_{q,p}(A) = (1/Z) p^{|A|} (1-p)^{|E|-|A|} q^{c(A)}

This is related to the Tutte polynomial by:

    Z_RC(G; q, p) = sum_{A subseteq E} p^{|A|} (1-p)^{|E|-|A|} q^{c(A)}

**Special cases:**
- q = 1: percolation
- q = 2: Ising model
- q = 3, 4, ...: Potts model with q states

### 5.4 How Huh's Results Constrain the Potts Partition Function

**Key theorem (Branden-Huh, arXiv:1811.01696):** For any matroid M, the
homogenized multivariate Tutte polynomial

    Z_M(q, w_1, ..., w_n) = sum_{A subseteq E} q^{rk(E)-rk(A)} prod_{i in A} w_i

is **Lorentzian** whenever 0 < q <= 1.

**Consequences:**

1. The Hessian of any nonzero partial derivative of Z_M has **exactly one
   positive eigenvalue** on the positive orthant (Hodge-Riemann analogue).

2. **Negative dependence** for the random cluster model: When 0 < q <= 1,
   the random cluster measure satisfies:

       Pr(e and f in A) <= 2 Pr(e in A) Pr(f in A)

   for edges e, f. More generally, the measure is **negatively associated**.

3. The **ultra-log-concavity** of independent set counts (Mason's conjecture
   Version III) follows from the Lorentzian property.

### 5.5 Connection to Duminil-Copin's Phase Transition Results

Hugo Duminil-Copin (also 2022 Fields Medal) proved:

- **Sharp phase transition** for the random-cluster model on Z^2:
  - Continuous phase transition for 1 <= q <= 4
  - Discontinuous for q > 4
  - Critical point: p_c(q) = sqrt(q) / (1 + sqrt(q))
  - For q=2 (Ising): beta_c = (1/2) log(1 + sqrt(2)) (Onsager's result)

**The conceptual bridge:**

| Aspect | Huh (combinatorics) | Duminil-Copin (probability) |
|--------|--------------------|-----------------------------|
| Object | Tutte polynomial T_M(x,y) | Random cluster measure phi_{q,p} |
| Setting | Arbitrary finite matroid | Infinite lattice Z^d |
| Tool | Lorentzian polynomials, Hodge theory | Parafermionic observables, RSW |
| Result type | Algebraic inequalities (log-concavity) | Phase transition location and type |
| Parameter regime | 0 < q <= 1 (Lorentzian) | q >= 1 (physical regime) |

**The connection is through the Tutte polynomial / random cluster model:**

1. Both study the same generating function Z(q, v) = sum_A q^{c(A)} v^{|A|}
2. Huh's log-concavity results constrain the *coefficients* of this polynomial
3. Duminil-Copin's results determine the *zeros* and *phase structure* in the
   thermodynamic limit
4. The Potts partition function Z(G; q, v) at the critical point v_c(q) is
   where the phase transition occurs
5. The zeros of Z in the complex (q, v) plane (Lee-Yang theory) constrain
   both the coefficients (Huh) and the phase diagram (Duminil-Copin)

**Caveat:** The parameter regimes are different. Huh's Lorentzian result holds
for 0 < q <= 1, while the physical Potts model has q >= 2 (integer). The
connection is more conceptual than direct: both constrain the same universal
object (the Tutte polynomial) from complementary directions.

However, for the random cluster model with noninteger 0 < q <= 1, Huh's
negative dependence results are directly applicable to the probabilistic
structure of the model.

---

## 6. DISCRETE HODGE THEORY ON GRAPHS

### 6.1 The Chain Complex

Given a simplicial complex K (e.g., the clique complex of a graph G), define:

- **k-chains:** C_k(K) = formal R-linear combinations of oriented k-simplices
  - C_0 = functions on vertices
  - C_1 = functions on (oriented) edges
  - C_2 = functions on (oriented) triangles

### 6.2 Boundary and Coboundary Operators

**Boundary operator** partial_k : C_k --> C_{k-1}:

    partial_1[u, v] = v - u         (for edges)
    partial_2[u, v, w] = [v,w] - [u,w] + [u,v]   (for triangles)

In general: partial_k(sigma) = sum_{i=0}^{k} (-1)^i (i-th face of sigma).

Fundamental property: partial_{k-1} circ partial_k = 0.

**Coboundary operator** delta_k = partial_{k+1}^* (the adjoint):

    delta_k : C^k --> C^{k+1}

This is the discrete analogue of the exterior derivative d on differential forms.

### 6.3 The Hodge Laplacians

The **k-th Hodge Laplacian** is:

    Delta_k = partial_{k+1}^* partial_{k+1} + partial_k partial_k^*
            = delta_k^* delta_k + delta_{k-1} delta_{k-1}^*

or in "up-down" notation:

    Delta_k = L_k^{up} + L_k^{down}

where:
- L_k^{up}  = delta_k^* delta_k   (measures "how much k-chain is a coboundary")
- L_k^{down} = delta_{k-1} delta_{k-1}^*  (measures "how much k-chain is a boundary")

**Special cases for a graph G:**

**0-Laplacian (vertex Laplacian):**

    Delta_0 = partial_1^* partial_1 = B^T B = D - A = L

where B is the incidence matrix, D = diag(deg(v)), A = adjacency matrix.
This is the standard **graph Laplacian**.

**1-Laplacian (edge Laplacian):**

    Delta_1 = partial_2^* partial_2 + partial_1 partial_1^*
            = B_2^T B_2 + B_1 B_1^T

where B_1 = partial_1 (vertex-edge incidence) and B_2 = partial_2
(edge-triangle incidence).

### 6.4 The Hodge Decomposition

**Theorem (Discrete Hodge Decomposition).** The space of k-cochains admits
an orthogonal decomposition:

    C^k = im(delta_{k-1}) + im(partial_{k+1}^*) + ker(Delta_k)
         = (exact k-forms) + (coexact k-forms) + (harmonic k-forms)

Every k-cochain omega decomposes uniquely as:

    omega = delta alpha + partial^* beta + h

where h is harmonic (Delta_k h = 0).

### 6.5 Harmonic Forms and Homology

**Theorem (Discrete Hodge Theorem).**

    ker(Delta_k) = ker(partial_k) intersection ker(delta_k)

and there is a canonical isomorphism:

    ker(Delta_k) ~ H_k(K; R)

The dimension of the space of harmonic k-forms equals the k-th **Betti number**:

    dim ker(Delta_k) = beta_k = dim H_k(K; R)

**For graphs (k=0):**
- ker(Delta_0) = constant functions on each connected component
- dim ker(Delta_0) = number of connected components = beta_0

**For graphs (k=1):**
- ker(Delta_1) = harmonic 1-forms (edge flows that are both divergence-free
  and curl-free)
- dim ker(Delta_1) = beta_1 = |E| - |V| + c = cycle rank (first Betti number)
- These correspond to independent cycles in the graph

### 6.6 Spectral Properties

The eigenvalues of Delta_k are all nonneg (Delta_k is positive semidefinite).

For the graph Laplacian L = Delta_0:
- Eigenvalues: 0 = lambda_0 <= lambda_1 <= ... <= lambda_{n-1}
- lambda_1 > 0 iff G is connected (Fiedler value = algebraic connectivity)
- The spectrum encodes expansion, mixing time, isoperimetry

For higher Hodge Laplacians:
- The spectrum of Delta_k encodes k-dimensional "holes" in the complex
- Multiplicity of zero eigenvalue = beta_k (Betti number)
- Nonzero eigenvalues capture higher-order connectivity

### 6.7 Relation to the Matroid / Huh Framework

The discrete Hodge theory of Section 6 and Huh's Hodge theory for matroids
(Section 3) are conceptually parallel but technically distinct:

| | Discrete Hodge (Eckmann, Lim) | Matroid Hodge (Adiprasito-Huh-Katz) |
|---|---|---|
| Space | C^k(K) (k-cochains on simplicial complex) | A^k(M) (degree-k part of Chow ring) |
| Laplacian | Delta_k = dd* + d*d | No Laplacian; uses Lefschetz operator L_ell |
| Decomposition | C^k = im(d) + im(d*) + ker(Delta) | Lefschetz decomposition via ell |
| Duality | Poincare duality for closed manifolds | Poincare duality for A*(M) |
| Key result | dim ker(Delta_k) = beta_k | Hodge-Riemann bilinear relations |
| Application | Topology, signal processing on graphs | Log-concavity, matroid inequalities |

**Unifying thread:** Both invoke the algebraic structure of a "Hodge-type"
decomposition to extract topological or combinatorial information. In the
classical setting (compact Kahler manifold), both frameworks coincide:
the Hodge Laplacian commutes with the Lefschetz operator, and harmonic
forms carry the Hodge structure.

---

## 7. SYNTHESIS: THE STRUCTURAL HIERARCHY

```
COMPACT KAHLER MANIFOLD X
  |
  |-- H*(X, R) satisfies full Kahler package
  |     (Poincare duality + Hard Lefschetz + Hodge-Riemann)
  |
  +-- Specialize to: smooth toric variety X_Sigma
        |
        |-- H*(X_Sigma) = Chow ring of fan Sigma
        |
        +-- Specialize to: Bergman fan Sigma_M of a REALIZABLE matroid M
              |
              |-- A*(M) = Chow ring of matroid (= Chow ring of toric variety)
              |-- Huh-Katz (2012): log-concavity for realizable matroids
              |
              +-- GENERALIZE to: ARBITRARY matroid M (possibly non-realizable)
                    |
                    |-- Adiprasito-Huh-Katz (2018): Kahler package for A*(M)
                    |   proved by combinatorial arguments (no geometry!)
                    |
                    |-- Application 1: Heron-Rota-Welsh conjecture
                    |-- Application 2: Mason conjecture (Version I)
                    |
                    +-- Braden-Huh-Matherne-Proudfoot-Wang (2020):
                          SINGULAR Hodge theory --> intersection cohomology IH(M)
                          |
                          +-- Application: Dowling-Wilson top-heavy for ALL matroids
                          +-- Application: Nonnegativity of matroid K-L polynomials

PARALLEL TRACK:

LORENTZIAN POLYNOMIALS (Branden-Huh 2019)
  |
  |-- Generalize stable polynomials and volume polynomials
  |-- Hessian has exactly one positive eigenvalue (= Hodge-Riemann analogue)
  |-- Multivariate Tutte polynomial is Lorentzian for 0 < q <= 1
  |
  +-- Application: Mason conjecture (Version III -- ultra-log-concavity)
  +-- Application: Negative dependence for random cluster model
  +-- Application: Constraints on Potts model partition function
```

---

## 8. OPEN DIRECTIONS

1. **Equivariant Kahler package:** Extending Hodge theory to group actions on
   matroids (Berget-Eur-Spink-Tseng, arXiv:2205.05420).

2. **Stellahedral geometry:** Huh-Eur-Larson (2023) realized matroid invariants
   via stellahedral geometry, computing Tutte polynomials from intersection
   theory on permutohedral/stellahedral varieties.

3. **Deeper connections to physics:** The Lorentzian polynomial framework
   applies for 0 < q <= 1, but the physical Potts model lives at q >= 2.
   Extending the theory to q > 1 (or finding analogues) would directly
   constrain physical phase transitions.

4. **Algorithmic implications:** Completely log-concave polynomials led to
   FPRAS (fully polynomial randomized approximation scheme) for counting
   bases of matroids (Anari et al., arXiv:1807.00929).

5. **Higher Hodge theory:** Extending the matroid Hodge theory to more general
   combinatorial structures (lattices, posets, tropical geometry).
