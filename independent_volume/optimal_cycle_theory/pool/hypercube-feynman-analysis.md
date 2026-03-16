# 3-Qubit Hypercube & Feynman Diagram Analysis

## Source: Gemini conversation review
## Status: Under evaluation — separating insight from decoration

---

## The Proposal

Map the 8 Chu objects to vertices of a 3-qubit hypercube $\{0,1\}^3$:

```
|q1 q2 q3⟩   Object              Role
|000⟩         1 = PF (Pontryagin)  identity
|001⟩         e1 = BB (Barrier)    contact constraints
|010⟩         e2 = Ri (Riccati)    optimal feedback
|011⟩         e3 = LP (Lie-Poisson) momentum dynamics
|100⟩         e4 = HC (Hopf-Cole)  linearization bridge
|101⟩         e5 = Ha (Hardy)      causal structure
|110⟩         e6 = PW (Peter-Weyl) spectral decomposition
|111⟩         e7 = AS (Action-State) contact schedule
```

Three axes:
- X (q3): constraint injection — R → C (adjoin e1)
- Y (q2): dynamics injection — C → H (adjoin e2)
- Z (q1): analytic bridge — H → O (adjoin e4)

Fano triads = XOR on qubit labels: $|a⟩ \oplus |b⟩ = |c⟩$.

Edges = Feynman-Kac propagators.

---

## What is genuinely correct

### 1. The XOR structure is a THEOREM, not an analogy

The octonion multiplication table for imaginary units satisfies:
if $e_a \cdot e_b = \pm e_c$, then $a \oplus b = c$ (bitwise XOR in binary).

This is because the Cayley-Dickson construction is literally a doubling that adds
one binary digit at each level. The Fano plane IS the projective plane over $\mathbb{F}_2$,
and its incidence structure IS the XOR relation on $\{1,...,7\}$ in binary.

So the 3-qubit labeling is not an analogy — it's the standard representation theory
of the Fano plane as $PG(2, \mathbb{F}_2)$.

**Reference**: Baez, "The Octonions" (Bull. AMS, 2002), Section 4.

### 2. The Cayley-Dickson splitting H ⊕ He₄ IS the qubit-1 (Z-axis) flip

The paper already identifies:
- H component = {1, e1, e2, e3} = control-loop quaternion = {|0xx⟩}
- He₄ component = {e4, e5, e6, e7} = spectral-analytic quaternion = {|1xx⟩}

Flipping q1 (the Z-axis) sends every control object to its spectral counterpart
via the Hopf-Cole exponential bridge. This is exactly the paper's "doubling unit e4."

### 3. The axes match the paper's "three doublings = three laws"

- X: R → C via e1 (BB) = Newton I (inertia/reference frame)
- Y: C → H via e2 (Ri) = Newton II (F = dp/dt)
- Z: H → O via e4 (HC) = Newton III (action = −reaction)

This is already in chu-duality.tex lines 578-601.

---

## What needs critical scrutiny

### 4. "Edges are Feynman diagrams" — MIXED

**What is correct:**
- The MPPI path integral $w^{(i)} \propto e^{-S[\beta^{(i)}]/\varepsilon}$ has the
  structure of a Feynman-Kac integral. This is a theorem (Section 17 of the paper).
- The parameter ε plays the role of ℏ. As ε → 0, the path integral concentrates
  on the classical path (tree-level). This is Maslov dequantization (already in the paper).
- The Chu morphism's forward/backward arrows DO parallel particle/antiparticle
  propagation (state forward, costate backward).

**What is decoration/overstatement:**
- NOT every edge of the hypercube corresponds to a well-defined Feynman-Kac propagator.
  The 12 edges include 3 axis-parallel edges from each vertex, but only the 7 Fano
  triads (faces/diagonals) have verified physical content. The remaining edges are
  just binary digit flips with no guaranteed physical morphism.
- A Feynman DIAGRAM (in the QFT sense) involves vertices (interactions), internal
  lines (propagators), and external lines (asymptotic states). The hypercube edges
  are at best propagators, not full Feynman diagrams. The TRIADS (faces) are closer
  to Feynman vertices (3-point interactions).
- The claim "holonomy = 1-loop correction" is poetic but imprecise. In QFT, 1-loop
  corrections involve integrating over internal momenta (a specific integral). The
  holonomy H(f) = Σk|c_k|² is a spectral invariant, not a momentum integral.
  The ANALOGY is: both measure the gap between tree-level (classical) and full
  quantum (stochastic) computation. But they are not literally the same mathematical
  object.

### 5. "Vertices are qubit basis states" — CAUTIOUS

The 3-qubit Hilbert space $(\mathbb{C}^2)^{\otimes 3}$ has dimension 8, matching the
8 Chu objects. But:
- Qubits have SUPERPOSITION: $\alpha|0⟩ + \beta|1⟩$. What does a superposition of
  Chu objects mean categorically? In the *-autonomous category, tensor products and
  pars exist, but they are NOT the same as quantum superposition.
- The 3-qubit structure has entanglement classes (GHZ, W, biseparable, product).
  Does this classification have a Chu-theoretic counterpart?
- Without answering these questions, the "qubit" label is a convenient indexing scheme
  (which is fine!) but not a deep quantum-information connection.

### 6. "The optimal cycle is an Eulerian walk on the hypercube" — NEEDS PROOF

An Eulerian walk visits every EDGE exactly once. The 3-cube has 12 edges and every
vertex has degree 3 (odd), so an Eulerian circuit does NOT exist (Euler's theorem
requires all vertices to have even degree). An Eulerian PATH exists only if exactly
2 vertices have odd degree — but ALL 8 vertices of the 3-cube have degree 3 (odd).

Therefore: **no Eulerian walk exists on the 3-cube.** Gemini's claim is
mathematically false.

A HAMILTONIAN path (visiting every vertex exactly once) does exist on the 3-cube
(e.g., Gray code: 000→001→011→010→110→111→101→100). This might be what Gemini
intended, and it's more appropriate: the control algorithm visits each Chu object
once per cycle.

---

## Verdict: What to keep, what to discard

### KEEP (mathematically grounded):
1. The $\mathbb{F}_2^3$ labeling of octonion basis elements (standard, cite Baez)
2. The XOR structure of Fano triads (theorem)
3. The three axes = three Cayley-Dickson doublings = three Newton laws (already in paper)
4. The Z-axis = Hopf-Cole bridge between H and He₄ (already in paper)
5. ε as deformation parameter analogous to ℏ (already in paper, Maslov dequantization)

### DISCARD or REPHRASE:
1. "Edges are Feynman diagrams" → REPHRASE: "Fano triads are 3-point vertices in the
   interaction structure; the Feynman-Kac path integral provides the propagator between
   Chu objects connected by the exponential bridge (Z-axis edges only)."
2. "Holonomy = 1-loop correction" → REPHRASE: "Both H(f) and 1-loop corrections measure
   the gap between deterministic (tree-level) and stochastic (quantum) regimes, but the
   precise relationship requires specifying the loop integration measure."
3. "Eulerian walk" → CORRECT to Hamiltonian path (or more accurately: the algorithm's
   data flow visits specific triads, not a walk on the graph).
4. "Qubit superposition" → DOWNGRADE to "F₂-vector labeling" unless categorical
   superposition is defined.

### INVESTIGATE FURTHER:
1. Does the 3-qubit error-correcting code structure (e.g., Steane code, CSS codes)
   have a Chu-theoretic interpretation? The Fano plane IS the incidence matrix of the
   [7,4,3] Hamming code, which is foundational to quantum error correction.
2. The Fano plane = PG(2, F₂) connection to the [7,4,3] Hamming code could provide
   an information-theoretic interpretation of the seven triads as parity checks.
3. Is there a functorial relationship between Chu(Vect, R) and the category of
   stabilizer states in 3-qubit systems?

---

## Recommended integration into the paper

Add as a Remark (not a theorem) in Section 21:

> **Remark (F₂-labeling and the hypercube).** The identification of octonion basis
> elements with vertices of the 3-cube $\{0,1\}^3$ is standard: the Fano plane is
> the projective plane $PG(2, \mathbb{F}_2)$, and the multiplication rule
> $e_a \cdot e_b = \pm e_c$ satisfies $c = a \oplus b$ (bitwise XOR)
> [Baez, Bull. AMS 2002]. Under this labeling, the three Cayley-Dickson doublings
> correspond to the three coordinate axes, and the Fano triads to faces and body
> diagonals of the cube. The parameter $\varepsilon$ interpolates along the Z-axis
> ($e_4$ = Hopf-Cole), acting as the deformation parameter between the nonlinear
> control domain ($\mathbb{H}$ face, $q_1 = 0$) and the linear spectral domain
> ($\mathbb{H}e_4$ face, $q_1 = 1$)—a categorical analogue of the role of $\hbar$
> in Maslov dequantization (Proposition~\ref{prop:tropical-chu}).

This adds geometric clarity without overclaiming quantum-information connections.
