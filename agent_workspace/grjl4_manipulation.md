# GRJL 4 — General Manipulation as Tool Using

**Date:** 2026-03-02
**Status:** Draft specification
**Depends on:** threebody.tex (Appendix J), framework.tex (Ch. 2),
meanfield.tex (Ch. 4), calculus.tex (Ch. 7)

---

## 0. The claim

Every manipulation task decomposes into five phases:
**pick -- load -- use -- unload -- place**.

This decomposition is not a design choice. It is forced by
the contact phase structure ($\rho$ crossing $\Sigma$ twice)
and the operator algebra of the task (RANK = Re, NULL = Im).

The five phases instantiate the paper's existing machinery:
sword lifecycle, bang-singular arcs, force elimination,
Kalman duality. No new axioms are needed.

---

## 1. The three-layer state machine

Three simultaneous views of the same process:

```
Phase:    |  1          |  2                |  3               |  4                |  5          |
          | [t_0, t_1)  | [t_1, t_2)        | [t_2, t_3)       | [t_3, t_4)        | [t_4, t_5) |
----------|-------------|-------------------|------------------|-------------------|-------------|
TASK:     | Start       | Preparing          | Executing        | Finishing          | End        |
OBJECT:   | Not moving  | Contact trans. IN  | Controlled       | Contact trans. OUT | Not moving |
ROBOT:    | Not touching| Establishing       | Form closure     | Breaking contact   | Not touching|
          |             | contact            | (cage the object)|                   |             |
----------|-------------|-------------------|------------------|-------------------|-------------|
ρ:        | < 1         | = 1 (crossing ↑)   | > 1              | = 1 (crossing ↓)  | < 1        |
λ₁:       | —           | transient          | ≥ ε              | transient          | —          |
Arc type: | singular    | bang               | singular (prod.) | bang               | singular   |
```

### Connection to threebody.tex

This is the dribble state machine (fig:dribble, line 886) generalised:

| Dribble | Manipulation | Shared structure |
|---------|-------------|-----------------|
| Ball in free flight | Object not moving | Singular arc, $\rho < 1$ |
| Hand strikes ball | Robot establishes contact | Bang arc at $\Sigma$: $\rho = 1$ |
| Ball on hand (bounce) | Object in form closure | $\rho > 1$, $\lambda_1 \geq \epsilon$ |
| Ball leaves hand | Robot breaks contact | Bang arc at $\Sigma$: $\rho = 1$ |
| Ball in free flight | Object placed | Singular arc, $\rho < 1$ |

The dribble has *symmetric* $\Sigma$-crossings (same surface entered
and exited). Manipulation has *asymmetric* crossings: the object starts
at one pose and ends at another. This asymmetry is the task.

### Connection to the sword lifecycle (thm:lifecycle)

Map the manipulation phases onto the sword lifecycle:

| Lifecycle phase | Manipulation phase | Mechanism |
|----------------|-------------------|-----------|
| Pre-sword | Phase 1 (start) | Object free, $U_r = \varnothing$ |
| Sword creation | Phase 2 (contact IN) | Object gains actuation through contact; condition (1) of def:sword activates |
| Sword resolution (a): absorption | Phase 3 (form closure) | Object absorbed into robot's execution graph; $\kappa$ controls $r$ |
| Sword resolution (b): release | Phase 4 (contact OUT) | Object released; condition (1) deactivates |
| Post-sword | Phase 5 (end) | Object free at new pose |

The critical insight: in manipulation, the robot *deliberately creates*
a sword (contact = the object acquires autonomous actuation relative to
the robot) and then *deliberately resolves* it (form closure = absorption;
release = condition (1) deactivated). The sword lifecycle is not a threat
to be survived — it is a tool to be wielded.

---

## 2. The operator sequence

### Task-space operators

Each phase has an associated operator on the state space:

```
Phase:     |  1      |  2      |  3      |  4          |  5          |
Operator:  |  T₀     |  T₁     |  T*     |  T₁⁻¹      |  T₀⁻¹      |
Robot act: |  pick   |  load   |  use    |  unload     |  place      |
```

**Interpretation:**

- **$T_0$ (pick):** Approach operator. Moves the robot from home
  configuration to pre-grasp pose. Acts on robot state only;
  object unchanged. Essentially free (no contact forces).

- **$T_1$ (load):** Contact-building operator. Establishes form closure.
  Crosses $\Sigma$ upward ($\rho: < 1 \to > 1$). Builds up $\lambda_1$
  from 0 to $\geq \epsilon$. This is the bang arc: maximum control
  authority deployed to establish spectral gap.

- **$T^*$ (use):** The adjoint. The "productive" operator. With
  contact established ($\rho > 1$, $\lambda_1 \geq \epsilon$), the
  robot uses the object as a tool — or moves the object to the target.
  *Why the adjoint?* Because $T_1$ maps forces to motions (building
  the grasp), and $T^*$ maps motions to forces (using the grasp to
  do work). The adjoint reverses the direction of the force-motion
  duality. In Kalman terms (thm:3b-kalman): $T_1$ is observability
  (sensing contact), $T^*$ is controllability (exploiting contact).

- **$T_1^{-1}$ (unload):** Inverse of loading. Releases the grasp.
  Crosses $\Sigma$ downward ($\rho: > 1 \to < 1$). $\lambda_1$
  drops below $\epsilon$. Another bang arc.

- **$T_0^{-1}$ (place):** Return operator. The robot deposits the
  object at its target and **retracts to the initial joint
  configuration $q_0$**. The robot cycle closes:

  $$q_0 \xrightarrow{T_0} q_{\text{grasp}} \xrightarrow{T_1} q_{\text{ready}} \xrightarrow{T^*} q_{\text{done}} \xrightarrow{T_1^{-1}} q_{\text{release}} \xrightarrow{T_0^{-1}} q_0$$

  This is genuinely $T_0^{-1}$ (not $T_2^{-1}$): the robot reverses
  the approach motion. The operator sequence is a **loop in joint
  space**, making each per-block cycle self-contained.

### Irreversibility is in the object, not the robot

The robot returns to $q_0$ — the cycle closes in **robot state**.
But the composite operator on the **object** is not the identity:

$$\pi_{\text{obj}} \circ (T_0^{-1} \circ T_1^{-1} \circ T^* \circ T_1 \circ T_0) \neq \mathrm{Id}_{\text{obj}}$$

The object has moved from $g_{\text{init}} \in SE(3)$ to
$g_{\text{target}} \in SE(3)$. Irreversibility lives in the object
space, not in the robot space. This is the manipulation analogue of
the paper's temporal irreversibility: the pawn-to-sword transition
is hysteretic (rem:dumu-irreversibility), and in manipulation, the
object's pose change is the irreversible residue of the cycle.

The **separation of concerns** is clean:
- Robot: cyclic ($q_0 \to q_0$). Each block cycle is identical in
  joint-space topology. The upper-level planner only issues
  "do block $k$" — the cycle is self-contained.
- Object: irreversible ($g_{\text{init}} \to g_{\text{target}}$).
  The object accumulates state changes across cycles.
- $\rho$ trajectory: cyclic ($0 \to 1 \to {>}1 \to 1 \to 0$).
  Maps exactly onto pick→load→use→unload→place.

### Connection to the three-term decomposition (thm:3b-damper)

The five-phase operator sequence decomposes into the three-term
structure at each phase:

| Phase | Term (I): Gravity | Term (II): Least action | Term (III): Spectral kick |
|-------|-------------------|------------------------|--------------------------|
| 1 (pick) | Gravity on object | Robot follows minimum-energy path | — (no contact) |
| 2 (load) | Gravity pulls object away | Robot tracks approach trajectory | Hand strikes at $\Sigma$: establish $\lambda_1$ |
| 3 (use) | Gravity on object+robot | Minimum-energy manipulation trajectory | Maintain $\lambda_1 \geq \epsilon$ via grasp adjustment |
| 4 (unload) | Gravity on object | Robot follows release trajectory | Controlled release at $\Sigma$ |
| 5 (place) | Gravity on object | Robot retreats | — (no contact) |

Phases 1 and 5 are purely singular arcs (Term III = 0).
Phases 2 and 4 are bang arcs (Term III active at $\Sigma$).
Phase 3 is a singular arc with spectral maintenance.

---

## 3. The RANK/NULL decomposition: Re and Im

### The task Jacobian

Let $q \in \mathbb{R}^n$ be the robot's joint configuration and
$x_\mathrm{task} \in \mathbb{R}^m$ be the task-space coordinates
(e.g., object pose). The task Jacobian is

$$J(q) = \frac{\partial x_\mathrm{task}}{\partial q}, \qquad \dot{x}_\mathrm{task} = J(q)\,\dot{q}.$$

The fundamental theorem of linear algebra splits the joint space:

$$\mathbb{R}^n = \underbrace{\mathrm{Range}(J^\top)}_{\text{RANK: task-relevant}} \oplus \underbrace{\mathrm{Null}(J)}_{\text{NULL: self-motion}}$$

### The Re/Im identification

| Subspace | Robotics meaning | Operator role | T = S + A role | Energy effect |
|----------|-----------------|---------------|----------------|---------------|
| RANK$(J^\top)$ | Joint motions that produce task-space motion | Forces that do work on the object | **Real part $S$** (self-adjoint) | Changes task energy |
| NULL$(J)$ | Joint motions with zero task-space effect | Internal reconfiguration | **Imaginary part $A$** (skew-self-adjoint) | Preserves task energy |

**Why this identification is correct:**

1. **$S$ (RANK) is self-adjoint:** The task forces $\tau_\mathrm{task} = J^\top F$
   satisfy $\langle \tau_\mathrm{task}, \dot{q} \rangle = \langle F, J\dot{q} \rangle = \langle F, \dot{x}_\mathrm{task} \rangle$.
   This is the power delivered to the task — real work, changing the
   object's energy state. The inner product is symmetric: the force-motion
   pairing is self-adjoint.

2. **$A$ (NULL) is skew-self-adjoint:** Null-space motions $\dot{q}_\mathrm{null} \in \mathrm{Null}(J)$
   satisfy $J \dot{q}_\mathrm{null} = 0$, so they do zero work on the task.
   They reconfigure the robot internally without affecting the object.
   In the Hamiltonian formulation, these are the directions conjugate to
   cyclic coordinates — the "imaginary" directions that circulate energy
   without dissipating it.

3. **The commutator $[S, A]$:** This measures the coupling between
   task-space forces and null-space motions. When $[S,A] = 0$, the
   task and null spaces decouple — changing the grasp configuration
   doesn't affect the force distribution. This is a *power grasp*:
   fingers locked, no dexterity.

   When $[S,A] \neq 0$, null-space reconfiguration changes the
   force distribution — this is *dexterous manipulation*. The
   non-commutativity is the mechanism by which finger repositioning
   (null-space) modulates contact forces (task-space).

### Connection to spectral gap

The spectral gap $\lambda_1$ of the contact graph Laplacian $L_G$
is maintained by the non-commutativity $[S,A] \neq 0$:

- **$[S,A] = 0$ (power grasp):** The grasp is rigid. $\lambda_1$ is
  fixed by the geometry. No adaptation possible. If $\lambda_1$
  drops (e.g., object slips), the robot cannot compensate without
  breaking and re-establishing contact.

- **$[S,A] \neq 0$ (dexterous grasp):** The robot can modulate
  $\lambda_1$ via null-space motions. Finger repositioning changes
  contact normals, which changes the Laplacian weights, which
  changes $\lambda_1$. The spectral gap is *actively maintained*.

This is exactly the mechanism of thm:3b-damper, Term (III):
the spectral kick $\nabla_{q_*}\lambda_1$ is the gradient in
the direction that most increases $\lambda_1$. In manipulation,
this gradient has components in both RANK (push harder) and NULL
(reposition fingers). The non-commutativity $[S,A] \neq 0$ is
what makes the NULL component useful.

### Connection to the paper's existing framework

| Paper concept | Manipulation instantiation |
|--------------|---------------------------|
| Mean field $\bar{U}$ (thm:meanfield) | Average contact force across all fingers |
| Sword = deviation from mean | Finger with anomalous force (slipping, overloaded) |
| Detection $\Obs$ (prop:detection-derivation) | Tactile/proprioceptive sensing of contact forces |
| Bandwidth $B$ | Number of fingers with force sensors |
| Bypass capacity $c(e_r)$ (lem:capacity) | Excess force a finger can exert without coordination |
| Flow-cut (thm:flowcut) | Max manipulable load = min-cut of contact graph |
| Kakeya condition (prop:3b-kakeya) | Minimum finger force for stable grasp: $\bar{u}^* > 0$ strictly |

---

## 4. Force elimination in manipulation

The force elimination theorem (thm:3b-force-elim) applies directly.

**In dribbling:**
$$\rho(t) = \left|\frac{\ddot{q}_z}{g} + 1\right|$$

**In manipulation (general EL system):**
$$\rho(t) = \frac{[M(q)\ddot{q}]_\mathrm{contact}}{[M(q)\ddot{q}]_\mathrm{gravity}}$$

The force is recovered from kinematics: $\tau_\mathrm{ext}(t) = M(q(t))\ddot{q}(t)$.
No force sensor is needed. The contact mode ($\rho < 1$, $\rho = 1$,
$\rho > 1$) is determined entirely by $(q, \dot{q}, \ddot{q})$.

This is the grjl3 breakthrough applied to manipulation: the entire
five-phase state machine is observable from kinematics alone. The robot
does not need to measure contact forces — it reads them from
joint accelerations via the mass matrix.

**Implication for the operator sequence:**
- $T_1$ (load): $\rho$ crosses 1 upward. Detectable from $\ddot{q}$.
- $T^*$ (use): $\rho > 1$ maintained. Monitorable from $\ddot{q}$.
- $T_1^{-1}$ (unload): $\rho$ crosses 1 downward. Detectable from $\ddot{q}$.

The $\Sigma$-crossing events are *kinematically observable* —
they are facts about acceleration, not about force.

---

## 5. Agenticity in manipulation

The agenticity definition (def:agenticity) instantiates as:

### (A) Observability

The object $r$ is spectrally visible: perturbations to $r$'s state
produce detectable changes in $\lambda_1$.

**Manipulation:** When a finger's contact with the object is perturbed
(e.g., the object shifts), the contact Laplacian $L_G$ changes, and
$\lambda_1$ changes. If the robot has sufficient proprioceptive
sensing (observability Gramian $W_O \succ 0$ on $r$'s coordinates),
it detects the perturbation.

### (B) Reachability

The reachable set $\mathcal{R}(T, \mathcal{U})$ of the robot hand
$\kappa$ intersects the set of states where $\kappa$ can influence
the object's contact edge weight $w_{\kappa r}$.

**Manipulation:** The robot can reach configurations where its
fingers make contact with the object. The dynamics $A$ (gravity +
manipulator dynamics) determines the reachable set. Heavier objects
shrink $\mathcal{R}$; longer arms expand it.

### (C) Controllability

The controllability Gramian $W_C \succ 0$ on the subspace coupling
$\kappa$ to $r$.

**Manipulation:** The robot can modulate the contact forces
(equivalently, the edge weights $w_{\kappa r}$) through joint
torques. This requires the contact Jacobian $J_c$ to have
sufficient rank — i.e., the fingers must not all push in the
same direction.

### Kalman duality (thm:3b-kalman)

The ability to detect a contact change (observability) is dual to
the ability to compensate for it (controllability). The dynamics
$A$ is the bridge:

- Forward: perturbation at object $\to$ propagation through
  contact dynamics $\to$ observable at joints.
- Backward: control at joints $\to$ propagation through
  contact dynamics $\to$ force change at object.

Same matrix $A$, transposed. Same $\nabla_{\hat{\omega}} P$.

---

## 6. The OT-control connection (from DeepSeek conversation)

The five-phase manipulation decomposes into an optimal transport
problem (pool/deepseek_ot_control_2026-03-01.md, §1):

$$
\min_{v} \; \mathbb{E}_{X_0 \sim \mu_0}\!\left[
  \int_0^T L(X_t, v(X_t,t))\,dt + \Psi(X_T)
\right]
\quad\text{s.t.}\quad
\partial_t \mu_t + \nabla_x \cdot (\mu_t v_t) = 0
$$

where:
- $\mu_0$ = initial distribution over object poses (randomised for
  generalisation)
- $\mu_T$ = target distribution (goal pose, potentially with
  uncertainty)
- $v_\theta(x,t)$ = learned velocity field (the "disc")
- $u = \mathcal{D}(x, v_\theta)$ = force recovered via inverse dynamics

### Four conditions for task reachability

1. **Kinematic feasibility:** Continuity equation satisfied,
   $\mu_0 \to \mu_T$ achievable.
2. **Mechanical energy:** $\mathcal{J}[v] < \infty$ (finite cost).
3. **Contact feasibility:** During $\rho > 1$ phases, $\lambda_1 \geq \epsilon$.
4. **Information timeliness:** $t_\pi \leq \Delta t$ (control loop
   latency $\leq$ discretisation step).

Condition 4 is the concrete instantiation of the paper's
"high-latency detection" failure mode (discussion.tex, line 19-20):
when $t_\pi > \Delta t$, the king's detection function $\Obs$ has
insufficient bandwidth, and the costate gradient goes stale.

---

## 7. Two-level architecture: randomness buys tractability

### 7.1 Why two levels are forced

The manipulation problem has two fundamentally different
computational structures:

| | Upper level | Lower level |
|---|------------|-------------|
| **Decides** | Which block, which order, which grasp | How to move block from A to B |
| **Space** | Combinatorial: $O(N! \cdot G^N)$ orderings $\times$ grasps | Continuous: $\mathbb{R}^{8}$ joint space $\times$ $[0,T]$ |
| **Smoothness** | Discrete (non-smooth) | Smooth within arcs, non-smooth only at $\Sigma$ |
| **Paper concept** | Detection $\Obs$ (prop:detection-derivation) | Actuation $C(x)$ (five-phase cycle) |
| **Gradient** | Does not exist (combinatorial) | Exists (backprop through ODE) |

A single e2e network would need gradients to flow through
$2N$ switching surfaces ($\Sigma$-crossings) AND through a
combinatorial selection. This is numerically intractable.

### 7.2 The complexity wall

**Upper level — combinatorial explosion:**
- $N$ blocks, each with $G$ candidate grasp poses.
- Stacking DAG constrains ordering, but valid orderings
  can still be $O(N!)$ in the worst case (no dependencies).
- Exhaustive search: $O(N! \cdot G^N)$.
  For $N = 5$, $G = 10$: $12{,}000{,}000$ combinations.

**Lower level — curse of dimensionality:**
- State space: robot (7 DOF) + gripper (1 DOF) + block
  (6 DOF SE(3)) = 14 dimensions per block.
- Grid-based coverage of $\mu_0$: $O(k^{14})$ grid points.
  For $k = 10$: $10^{14}$ points. Impossible.

Both walls are exponential. Neither can be broken by
clever algorithms alone.

### 7.3 The exchange: randomness for complexity

**The only way through both walls is sampling.**

This is not an approximation trick — it is a fundamental
complexity-theoretic exchange:

$$\boxed{\text{Time} \times \text{Space} \;\longleftrightarrow\; \text{Randomness}}$$

At each level, randomness collapses the exponential:

**Upper level: MPPI over the DAG (discrete sampling)**

Instead of enumerating all $N! \cdot G^N$ plans, sample $K$
candidate plans from a proposal distribution and weight by cost:

$$w^{(k)} = \exp\!\left(-\frac{1}{\eta} \sum_{i=1}^N J_i^{(k)}\right), \qquad \pi_\mathrm{next} = \frac{\sum_k w^{(k)} \pi^{(k)}}{\sum_k w^{(k)}}$$

where $\pi^{(k)}$ is the $k$-th sampled plan (block order +
grasp poses) and $J_i^{(k)}$ is the cost of executing block $i$
under that plan.

This is thm:3b-mppi applied to the task level:
$N! \cdot G^N \to \mathrm{poly}(N, G, K)$. The Cheeger inequality
(prop:3b-mixing) guarantees that MPPI converges in polynomial
mixing time when $\lambda_1 > 0$ on the plan graph.

**Lower level: Particle OT (continuous sampling)**

Instead of gridding the 14D state space, sample $M$ initial
conditions $\{X_0^{(j)}\}_{j=1}^M \sim \mu_0$ and propagate:

$$\hat{\mathcal{J}}(\theta) = \frac{1}{M} \sum_{j=1}^M J(v_\theta; X_0^{(j)})$$

By the strong law of large numbers, $\hat{\mathcal{J}} \to \mathcal{J}$
as $M \to \infty$, regardless of dimension. The curse of
dimensionality is broken: $M$ scales with variance, not with
$\dim(\mathcal{M})$.

This is the convergence guarantee from the OT-control formulation
(pool/deepseek_ot_control_2026-03-01.md, §7): SLLN + uniform
convergence over $\Theta$.

### 7.4 The two-level algorithm

```
UPPER LEVEL (discrete, non-smooth):
  Input:  block set {B₁,...,Bₙ}, initial poses {g⁰ᵢ}, goal poses {g*ᵢ}
  Output: execution plan π = [(block_id, grasp_pose, slot)]

  1. Build dependency DAG G_task from goal config
  2. Sample K candidate plans from valid topological orders
  3. For each plan π⁽ᵏ⁾:
       For each block Bᵢ in order:
         Evaluate cost Jᵢ⁽ᵏ⁾ via LOWER LEVEL (fast rollout)
  4. Weight plans by Boltzmann: w⁽ᵏ⁾ = exp(-J/η)
  5. Select best plan or resample (MPPI iterate)

LOWER LEVEL (continuous, smooth):
  Input:  block Bᵢ, start pose gᴬ, goal pose gᴮ, grasp pose
  Output: joint trajectory q(t), t ∈ [t₀, t₅]

  1. Phase 1 (pick):   q(t) ← v_θ(x,t) integrated, ρ < 1
  2. Phase 2 (load):   close gripper until ρ crosses 1 ↑
  3. Phase 3 (use):    move to gᴮ, maintain λ₁ ≥ ε
  4. Phase 4 (unload): open gripper until ρ crosses 1 ↓
  5. Phase 5 (place):  retreat, ρ < 1

  Force recovered: u = D(x, v_θ(x,t))
  ρ from kinematics: ρ = ||M(q)q̈||_contact / ||M(q)q̈||_gravity
```

### 7.5 Why this is the ONLY way

The claim is not "sampling is a good heuristic." The claim is
stronger: **no deterministic algorithm can solve both levels
in polynomial time**.

**Upper level:** Plan selection over DAGs with costs is a
stochastic shortest-path problem. When costs depend on
execution (the cost of placing $B_2$ depends on where $B_1$
ended up), the problem is adaptive — future costs depend on
past outcomes. Deterministic dynamic programming requires
$O(|\mathrm{states}|)$ which is exponential in $N$.
Sampling collapses this to $O(K \cdot N)$ per iteration.

**Lower level:** The velocity field $v_\theta$ must generalise
over $\mu_0$ (all possible initial poses). A deterministic
approach would require covering the support of $\mu_0$, which
is exponential in dimension. Sampling from $\mu_0$ gives
$O(M)$ cost independent of dimension.

The exchange is:
- **Deterministic:** $O(\exp(N))$ time, 0 randomness → intractable
- **Randomised:** $O(\mathrm{poly}(N, K, M))$ time, $O(K + M)$ random bits → tractable

This is the same exchange as thm:3b-mppi ($3^n$ modes $\to$ $K$
samples) applied at both levels simultaneously. The paper's
framework already contains this insight; grjl4 instantiates it
for manipulation.

### 7.6 Connection to the paper's detection bandwidth

The king's detection function $\Obs$ has finite bandwidth $B$
(prop:detection-derivation): he can monitor at most $B$ agents
simultaneously. The threshold $\tau(B)$ selects the top-$B$
by deviation from the mean.

In the two-level architecture:
- $B$ at the upper level = number of MPPI samples $K$.
  More samples = better plan selection = lower $\tau$.
- $B$ at the lower level = number of particles $M$.
  More particles = better coverage of $\mu_0$ = lower variance.

Both are finite. Both are chosen to balance compute budget vs.
solution quality. The fundamental limit is information timeliness:
$t_\pi \leq \Delta t$. The total compute for one control cycle
must fit in $\Delta t$:

$$\underbrace{K \cdot N \cdot t_\mathrm{rollout}}_{\text{upper level}} + \underbrace{t_\mathrm{forward}(\theta)}_{\text{lower level}} \leq \Delta t$$

This is the manipulation instantiation of Condition 4
(information timeliness). If MPPI uses too many samples ($K$
too large) or the network is too slow ($t_\mathrm{forward}$ too
large), the control loop misses its deadline, the costate goes
stale, and controllability is lost.

### 7.7 The plan generator

The upper-level MPPI operates on **plans**. A plan is the output
interface between the discrete planner and the continuous executor.

**Definition (Plan).** A plan is an ordered list

$$P = [(b_1, g_1, \gamma_1, d_1), \; (b_2, g_2, \gamma_2, d_2), \; \ldots, \; (b_N, g_N, \gamma_N, d_N)]$$

where each tuple specifies:
- $b_i \in \{1, \ldots, N\}$: block index
- $g_i \in SE(3)$: target pose for block $b_i$
- $\gamma_i \in \Gamma$: grasp type (e.g., top-down, side, angled)
- $d_i \in S^2$: approach direction

**Definition (Feasible plan).** A plan $P$ is feasible if it
satisfies four constraints simultaneously:

| # | Constraint | Formal | Check |
|---|-----------|--------|-------|
| F1 | **Topological** | If $b_j$ rests on $b_k$ in the goal, then $b_k$ appears before $b_j$ in $P$ | Topological sort of DAG |
| F2 | **Stability** | For every prefix $P_{1:i}$, the partial stack is statically stable: $\mathrm{CoM}(P_{1:i}) \in \mathrm{ConvHull}(\mathrm{support}(P_{1:i}))$ | Incremental CoM + support polygon |
| F3 | **Reachability** | The robot can reach $(g_i, \gamma_i, d_i)$ without colliding with $P_{1:i-1}$ | Collision-free IK (fast: analytical for Franka) |
| F4 | **Observable** | Block $b_i$ is within the camera's FOV from the pre-grasp pose: $b_i \in D(q_{\mathrm{pre},i})$ | FOV check from wrist camera model (§8) |

**The plan generator** is a function:

$$\mathrm{PlanGen}: \underbrace{G}_{\text{goal config}} \times \underbrace{\xi}_{\text{random seed}} \to P \cup \{\bot\}$$

It returns a feasible plan or $\bot$ (infeasible). The algorithm:

```
PlanGen(G, ξ):
  1. Build DAG from G (topological dependencies)         [F1]
  2. Sample a valid topological order using ξ             [F1]
  3. For i = 1, ..., N:
       Check stability of partial stack P_{1:i}          [F2]
       If unstable: return ⊥
       Check collision-free IK for (g_i, γ_i, d_i)      [F3]
       If unreachable: try alternative (γ_i, d_i); if all fail: return ⊥
       Check FOV visibility of b_i from pre-grasp        [F4]
       If invisible: insert a "look" action (move to see b_i first)
  4. Return P
```

**MPPI uses PlanGen as its rollout model:**

```
for k = 1, ..., K:
    P⁽ᵏ⁾ = PlanGen(G, ξ⁽ᵏ⁾)
    if P⁽ᵏ⁾ = ⊥: J⁽ᵏ⁾ = ∞
    else:        J⁽ᵏ⁾ = Σᵢ cost(P⁽ᵏ⁾ᵢ)   (via lower-level fast rollout)
w⁽ᵏ⁾ = exp(-J⁽ᵏ⁾/η)
P* = argmax_k w⁽ᵏ⁾
```

**Key property:** PlanGen is $O(N)$ per call (linear in block
count). The topological sort is $O(N + E)$ where $E$ = DAG edges.
Stability and IK checks are $O(1)$ per block (incremental). The
$K$ MPPI samples are independent → parallelisable. Total upper-level
cost: $O(K \cdot N)$, matching the complexity claim of §7.3.

**Connection to the paper:** PlanGen is the manipulation
instantiation of the causal envelope computation
$\mathrm{Reach}(x, \mathcal{U}, T)$ from the framework. Each
feasible plan $P$ is a path in the viability kernel $K$. Infeasible
plans ($P = \bot$) are paths that exit $K$ — the partial stack
collapses (F2 violated), the robot can't reach (F3), or the block
is invisible (F4, 夏虫语冰). MPPI searches for the lowest-cost
path that stays within $K$.

---

## 8. The robot observer: causal observability for manipulation

The preceding sections formalise the robot's *actuation* (what it can
do). This section formalises its *observation* (what it can know).
The framework is the causal observability theory of 夏虫语冰
(Covariant Radiative Transport, pool/夏虫语冰.md), instantiated
for the manipulation setting.

### 8.1 The physical setup

A single camera is mounted near the gripper (wrist camera). This is
the detector $W_\tau$ from 夏虫语冰 §3. The instantiation:

| 夏虫语冰 (general) | grjl4 (manipulation) |
|---|---|
| $(M, g)$ spacetime | Task environment $\mathbb{R}^3 \times \mathbb{R}^1$ (flat Minkowski) |
| $P^+$ (null phase space) | Light rays from blocks to camera |
| Observer worldline $\gamma(\tau)$ | Camera pose trajectory (attached to end-effector) |
| $W_\tau$ (detector kernel) | Camera PSF $\times$ pixel response at pose $\gamma(\tau)$ |
| $D_\tau = J^-(S_\tau)$ | **Field of view (FOV)** from current camera pose |
| $P(D_\tau)^c$ (invisible region) | Occluded blocks + blocks outside FOV |
| $T(\theta)$ transfer matrix | Rendering/projection operator (pinhole model + occlusion) |
| $X$ (source) | Block states $\{g_i\} \in SE(3)^N$ + shape/colour |
| $Y$ (measurement) | Image features (depth, RGB, segmentation mask) |
| $\eta$ (nuisance source) | Scene illumination, shadows, reflections |

### 8.2 Theorem 1 instantiation: the FOV boundary

**Causal invisibility for manipulation:** A block $B_k$ with
$\pi_x(\mathrm{supp}(B_k)) \cap D_\tau = \varnothing$ — i.e.,
not in the camera's FOV at time $\tau$ — is **exactly invisible**
to the robot at that instant. No amount of computation or
learning can recover $g_k$ from the image $Y(\tau)$.

This is not an approximation. It is Theorem 1 of 夏虫语冰
applied to flat spacetime: the null geodesics (light rays) from
$B_k$ do not intersect the detector support $S_\tau$.

**Occlusion** is the same mechanism: if block $B_j$ occlude $B_k$,
the light rays from $B_k$ are absorbed before reaching $W_\tau$.
The transfer matrix $T(\theta)$ has a zero block for the occluded
source — exactly the causal sparsity structure.

### 8.3 The coupling: observation requires action

Unlike a fixed external camera, the wrist camera moves with the
robot. The detector support $S_\tau$ depends on the robot state
$q(\tau)$:

$$D_\tau = D(q(\tau)) = \mathrm{FOV}(\gamma(q(\tau)))$$

This creates a fundamental **observation-action coupling**:
- To see block $B_k$, the robot must move to a pose where
  $B_k \in D(q)$.
- To move, the robot needs to know where to go — which requires
  having already observed.
- This is the **active perception loop**: observe → plan → move →
  observe again.

**Connection to the paper's Obs:** This is exactly the detection
function from meanfield.tex (prop:detection-derivation), now
given a physical realisation:

- Detection bandwidth $B$ = camera resolution $\times$ FOV solid angle.
  The camera can "monitor" at most $B$ blocks simultaneously
  (those within FOV at sufficient resolution).
- Detection threshold $\tau(\mathrm{Obs})$ = minimum block size (in
  pixels) required for reliable pose estimation.
- $r \in \mathrm{Im}(\Obs) \iff$ block $r$ occupies $> \tau$ pixels
  in the current image.

### 8.4 Persistent excitation and learnability

**Theorem 2 instantiation:** The transfer matrix $T(\theta)$
(visual-to-state mapping) is learnable by least squares if and
only if the input covariance $\Sigma_X \succ 0$ — i.e., the
camera sees blocks from sufficiently diverse viewpoints.

For the wrist camera, persistent excitation is **automatically
provided** by the pick-place cycle: the robot approaches each
block from a pre-grasp pose, grasps it, lifts it, moves it, and
returns. This trajectory naturally provides diverse viewpoints
of the block and its surroundings.

**Corollary 2 instantiation:** If the camera always views blocks
from the same angle (e.g., always top-down), then $\Sigma_X$ is
singular on the lateral dimensions — and lateral pose is
unidentifiable. The robot must approach from varied angles.

### 8.5 Identifiability quotient

**Theorem 3 instantiation:** The robot can learn block
parameters $\theta$ (pose, shape, material) only up to the
observational equivalence class $[\theta_*]$:

$$\theta \sim \theta' \iff T(\theta) = T(\theta')$$

Concrete consequences:
- **Symmetric blocks:** A cube looks identical from 24 orientations
  (the rotation group of the cube). The robot learns pose only
  up to this 24-fold ambiguity until it makes contact and breaks
  the symmetry via tactile feedback.
- **Identical blocks:** If blocks $B_j$ and $B_k$ are physically
  identical, the robot cannot distinguish them visually. This
  does not matter for stacking (the task is symmetric in block
  identity) but matters for tasks requiring specific block
  placement.
- **Gauge freedom:** The overall scene pose (camera extrinsics)
  is a gauge degree of freedom. The robot learns block poses
  relative to its own frame, not in absolute coordinates.

This is exactly the identifiability quotient $\Theta / {\sim}$
from 夏虫语冰 §7, applied to the manipulation setting.

### 8.6 Information timeliness: Condition 4

The camera frame rate $f_\mathrm{cam}$ must satisfy:

$$t_\pi = 1/f_\mathrm{cam} + t_\mathrm{detect} + t_\mathrm{plan} \leq \Delta t$$

where:
- $t_\mathrm{detect}$ = neural network inference time for block
  detection/pose estimation from the image
- $t_\mathrm{plan}$ = MPPI + velocity field forward pass (from §7)
- $\Delta t$ = control loop period

This is Condition 4 (information timeliness, from
pool/deepseek_ot_control_2026-03-01.md §3) given a concrete
hardware decomposition. The camera's $\sigma$-algebra filtration
$\mathcal{F}_\tau = \sigma(Y(s) : 0 \leq s \leq \tau)$ grows
at rate $f_\mathrm{cam}$; the control loop consumes this
information at rate $1/\Delta t$. If production exceeds
consumption ($f_\mathrm{cam} > 1/\Delta t$ after processing),
the robot is informationally solvent. Otherwise, the costate
gradient goes stale and controllability is lost.

### 8.7 The cognitive boundary for manipulation

Combining all of the above:

**What the robot can know at time $\tau$:**
$$\mathcal{F}_\tau = \sigma\!\left(\{Y(s) : 0 \leq s \leq \tau\} \cup \{q(s), \dot{q}(s) : 0 \leq s \leq \tau\}\right)$$

This includes:
- All past images (visual history)
- All past joint states (proprioceptive history)

**What the robot cannot know:**
- Block states outside the cumulative causal domain
  $D = \bigcup_{\tau \in [0,T]} D(q(\tau))$ (Corollary 1 of 夏虫语冰)
- Block parameters in the null space of $T(\theta)$
  (Corollary 3 of 夏虫语冰)
- Block states that changed after last observation but before
  next observation ($t_\pi$ gap)

The **cognitive boundary** for the robot is the surface
$\partial D$ — the edge of the cumulative FOV. Blocks that have
never been seen are exactly as invisible as ice to the summer
insect.

**The three sensory modalities map to three $\Obs$ channels:**

| Modality | What it detects | Bandwidth | Latency |
|----------|----------------|-----------|---------|
| Vision (wrist camera) | Block pose $g_i \in SE(3)$ | High (megapixels) | Medium ($\sim$30 ms) |
| Proprioception (joint encoders) | Robot state $q, \dot{q}$ | Medium (7 joints) | Low ($\sim$1 ms) |
| Tactile (force/torque at wrist) | Contact forces $F_c$ | Low (6 DOF) | Low ($\sim$1 ms) |

Vision has the highest bandwidth but the highest latency. Tactile
has the lowest bandwidth but the lowest latency. The robot must
fuse all three, weighted by their respective $\tau(\mathrm{Obs})$
thresholds. This is the multi-channel version of the detection
function (eq:detection in meanfield.tex).

---

## 9. Summary: what grjl4 instantiates

| Paper construct | grjl4 instantiation |
|----------------|---------------------|
| Viability kernel $K$ | Set of (robot, object) states where task is feasible |
| King $\kappa$ | Robot hand / manipulator |
| Sword $r$ | Object (acquires actuation via contact) |
| $\rho$ | $F_\mathrm{rep} / F_\mathrm{att}$ at each contact point |
| $\lambda_1$ | Spectral gap of contact graph Laplacian |
| $\Sigma = \{\rho = 1\}$ | Form closure boundary |
| Singular arc | Free motion (phases 1, 3, 5) |
| Bang arc | Contact transition (phases 2, 4) |
| $\bar{U}$ (mean field) | Average contact force across fingers |
| Detection $\Obs$ | Wrist camera (vision) + joint encoders (proprioception) + F/T sensor (tactile) |
| Causal domain $D_\tau$ | Camera FOV at current pose (夏虫语冰 Thm 1) |
| Persistent excitation $\Sigma_X \succ 0$ | Diverse viewpoints from pick-place cycle (夏虫语冰 Thm 2) |
| Identifiability quotient $[\theta_*]$ | Block symmetry group (夏虫语冰 Thm 3) |
| Force elimination | $\rho$ from kinematics: $M(q)\ddot{q}$ decomposition |
| Kalman duality | Detect slip $\Leftrightarrow$ compensate slip, via same $A$ |
| RANK$(J^\top)$ = Re | Task forces (work-doing) |
| NULL$(J)$ = Im | Self-motion (reconfiguration) |
| $[S,A] \neq 0$ | Dexterous manipulation (null-space modulates forces) |
| $[S,A] = 0$ | Power grasp (no internal dexterity) |
| $T_0 \to T_1 \to T^* \to T_1^{-1} \to T_0^{-1}$ | pick-load-use-unload-place |
| Robot cycle closes ($q_0 \to q_0$) | Object irreversible ($g \to g'$) |
| $\bar{u}^* > 0$ (Kakeya) | Minimum grasp force for stable manipulation |

---

## 10. Concrete task: 搭积木 (block stacking)

### 8.1 Task definition

**Given:**
- $N$ rigid blocks $\{B_1, \ldots, B_N\}$, each a rectangular
  cuboid with known dimensions $(l_i, w_i, h_i)$ and mass $m_i$.
- Initial poses $\{g_i^0 \in \mathrm{SE}(3)\}_{i=1}^N$, sampled
  randomly on a table surface (positions uniform in workspace,
  orientations uniform in $\mathrm{SO}(3)$ restricted to
  stable resting poses).
- Goal configuration $\{g_i^* \in \mathrm{SE}(3)\}_{i=1}^N$,
  specifying the target pose of each block (e.g., a tower,
  an arch, a wall).

**Goal:** Move all blocks from $\{g_i^0\}$ to $\{g_i^*\}$.

**Success metric:**
$$e_i = \|g_i(T) \ominus g_i^*\|_{\mathrm{SE}(3)}, \qquad \text{task success iff } \max_i\, e_i < \epsilon_\mathrm{goal}$$

where $\ominus$ is the SE(3) logarithmic error and
$\epsilon_\mathrm{goal}$ is the tolerance (e.g., 5 mm / 5 deg).

### 8.2 The robot: Franka Emika Panda

| Property | Value | Consequence |
|----------|-------|-------------|
| Arm DOF | 7 | 1D null space for 6D task |
| Gripper DOF | 1 (parallel jaw, open/close) | Power grasp: $[S,A] \approx 0$ for gripper |
| Total DOF | 8 | RANK = 6 (SE(3)), NULL = 7 - 6 = 1 (elbow) |
| Gripper width | 0--80 mm | Block size must fit |
| Payload | 3 kg | Limits block mass |
| Control rate | 1 kHz | $\Delta t = 0.001$ s, sets $t_\pi$ bound |

**The 1D null space:** The elbow angle $\phi_\mathrm{elbow}$ is the
single self-motion DOF. It parameterises the Im direction:

$$\dot{q}_\mathrm{null} = \alpha \cdot n(q), \quad J(q)\, n(q) = 0, \quad \|n(q)\| = 1$$

where $n(q)$ is the unit null-space vector and $\alpha \in \mathbb{R}$
is the null-space velocity. This is the "imaginary" motion: the elbow
swings, the end-effector stays put.

**Does $[S,A] \neq 0$ for the elbow?** Yes, in general. The elbow
configuration affects:
- Joint torques (via the mass matrix $M(q)$, which depends on $q$
  including elbow angle)
- Singularity proximity (the manipulability ellipsoid rotates
  with the elbow)
- Obstacle avoidance (the elbow sweeps through workspace)

So even though the gripper is a power grasp ($[S,A]_\mathrm{gripper} \approx 0$),
the arm has $[S,A]_\mathrm{arm} \neq 0$ via the elbow self-motion.
The Re/Im decomposition is non-trivial at the arm level.

### 8.3 The execution graph for $N$ blocks

Each block $B_i$ requires one five-phase cycle. But blocks have
*stacking dependencies*: $B_j$ cannot be placed at $g_j^*$ if
$B_j$ rests on $B_k$ and $B_k$ is not yet at $g_k^*$.

This defines a **dependency DAG** $G_\mathrm{task} = (V, E)$:
- $V = \{B_1, \ldots, B_N\}$
- $(B_k, B_j) \in E$ iff $B_j$ rests on $B_k$ in the goal
  configuration

The topological sort of $G_\mathrm{task}$ gives the valid
execution orders. This DAG *is* the execution graph
(def:exgraph) of the task, with the robot $\kappa$ as the
king and each block as a resource.

**Example — 3-block tower:**
```
Goal:   [C]      Dependency DAG:  A → B → C
        [B]      (A must be placed first, then B, then C)
        [A]
       ─────
       table
```

Execution: 3 sequential five-phase cycles.
```
Cycle 1 (block A):  T₀ᴬ → T₁ᴬ → T*ᴬ → (T₁ᴬ)⁻¹ → (T₀ᴬ)⁻¹  [robot → q₀]
Cycle 2 (block B):  T₀ᴮ → T₁ᴮ → T*ᴮ → (T₁ᴮ)⁻¹ → (T₀ᴮ)⁻¹  [robot → q₀]
Cycle 3 (block C):  T₀ᶜ → T₁ᶜ → T*ᶜ → (T₁ᶜ)⁻¹ → (T₀ᶜ)⁻¹  [robot → q₀]
```

Each cycle has two $\Sigma$-crossings (contact IN, contact OUT).
Total: $2N$ bang arcs for $N$ blocks.

**The mean field over blocks:** At any time $t$, some blocks are
placed (stable, $\rho = 0$) and some are not yet placed (free,
$\rho = 0$) or being manipulated ($\rho > 1$). The mean
actuation across blocks is

$$\bar{U}_\mathrm{blocks}(t) = \frac{1}{N} \sum_{i=1}^N \|U_{B_i}(t)\|$$

A block being manipulated has $\|U_{B_i}\| > 0$ (the robot gives
it actuation); a free or placed block has $\|U_{B_i}\| = 0$. So
$\bar{U}_\mathrm{blocks}$ is low (at most $1/N$ of max), and the
single manipulated block exceeds the mean — it is a sword.

This is thm:meanfield instantiated: the block being manipulated
is the sword because its actuation deviates from the population
mean. The moment it is placed ($\rho \to 0$), it ceases to be
a sword.

### 8.4 The $\rho$ trajectory for one block cycle

```
ρ(t)
  │
  │         ┌──────────────────────┐
  │         │   Phase 3: ρ > 1     │
  │         │   form closure       │
  │         │   λ₁ ≥ ε             │
  1 ........┤.......................├........ Σ (switching surface)
  │    ╱    │                      │    ╲
  │   ╱     │                      │     ╲
  │  ╱      │                      │      ╲
  0 ╱───────┘                      └───────╲──────
  │ Phase 1  Phase 2               Phase 4  Phase 5
  │ ρ = 0   ρ ↑ 1                  ρ ↓ 1   ρ = 0
  └──────────────────────────────────────────────── t
  t₀       t₁      t₂            t₃      t₄      t₅
```

- **$[t_0, t_1)$:** Robot approaches block. $\rho = 0$ (no contact).
  Singular arc. Gravity only.
- **$t_1$:** Gripper contacts block. $\rho$ crosses 1 upward.
  Bang arc. $\lambda_1$ jumps from 0.
- **$[t_1, t_2)$:** Gripper closes. $\rho$ increases.
  $\lambda_1$ builds to $\geq \epsilon$.
- **$[t_2, t_3)$:** Stable grasp. $\rho > 1$, $\lambda_1 \geq \epsilon$.
  Singular arc (productive). Robot moves block to goal.
- **$[t_3, t_4)$:** Gripper opens. $\rho$ decreases toward 1.
  $\lambda_1$ drops toward $\epsilon$.
- **$t_4$:** Block released. $\rho$ crosses 1 downward.
  Bang arc. Block is now placed.
- **$[t_4, t_5)$:** Robot retreats. $\rho = 0$. Singular arc.

The $\rho$ trajectory for $N$ blocks is $N$ such pulses in
sequence (for serial execution) or overlapping (for parallel
execution with multiple arms).

### 8.5 Kinematic $\rho$ for Franka + block

By the force elimination theorem (thm:3b-force-elim):

$$\tau_\mathrm{ext}(t) = M(q(t))\,\ddot{q}(t) + C(q,\dot{q})\dot{q} + g(q) - B\,u_\mathrm{cmd}$$

where $u_\mathrm{cmd}$ is the commanded joint torque. The contact
wrench on the object is the residual:

$$F_\mathrm{contact} = \tau_\mathrm{ext} - \tau_\mathrm{expected}$$

For the Franka, $M(q)$, $C(q,\dot{q})$, $g(q)$ are known
analytically (from the URDF/MuJoCo model). The kinematic $\rho$ is:

$$\rho(t) = \frac{\|F_\mathrm{contact}(t)\|}{m_\mathrm{block} \cdot g}$$

No force/torque sensor needed — $\rho$ is computed from
$(q, \dot{q}, \ddot{q}, u_\mathrm{cmd})$ via the known dynamics.

### 8.6 Contact graph Laplacian for the gripper

The contact graph $G_c$ during form closure:
```
         finger_L ──── block ──── finger_R
                         │
                       table
```

Nodes: {finger_L, finger_R, block, table} (during placement).
Edges: contact pairs, weighted by $w_{ij} = k_n \cdot \rho_{ij}$
where $k_n$ is the contact stiffness and $\rho_{ij}$ is the local
contact force ratio.

The graph Laplacian:
$$L_G = D - W, \quad D_{ii} = \sum_j w_{ij}$$

$\lambda_1(L_G) \geq \epsilon$ iff the grasp is stable (all contacts
active, no slip). When one finger loses contact, $w_{ij} \to 0$ for
that edge, $\lambda_1$ drops, and the grasp fails.

For a 2-finger parallel grasp on a cuboid:
- $\lambda_1 = \min(w_L, w_R)$ (the weakest finger contact)
- $\lambda_1 \geq \epsilon$ iff both fingers maintain sufficient
  normal force
- This is the simplest non-trivial Laplacian (2 edges, 3 nodes)

### 8.7 Distribution formulation

**Training distribution:**
$$\mu_0 = \mathrm{Uniform}(\text{block poses on table}) \otimes \mathrm{Uniform}(\text{goal configs from dataset})$$

**Velocity field:** $v_\theta(x, t)$ maps (robot state, block poses, time)
to desired joint velocities. Trained to minimise:

$$\hat{R}_N(\theta) = \frac{1}{N_\mathrm{train}} \sum_{i=1}^{N_\mathrm{train}} \left[ \sum_{k=0}^{K-1} L(x_k^{(i)}, v_\theta(x_k^{(i)}, t_k)) \Delta t + \Psi(x_K^{(i)}) \right]$$

where $\Psi(x_K) = \sum_{i=1}^N \|g_i(T) \ominus g_i^*\|^2$ is
the SE(3) goal error and $L$ includes the control cost
$\frac{1}{2} u^\top R u$ with $u = \mathcal{D}(x, v_\theta)$.

---

## 10.5. Bi-level formulation: grasping nested within transport

### The observation (from floating-gripper experiments)

The five-phase pick-place cycle (§2) contains an **inner optimisation
problem** that is invisible in the operator notation $T_0 \to T_1 \to
T^* \to T_1^{-1} \to T_0^{-1}$ but dominates the physics.

The outer problem is **trajectory planning**: move the object from
$g^A \in \text{SE}(3)$ to $g^B \in \text{SE}(3)$.

The inner problem is **force closure maintenance**: at every instant
$t \in [t_1, t_4]$ (phases 2–4), the gripper must exert finger
forces $f_L(t), f_R(t)$ such that the contact graph Laplacian's
spectral gap satisfies $\lambda_1(t) \geq \varepsilon$.

These are coupled: the outer trajectory determines the inertial
loads the inner grasp must resist, and the inner grasp's feasibility
constrains the outer trajectory's velocity and acceleration.

### The bi-level programme

$$
\boxed{
\begin{aligned}
\textbf{Outer:} \quad & \min_{v_\theta} \; \mathbb{E}_{X_0 \sim \mu_0}\!\left[\int_0^T L(X_t, v_\theta) \, dt + \Psi(X_T)\right] \\
& \text{s.t.} \quad \partial_t \mu + \nabla \cdot (\mu v_\theta) = 0 \\
& \phantom{\text{s.t.}} \quad \lambda_1^*(t) \geq \varepsilon \quad \forall\, t \in [t_1, t_4] \\[6pt]
\textbf{Inner:} \quad & \lambda_1^*(t) = \max_{f \in \mathcal{F}(t)} \; \lambda_1(L_G(f)) \\
& \text{s.t.} \quad f \in \text{FC}(\mu_s) : \quad
  \sqrt{f_{t1}^2 + f_{t2}^2} \leq \mu_s \, f_n \quad \text{(friction cone)} \\
& \phantom{\text{s.t.}} \quad \sum_i f_i = m(\ddot{x}_\text{des}(t) - g)
  + F_\text{wind}(t) \quad \text{(Newton)} \\
& \phantom{\text{s.t.}} \quad f_n \geq 0 \quad \text{(unilateral contact)}
\end{aligned}
}
$$

where:
- **Outer decision variable:** velocity field $v_\theta(x,t)$
  determining the object trajectory $X_t$
- **Inner decision variable:** finger force distribution
  $f = (f_L, f_R) \in \mathbb{R}^6$ (normal + 2 tangential per finger)
- **Coupling (outer → inner):** The desired acceleration
  $\ddot{x}_\text{des}(t) = \dot{v}_\theta + (v_\theta \cdot \nabla) v_\theta$
  enters the Newton constraint. Fast trajectories
  demand larger $f_n$, which may exceed actuator limits.
- **Coupling (inner → outer):** The outer constraint
  $\lambda_1^*(t) \geq \varepsilon$ restricts the set of feasible
  trajectories. If no force distribution can maintain $\lambda_1 \geq \varepsilon$
  at the commanded acceleration, the trajectory is infeasible.

### Force closure as the inner feasibility set

For a parallel-jaw grasp with friction coefficient $\mu_s$, the
inner problem has a closed-form feasibility condition. The grasp
wrench space (GWS) is:

$$
\mathcal{W}_\text{grasp} = \left\{ w = \sum_{i \in \{L,R\}} J_c^{(i)\top} f_i \;\middle|\; f_i \in \text{FC}_i(\mu_s) \right\}
$$

The object's required wrench at time $t$ is:

$$
w_\text{req}(t) = \begin{pmatrix} m\,\ddot{x}_\text{des}(t) - m g + F_\text{wind}(t) \\ I\,\dot{\omega}_\text{des}(t) \end{pmatrix}
$$

**Force closure holds iff** $w_\text{req}(t) \in \text{int}(\mathcal{W}_\text{grasp})$.

For the parallel-jaw case this simplifies to:

$$
\lambda_1 \geq \varepsilon \quad \Longleftrightarrow \quad
2\mu_s N(t) \geq m\,|\ddot{x}_z(t) + g| + |F_\text{wind}^\perp(t)|
$$

where $N(t)$ is the normal clamping force per finger. The factor
of 2 comes from two symmetric contacts; $|\ddot{x}_z + g|$ is the
net vertical load; $F_\text{wind}^\perp$ is the wind component
perpendicular to the contact normal.

### The velocity constraint (how inner limits outer)

Rearranging the force closure condition for the maximum feasible
vertical acceleration:

$$
|\ddot{x}_z(t)| \leq \frac{2\mu_s N_\text{max} - |F_\text{wind}^\perp(t)|}{m} - g
$$

This is a **state-dependent acceleration bound** on the outer
trajectory. It depends on:
- $N_\text{max}$: maximum normal force the actuator can exert
  (gripper kp × finger displacement limit)
- $\mu_s$: pad-to-block friction coefficient
- $F_\text{wind}^\perp(t)$: current wind perturbation (stochastic)
- $m$: block mass (estimated from lift phase: $\hat{m} = \tau_\text{ext}/g$)

**Consequence:** The outer planner cannot command arbitrarily fast
trajectories. Lift velocity, rotation rate, and descent velocity
are all bounded by the inner problem's feasibility set. This is
the coupling that makes the problem genuinely bi-level, not merely
sequential.

### MuJoCo verification (from floating-gripper experiments)

The floating-gripper test fixture (`scene/floating_gripper.xml`)
verified the bi-level structure empirically:

| Finding | What it demonstrates |
|---------|---------------------|
| Mocap bodies have zero solver velocity → zero friction | The inner problem (friction generation) is **physical**, not numerical. MuJoCo's velocity-level contact solver requires real body velocity to generate friction. |
| Architecture: mocap → weld → dynamic body → fingers | The weld transfers commanded position to a body that participates in the velocity-level solver. Friction is now generated correctly. |
| $2\mu N = 15.2$ N $\gg mg = 0.98$ N (margin) | Force closure is easily satisfied statically. The inner problem becomes non-trivial only under dynamics (inertial loads, wind). |
| Wind at $0.8 mg$ reduces $\lambda_1$ | Wind enters the inner problem as an additive wrench, consuming friction margin. |
| Instantaneous mocap teleport flings the block | Violating the velocity constraint (inner → outer coupling): the acceleration exceeds what the weld + friction can support. Ramped transitions (`_ramp_mocap`) respect the bound. |

### Flow diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    BI-LEVEL PICK-PLACE                          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  OUTER LEVEL: Trajectory Optimisation                     │  │
│  │                                                           │  │
│  │  min_{v_θ}  E[ ∫ L(X,v) dt + Ψ(X_T) ]                  │  │
│  │  s.t. continuity equation                                 │  │
│  │       λ₁*(t) ≥ ε  ∀ t ∈ [t₁, t₄]  ←── from inner       │  │
│  │                                                           │  │
│  │  Decides: object pose trajectory X(t) ∈ SE(3)            │  │
│  │  Outputs: desired acceleration ẍ_des(t)  ───┐            │  │
│  └─────────────────────────────────────────────┼────────────┘  │
│                                                 │               │
│                                                 ▼               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  INNER LEVEL: Force Closure Maintenance                     ││
│  │                                                             ││
│  │  max_f  λ₁(L_G(f))                                        ││
│  │  s.t. friction cone:  |f_t| ≤ μ f_n                       ││
│  │       Newton:  Σf = m(ẍ_des - g) + F_wind                 ││
│  │       unilateral:  f_n ≥ 0                                 ││
│  │                                                             ││
│  │  Decides: finger forces f_L(t), f_R(t)                     ││
│  │  Returns: λ₁*(t) = achievable spectral gap  ───┐           ││
│  └──────────────────────────────────────────────────┼──────────┘│
│                                                      │          │
│                        ┌─────────────────────────────┘          │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  COUPLING                                                   ││
│  │                                                             ││
│  │  Outer → Inner:  ẍ_des(t) sets the required wrench         ││
│  │                  Fast traj → large wrench → harder closure  ││
│  │                                                             ││
│  │  Inner → Outer:  λ₁*(t) ≥ ε constrains feasible ẍ         ││
│  │                  |ẍ_z| ≤ (2μN_max - |F_wind⊥|)/m - g      ││
│  │                                                             ││
│  │  Wind → Inner:   F_wind(t) consumes friction margin        ││
│  │                  Stronger wind → tighter velocity bound     ││
│  │                                                             ││
│  │  Mass → Both:    m̂ estimated during lift (instinct)        ││
│  │                  Enters both Newton eqn and accel bound     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### The three-level nesting (complete picture)

The bi-level pick-place sits *inside* the two-level architecture
of §7. The complete nesting is:

```
LEVEL 0 (discrete): Task planner — MPPI over DAG
  Which block? Which order? Which grasp type?
  Space: O(N! · G^N)  →  K samples
     │
     │  for each block b_i in plan:
     ▼
LEVEL 1 (continuous): Trajectory optimisation — OT velocity field
  How to move block from g^A to g^B?
  Decides: v_θ(x,t) → acceleration profile ẍ_des(t)
     │
     │  at every timestep t:
     ▼
LEVEL 2 (algebraic): Force closure maintenance
  Can the gripper hold the block at this acceleration?
  Decides: finger forces f(t) s.t. 2μN ≥ m|ẍ + g| + |F_wind|
  Returns: λ₁*(t) ≥ ε  (feasible) or < ε (infeasible → replan)
```

Level 2 is the fastest (algebraic, O(1) per timestep).
Level 1 is smooth (gradient-based, differentiable through ODE).
Level 0 is combinatorial (sampling-based, non-differentiable).

The hierarchy matches the paper's detection-actuation separation:
- Level 0 = detection $\mathrm{Obs}$ (what to manipulate)
- Level 1 = actuation $C(x)$ (how to move it)
- Level 2 = viability check (can we hold it?)

### Grasping as a manipulation singularity

Force closure is a **contact singularity** — the $\Sigma$-crossing
creates a topological change in the configuration space.

Before contact ($\rho < 1$): the object has 6 independent DOF in
$\text{SE}(3)$. The relative-motion Jacobian
$J_\text{rel}$ between gripper and object has full rank. The
system is non-singular — gripper and object are independent.

At grasp ($\rho \geq 1$): each frictional point contact constrains
up to 3 DOF (the friction cone spans 3 directions). Two parallel
contacts → up to 6 constraints. The rank of the independent
object-motion space drops:

$$
\text{rank}(G) : \; 0 \;\xrightarrow{\;\Sigma\;}\; 6
\qquad\text{(grasp matrix spans full wrench space)}
$$

| State | rank$(G)$ | Object unconstrained DOF | Physical meaning |
|-------|-----------|--------------------------|------------------|
| Pre-contact ($\rho < 1$) | 0 | 6 (free) | Independent dynamics |
| Partial contact | $0 < r < 6$ | $6-r$ | Can still slide/rotate in unconstrained directions |
| Force closure ($\lambda_1 \geq \varepsilon$) | 6 | 0 (locked) | No independent motion — **complete singularity** |

This is literally a singularity: the object's unconstrained DOF
drops discontinuously from 6 to 0 at $\Sigma$ as the grasp
matrix achieves full rank. The contact constraints merge two
previously independent bodies into one coupled system. The
spectral gap $\lambda_1$ measures the **margin** of the
singularity — how far inside the force-closure manifold the
system sits.

**The "attaching lock" interpretation:** Force closure is a lock
that attaches the object to the gripper. The lock's strength is
$\lambda_1$. Wind and inertial loads attempt to break the lock
(reduce $\lambda_1$). The inner optimisation problem (Level 2)
maintains the lock. The robot *deliberately creates* this
singularity (Phase 2) and *deliberately dissolves* it (Phase 4).

**Connection to the sword lifecycle:** Creating the singularity
= creating the sword. The object acquires actuation (it can now
exert forces on the gripper through the contact — condition (1)
of def:sword). The singularity = the locked state = absorption
(Phase 3). Dissolving the singularity = resolving the sword.
The manipulation cycle is a controlled creation and dissolution
of a contact singularity.

### Connection to the paper's forcing lemma

The inner problem is the manipulation instantiation of
lem:forcing (results.tex). The forcing lemma says: if a sword
persists, the king's compensation cost is unbounded over time.
In manipulation: if the gripper must maintain force closure
indefinitely under stochastic wind, the expected cumulative
friction energy diverges — the gripper must eventually place
the block. The bi-level structure makes this precise: Level 2's
friction margin shrinks under wind, forcing Level 1 to complete
the transport in finite time.

---

## 11. What needs to be built (code-level, for grjl4/)

Following the grjl1 $\to$ grjl2 $\to$ grjl3 progression:

| Module | Purpose | Depends on |
|--------|---------|------------|
| `block_stacking.py` | Main: N-block stacking with five-phase FSM | all below |
| `franka_scene.xml` | MuJoCo scene: Franka Panda + N blocks + table | — |
| `task_jacobian.py` | RANK/NULL decomposition of Franka at 7-DOF, elbow null-space $n(q)$, $[S,A]$ commutator | MuJoCo |
| `kinematic_rho_franka.py` | $\rho$ from Franka's $(q, \dot{q}, \ddot{q}, u)$ via known $M(q)$ | grjl3/kinematic_rho.py |
| `contact_laplacian.py` | $\lambda_1$ of contact graph for parallel-jaw grasp | grjl2/order_parameter.py |
| `five_phase_fsm.py` | State machine: detect phase from $\rho$ trajectory | kinematic_rho_franka.py |
| `plan_generator.py` | PlanGen: goal config $\times$ seed $\to$ feasible plan $P$ (F1-F4 checks) | execution_dag.py, wrist_observer.py |
| `execution_dag.py` | Compute stacking order from goal config (topological sort) | — |
| `ot_velocity_field.py` | Parameterised $v_\theta$ (RBF or MLP), training loop | task_jacobian.py |
| `wrist_observer.py` | Wrist camera: FOV computation, block detection, pose estimation, $\mathcal{F}_\tau$ filtration | MuJoCo camera API |
| `compare_v3_v4.py` | grjl3 dribble vs grjl4 block stacking | both |

### Key verification criteria

- V4.1: Kinematic $\rho$ matches force-sensor $\rho$ within $\mathcal{O}(\Delta t)$
- V4.2: Five phases detected correctly for each block cycle
- V4.3: $\lambda_1 \geq \epsilon$ maintained throughout every Phase 3
- V4.4: RANK = 6, NULL = 1: $J^\top F$ does work, $\dot{q}_\mathrm{null}$ does not
- V4.5: $[S,A]_\mathrm{arm} \neq 0$: elbow reconfiguration changes joint torques
- V4.6: Robot returns to $q_0$ after each cycle; object pose changed ($g \neq g'$)
- V4.7: Dependency DAG respected: $B_j$ not placed before $B_k$ if $B_j$ rests on $B_k$
- V4.8: $N$-block stacking completes for $N = 1, 2, 3$ with $\max_i e_i < 5$ mm
- V4.9: Wrist camera detects all blocks within FOV; blocks outside FOV correctly classified as invisible
- V4.10: Persistent excitation: pose estimation error decreases with diverse viewpoints (Thm 2)

### Milestone progression

### Curriculum: stack height as complexity parameter

The natural curriculum is the **number of layers** $L$ in the stack.
Each level adds exactly one unit of combinatorial and physical
complexity:

| Level $L$ | $N$ blocks | DAG structure | Upper level | Lower level | Paper analogue |
|-----------|-----------|---------------|-------------|-------------|----------------|
| 0 | 1 | trivial (single node) | no planner needed | single 5-phase cycle | Single sword, no mean field |
| 1 | 2 | linear chain ($A \to B$) | deterministic (only one order) | 2 cycles, $q_0 \to q_0$ each | 2-agent system, $\bar{U}$ appears |
| 2 | 3 | branching (2 base + 1 top) | MPPI needed (which base first?) | 3 cycles, stability across stack | Phase transition: which block is the "sword"? |
| 3 | 4-6 | tree / DAG | MPPI essential ($N!$ orderings) | inter-block interference | Full mean-field regime |
| $k$ | $O(k^2)$ | pyramid $k$ layers | $3^n \to K$ samples | stacking tolerance tightens | Scaling limit |

**Three orthogonal complexity axes:**

The full curriculum has three independent axes, each testing a
different capability:

| Axis | Symbol | Tests | Paper analogue |
|------|--------|-------|----------------|
| Stack layers | $L$ | Stability, DAG depth, error amplification | Viability chain depth |
| Block count | $N$ | Mean field $\bar{U}$, MPPI scaling | Number of agents $n$ |
| Block types | $K_\mathrm{type}$ | Observer, identifiability quotient $[\theta_*]$ | Detection threshold $\tau(\mathrm{Obs})$ |

These are **orthogonal** — co-growing them confounds variables.
Explore one axis at a time:

```
Phase 1: Fix L=0, K=1.  Grow N = 1,2,3,4.   (mean field scaling)
Phase 2: Fix N≈L², K=1.  Grow L = 1,2,3.     (stability + DAG)
Phase 3: Fix N=3, L=1.   Grow K = 1,2,3.     (observer + types)
Phase 4: Joint growth.    (N,L,K) together.   (integration)
```

Phase 3 is where the wrist camera's identifiability matters:
- $K=1$ (identical cubes): all blocks in same equivalence class
  $[\theta_*]$. Observer only needs position, not identity.
- $K=2$ (cubes + cylinders): observer must distinguish shape.
  Persistent excitation from diverse viewpoints breaks symmetry.
- $K=3+$ (cubes + cylinders + L-shapes): DAG becomes
  shape-dependent (L-shape can't support a cylinder on top).
  Upper-level MPPI must reason about type compatibility.

**Why this is the right curriculum:**

1. **Monotonic difficulty:** Each layer adds $\geq 1$ block, at least
   one new DAG edge, and tightens the placement tolerance (blocks
   higher up amplify base errors).

2. **Each level tests one new capability:**
   - $L=0$: basic sensorimotor loop (5-phase FSM + observer)
   - $L=1$: sequential planning (DAG + $q_0$ return)
   - $L=2$: combinatorial planning (MPPI) + stability monitoring
   - $L=3+$: scaling + randomness-for-complexity exchange

3. **Natural stopping criterion:** The system "graduates" level $L$
   when it stacks $L$ layers with $\max_i e_i < 5$ mm for $\geq 90\%$
   of random initial configurations.

4. **Connection to the paper's complexity:** Level $L$ has $O(L^2)$
   blocks, so the DAG has $O(L^2)$ nodes and $O(L^2)$ edges. The
   upper-level MPPI search space grows as $O((L^2)!)$. Without
   randomness, this is intractable at $L \geq 3$. With MPPI
   ($K$ samples), it's $O(K \cdot L^2)$ — **polynomial in $L$,
   independent of $(L^2)!$**. This is the complexity exchange
   (§7.3) made concrete.

### Milestone progression (aligned with curriculum)

| Milestone | Curriculum level | Task | Validates |
|-----------|-----------------|------|-----------|
| M1 | $L=0$ | Single block pick-and-place | Five-phase FSM, kinematic $\rho$, $\lambda_1$, wrist camera |
| M2 | $L=0$ | Single block, random initial poses ($\mu_0$) | OT generalisation, persistent excitation |
| M3 | $L=1$ | 2-block stack, fixed initial | DAG, sequential cycles, $q_0$ return |
| M4 | $L=2$ | 3-block pyramid, random initial | MPPI, full pipeline: $\mu_0 \to \mu_T$ via $v_\theta$ |
| M5 | all | RANK/NULL measurement | Elbow self-motion, $[S,A]$ commutator |
| M6 | $L=3$ | 6-block pyramid, random initial | Scaling, randomness-for-complexity exchange |

---

## 12. Open questions

1. **The adjoint $T^*$.** The claim that Phase 3 = $T^*$ (adjoint
   of loading) needs formal verification. In what inner product
   is this adjointness exact? Likely the energy inner product
   $\langle u, v \rangle_M = u^\top M v$, which is the natural
   metric on the configuration space.

2. **Deformable objects.** $\rho$ assumes rigid contact.
   For soft objects, the contact is distributed, not point-wise.
   The spectral gap $\lambda_1$ of the *continuous* contact
   Laplacian (not the graph Laplacian) may be the right quantity.
   Blocks are rigid, so this is deferred.

3. **Parallel execution.** With two arms, two blocks can be
   manipulated simultaneously. The $\rho$ trajectories overlap.
   Does the mean-field $\bar{U}_\mathrm{blocks}$ still work
   when two swords exist at once? (The paper's framework handles
   multiple simultaneous swords — this is a test case.)

4. **Underactuation.** The Franka gripper has 1 DOF (open/close).
   It cannot reorient a block within the grasp. This means
   some goal configurations are unreachable without regrasping
   (put down, regrasp from different angle). Regrasping is
   two five-phase cycles for one block. The execution DAG
   must account for this.

5. **$[S,A]$ quantification.** How to numerically compute the
   commutator $[S,A]$ from MuJoCo data? One approach: compute
   $S = (T + T^\top)/2$ and $A = (T - T^\top)/2$ from the
   linearised dynamics matrix $T = \partial f / \partial x$
   evaluated along the trajectory. Then $\|[S,A]\|_F$ is a
   scalar measure of dexterity.
