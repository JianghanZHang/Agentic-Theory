# grjl4 Implementation Plan — Locked Chain

```
P  := Block stacking works end-to-end in MuJoCo, robust to wind
T  := Camera → detect → plan → FSM → v_θ → τ → Franka → blocks move
     + wind → λ₁ drops → FSM detects → replan → rebuild

Fixed point: the XML scene.
Everything downstream is uniquely determined by what the scene contains.
```

---

## Status

| Link | Description | Status |
|------|-------------|--------|
| [0] Scene XML | franka + 4 block types + camera | **DONE** |
| [1] Kinematics | ρ + λ₁ + wind | **DONE** |
| [2] FSM | 5 phases + REPLAN | TODO |
| [3] Observer | wrist camera → block poses (GT mode) | **DONE** (GT); TODO (vision) |
| [4] Planner | DAG + PlanGen + MPPI | TODO |
| [5] Controller | v_θ MLP + inverse dynamics | TODO |
| [6] Training | flow matching + MMD | TODO |
| [7] Curriculum | L × N × K_type × F_max × ρ_mat | TODO |

---

## Problem Formulation: 夏虫运冰 (Block Stacking under Wind)

**Given:**
- N blocks on a table, each with type k ∈ {cube, cuboid, mortise, tenon} and mass m_k (unknown to the robot; may vary across visually identical blocks)
- A parallel-jaw gripper (free-floating for unit tests; Franka-mounted for full pipeline)
- Stochastic horizontal wind F_wind(t) ~ Uniform([0, F_max]) applied to all placed blocks at every timestep

**Objective:**
Stack all N blocks into a stable tower of L layers on a target location, such that the tower survives indefinitely under wind.

**Stability criterion:**
A tower is stable iff for every block i in the stack:

    λ₁_eff(i) ≥ ε

where λ₁ is the smallest nonzero eigenvalue of the contact graph Laplacian (spectral gap), and λ₁_eff = λ₁ − ‖F_wind_perp‖ / (m_i · g).

**Observables (what the robot can measure):**
- ρ(t): contact order parameter — ratio of measured contact force to block weight. ρ ≥ 1 = firm contact, ρ < 1 = slipping, ρ = 0 = no contact
- λ₁(t): spectral gap of the contact graph (computed from contact forces)
- Block poses via vision (DINOv2 encoder) or ground truth
- Mass estimate m̂ from τ_ext during lift (instinct)

**Control:**
- Gripper position (x, y, z) and finger aperture
- 5-phase FSM per block: SEEK → APPROACH → GRASP → TRANSPORT → PLACE (+REPLAN on failure)

**Constraints:**
- Wind is always blowing (F_max > 0 during all training episodes)
- Blocks are picked one at a time
- Mortise-tenon pairs must mate (geometric constraint)
- The robot must discover placement order through interaction (heavy blocks on bottom = more stable, but mass is unknown until touched)

**Curriculum (what gets harder over training):**

| Axis | Symbol | Range | Observable by | Tests |
|------|--------|-------|---------------|-------|
| Layers | L | 1 → 3 | vision | Stability, DAG depth |
| Count | N | 2 → 6 | vision | Mean field, MPPI scaling |
| Types | K_type | cube only → all 4 | vision | Observer, geometric constraints |
| Wind | F_max | 0.05mg → 0.8mg | haptics (λ₁) | Robustness, recovery |
| Density | ρ_mat | uniform → 4× spread | haptics (τ_ext) | Active perception, smart ordering |
| Size | σ_vol | 1.0 → [0.7, 1.3] | vision | Grip aperture, stability geometry |

**Success metric:**
Tower survives T_test seconds of maximum wind after placement. Equivalently: min_i λ₁_eff(i) ≥ ε for all t ∈ [0, T_test].

**First principle:**
Wind is the sole external perturbation — the one and only adversary. Without wind, stacking is pure kinematics (any geometrically correct placement succeeds). Wind is what makes the spectral gap λ₁ non-trivial, what forces the robot to care about grasp quality, placement order, and recovery. All intelligence in the system exists because wind exists.

**Test fixtures:**
- Free-floating gripper (`scene/floating_gripper.xml`): mocap-controlled, no IK. Tests Links 1-3 (ρ, λ₁, wind, observer) in isolation.
- Full Franka arm (`franka_scene.xml`): joint-controlled. Tests Links 4-7 (planner, controller, training, curriculum).

### Bi-level structure within each pick-place cycle

Each 5-phase cycle contains a nested optimisation (see grjl4_manipulation.md §10.5):

```
LEVEL 0: Task planner (MPPI over DAG — which block, which order)
   │
   ▼
LEVEL 1 (outer): Trajectory optimisation
   min_{v_θ}  E[ ∫ L(X,v) dt + Ψ(X_T) ]
   s.t. continuity equation
        λ₁*(t) ≥ ε  ∀ t ∈ [t₁,t₄]  ← from Level 2
   Decides: object trajectory X(t), hence ẍ_des(t)
   │
   ▼
LEVEL 2 (inner): Force closure maintenance
   max_f  λ₁(L_G(f))
   s.t. friction cone:  |f_t| ≤ μ f_n
        Newton:  Σf = m(ẍ_des - g) + F_wind
        unilateral:  f_n ≥ 0
   Decides: finger forces f_L, f_R
   Returns: λ₁* (achievable spectral gap)
```

**Coupling:**
- Outer → Inner: ẍ_des sets the required wrench. Faster traj → larger wrench → harder closure.
- Inner → Outer: feasibility constraint |ẍ_z| ≤ (2μN_max − |F_wind⊥|)/m − g.
- Wind → Inner: F_wind consumes friction margin. Stronger wind → tighter velocity bound.

**For the parallel-jaw gripper**, Level 2 reduces to an algebraic check:

    2μN(t) ≥ m|ẍ_z(t) + g| + |F_wind⊥(t)|

This is O(1) per timestep — no optimisation loop needed, just verify the inequality.

**Verified empirically** (floating_gripper.xml):
- Mocap bodies have zero solver velocity → zero friction → grasp fails (the inner problem is physical)
- Architecture fix: mocap → weld → dynamic body → correct friction generation
- Instantaneous teleport violates the velocity bound → block flung → ramped transitions respect it
- Wind at 0.8mg measurably reduces λ₁ (friction margin consumed)

---

## The Chain

```
[0]  Scene XML ─── franka + 4 block types + table + camera + wind params
      │
[1]  Kinematics ── ρ from (q, dq, ddq, u) + λ₁ from contact graph
      │
[2]  FSM ────────── 5 phases from ρ trajectory + wind recovery
      │
[3]  Observer ───── wrist camera → block poses {gᵢ} (pretrained encoder)
      │
[4]  Planner ────── DAG + PlanGen + MPPI (replan on topple)
      │
[5]  Controller ─── v_θ MLP + inverse dynamics → τ
      │
[6]  Training ───── flow matching + MMD + wind perturbation
      │
[7]  Curriculum ─── L × N × K_type × F_max (4 axes)
```

Each link is uniquely determined by the previous.
You cannot write [1] without [0] (ρ needs M(q) from the URDF).
You cannot write [2] without [1] (FSM needs ρ).
You cannot write [4] without [3] (planner needs detected poses).
You cannot write [5] without [2]+[4] (controller needs phase + plan).
You cannot write [6] without [5] (training needs the network).
You cannot write [7] without [6] (curriculum needs a working trainer).

**Exception:** [3] (observer) depends on [0] (camera in XML) but not on [1] or [2]. It is a parallel branch that merges at [4].

```
[0] ──→ [1] ──→ [2] ──→ ┐
 │                        ├──→ [4] ──→ [5] ──→ [6] ──→ [7]
 └──→ [3] ──────────────→ ┘
```

---

## Link 0: Scene XML — `franka_scene.xml` — DONE

**The fixed point.** Everything starts here. **Completed.**

### 0.1 What it contains

```xml
franka_scene.xml
├── Franka Panda arm (7 DOF + 1 gripper)     ← mujoco_menagerie/franka_emika_panda/panda.xml
├── Ground plane (floor)                      ← infinite plane
├── 2 cameras (overhead + side)               ← for observation
├── 4 block types (1 of each, freejoint)      ← see §0.2
├── Contact parameters (solref, solimp)       ← tuned for stable contact
├── Actuators (position-controlled via panda.xml)
└── Wind (no XML element — applied at runtime via xfrc_applied)
```

MJX variant: `franka_scene_mjx.xml` (implicitfast integrator, box collision Franka).

### 0.2 Block types (K_type = 1..4)

```
Type 1: 正方体 (cube)    — box 4×4×4 cm     — red       mass=0.100 kg
Type 2: 长方体 (cuboid)  — box 4×4×8 cm     — green     mass=0.200 kg
Type 3: 卯 (mortise)     — mesh (2 convex)  — blue      mass=0.088 kg
Type 4: 榫 (tenon)       — mesh (1 convex)  — orange    mass=0.113 kg

Constraint: mesh(3) + mesh(4) = box(2)  [complementary 榫卯 pair]
```

**Mortise convex decomposition:** The mortise is concave (V-notch at bottom).
MuJoCo computes convex hull per mesh, which would erase the notch.
Solution: split into 2 convex right-trapezoid prisms (mortise_L + mortise_R).
Each half's convex hull = itself. Verified via `mjVIS_CONVEXHULL`.

```
Type 3 cross-section (two convex halves):

    ┌───┬───┐  z = +h/2        Type 4 cross-section:
    │   │   │                          ╱╲    z = +h/2 + tab_h
    │   │   │                         ╱  ╲
    │   ╲ ╱ │  z = apex             ┌╱────╲┐  z = +h/2
    │    V   │                      │      │
    └───┘ └──┘  z = -h/2           └──────┘  z = -h/2
    L half R half
```

### 0.3 Design decisions (locked by XML)

| Decision | Value | Rationale |
|----------|-------|-----------|
| Cube size | 4×4×4 cm | Fits in 80mm gripper |
| Cuboid size | 4×4×8 cm | = 2 cubes stacked = mortise + tenon |
| Notch/tab depth | 2 cm | 50% of half-height; visible V-notch |
| Block placement | Diagonal line | No mutual camera occlusion |
| Control timestep | 0.002 s (500 Hz) | Stable contact dynamics |
| Contact params | solref=0.004/0.8, solimp=0.95/0.99/0.001 | Stiff but stable |
| Integrator (CPU) | implicit | Full-featured contact |
| Integrator (MJX) | implicitfast | MJX requirement |

### 0.4 Files created

```
grjl4/
├── franka_scene.xml           ← THE fixed point (CPU MuJoCo)
├── franka_scene_mjx.xml       ← MJX variant (GPU/JAX training)
├── generate_meshes.py         ← generates mortise_L/R + tenon STLs
├── mujoco_menagerie/          ← git submodule (Franka Panda MJCF)
└── assets/
    ├── mortise_L.stl          ← left convex half (8 verts, 12 tris)
    ├── mortise_R.stl          ← right convex half (8 verts, 12 tris)
    ├── tenon.stl              ← tenon mesh (10 verts, 16 tris)
    ├── link{0..7}.stl         ← symlinks → Franka visual meshes
    └── visual_reads/          ← rendered verification images
        ├── scene_overhead_convexhull.png
        ├── scene_mortise_convexhull.png
        ├── scene_tenon_front_convexhull.png
        └── ...
```

### 0.5 Verification — PASSED

- Volume check: mortise(48 cm³) + tenon(80 cm³) = cuboid(128 cm³) = 4×4×8 cm³ ✓
- Convex hull: `mjVIS_CONVEXHULL` renders show V-notch preserved ✓
- Scene loads: both `franka_scene.xml` and `franka_scene_mjx.xml` ✓
- Keyframe "ready": Franka at home + blocks at diagonal positions ✓
- Side view: mortise and tenon both appear as plain rectangles ✓

---

## Link 1: Kinematics — `kinematic_rho_franka.py` + `contact_laplacian.py`

### 1.1 `kinematic_rho_franka.py`

**Input:** `(q, dq, ddq, u_cmd)` from MuJoCo at each timestep.

**Output:** `ρ(t)` — scalar contact order parameter.

**Formula (from grjl4_manipulation.md §8.5):**
```python
# Known dynamics (from MuJoCo)
tau_expected = M @ ddq + C @ dq + g    # computed by mj_inverse
tau_ext = u_cmd - tau_expected          # residual = contact
F_contact = J.T @ tau_ext              # project to Cartesian
rho = np.linalg.norm(F_contact) / (m_block * 9.81)
```

**Reuse:** Inherits `KinematicRhoFilter` (EMA smoothing, α=0.3) from `grjl3/kinematic_rho.py`.

### 1.2 `contact_laplacian.py`

**Input:** Contact forces from MuJoCo (`mj_contactForce`).

**Output:** `λ₁` — smallest nonzero eigenvalue of contact graph Laplacian.

**For parallel-jaw on cuboid:**
```
Contact graph: finger_L ── block ── finger_R
                                │
                              table (during placement)
```
- `λ₁ = min(w_L, w_R)` where `w_i = k_n · ρ_i` (normal force ratio)
- During transport: 2-node graph (just fingers), `λ₁ = min(w_L, w_R)`
- During placement: 3-node graph (+ table), `λ₁ = min(w_L, w_R, w_table)`

**Wind coupling (prop:m-wind):** An external wrench F_wind shifts λ₁:
```python
# Wind reduces λ₁ by the lateral force component
F_perp = F_wind - np.dot(F_wind, support_normal) * support_normal
lambda1_effective = lambda1 - np.linalg.norm(F_perp) / (m_block * 9.81)
# Three regimes:
#   lambda1_eff >= eps:  stable (no action)
#   0 < lambda1_eff < eps:  sliding (regrasp possible)
#   lambda1_eff <= 0:  toppled (replan required)
```

**Reuse:** Pattern from `grjl2/order_parameter.py` (spectral gap computation).

### 1.3 `wind.py`

**The wind module.** Stochastic external wrench applied to placed blocks.

```python
class Wind:
    """Stochastic wind field — the adversary (prop:m-wind)."""
    def __init__(self, F_max=0.0):
        self.F_max = F_max  # annealed during training

    def sample(self):
        """Sample a random gust: magnitude × direction."""
        A = np.random.uniform(0, self.F_max)
        n_hat = random_unit_vector_on_S2()
        return A * n_hat  # R^3 force vector

    def apply(self, data, placed_block_ids):
        """Apply wind to all placed blocks via xfrc_applied."""
        F = self.sample()
        for bid in placed_block_ids:
            data.xfrc_applied[bid, :3] = F   # force
            data.xfrc_applied[bid, 3:] = 0.0 # no torque (pure force)
```

One line per block per timestep. No XML changes needed.

### 1.4 Verification

- V4.1: `ρ_kinematic ≈ ρ_force_sensor` within O(Δt) — compare against MuJoCo contact force ground truth
- V4.3: `λ₁ ≥ ε` throughout Phase 3 — plot λ₁(t) for a scripted grasp
- V4.11: Wind at F_max = 0.3·m_k·g reduces λ₁ measurably; at F_max = m_k·g, block topples (λ₁ → 0)

---

## Link 2: FSM — `five_phase_fsm.py`

### 2.1 State machine

```
States: {APPROACH, CLOSE, CARRY, OPEN, RETREAT, REPLAN}
         Phase 1   Phase 2  Phase 3  Phase 4  Phase 5   Recovery
```

### 2.2 Transition conditions

| Transition | Condition | Guard |
|------------|-----------|-------|
| APPROACH → CLOSE | `ρ_filtered` crosses 1.0 upward | `ρ_prev < 1.0 and ρ_curr ≥ 1.0` |
| CLOSE → CARRY | `λ₁ ≥ ε` | Grasp stable, min dwell 50ms |
| CARRY → OPEN | End-effector at goal pose | `‖g_ee ⊖ g_target‖ < ε_goal` |
| OPEN → RETREAT | `ρ_filtered` crosses 1.0 downward | `ρ_prev ≥ 1.0 and ρ_curr < 1.0` |
| RETREAT → DONE | Robot at `q₀` | `‖q - q₀‖ < ε_q` |
| **any → REPLAN** | **placed block toppled (wind)** | `λ₁(placed_block) ≤ 0` or `‖g_k - g_k*‖ > ε_topple` |
| REPLAN → APPROACH | New plan computed | DAG recomputed, MPPI re-run |

### 2.3 Design decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| ρ crossing threshold | 1.0 (with EMA filter α=0.3) | Smooth out noise, detect true crossings |
| ε (spectral gap) | 0.05 | Normalised: w_i = F_contact_i / (m_block·g), so ε=0.05 means ≥5% of block weight per finger |
| Min dwell time | 50 ms (25 steps at 500 Hz) | Prevent chattering |
| ε_goal (placement) | 5 mm + 5° | From milestone spec |
| ε_q (home) | 0.01 rad per joint | Close enough to q₀ |

### 2.4 Verification

- V4.2: 5 phases detected for scripted pick-and-place
- V4.6: q(t₅) ≈ q₀, but g_block(t₅) ≠ g_block(t₀)

---

## Link 3: Observer — `block_detector.py` + `wrist_observer.py` (parallel with Link 1-2)

### 3.0 Design requirement

The observer must run at inference time (real-time control loop).
Latency budget: < 10 ms per frame (100 Hz observation within 500 Hz control).
Must detect 4 block types + estimate 6-DOF poses from RGB(+depth).

### 3.1 Architecture — two modes

**Mode A: Ground truth** (sim training, curriculum L=0..2)
```python
def observe_gt(model, data, block_ids):
    """Ground truth: read poses directly from MuJoCo."""
    return {bid: (data.xpos[bid], data.xquat[bid]) for bid in block_ids}
```

**Mode B: Vision** (sim2real, curriculum L=2+ and real)

Pretrained distilled vision encoder + lightweight detection head.

```
RGB image (640×480)
    │
    ▼
┌─────────────────────────┐
│ Frozen backbone          │  ← DINOv2-small (ViT-S/14, distilled)
│ (pretrained, no finetune)│     or MobileDINO / EfficientViT-SAM
│ patch_size=14, dim=384   │     ~21M params, ~5ms on GPU
└─────────────────────────┘
    │ feature map (H/14 × W/14 × 384)
    ▼
┌─────────────────────────┐
│ Detection head (trained) │  ← lightweight: 2-layer MLP or
│ per-patch: class + 6DOF  │     1×1 conv → {class_4, pos_3, quat_4}
│ ~0.3M params, ~1ms       │     trained on MuJoCo renders
└─────────────────────────┘
    │
    ▼
{block_type, position, orientation} × N_detected
```

**Why DINOv2-small:**
- Pretrained on diverse images → strong feature extractor for geometric shapes
- Distilled (student of DINOv2-giant) → small but high-quality features
- ViT-S/14: 21M params, ~5ms/frame on RTX 3090 — within latency budget
- Frozen backbone = no catastrophic forgetting, only train head on sim renders
- Alternative if too slow: EfficientViT or MobileDINO (trade quality for speed)

### 3.2 Block type classification

4 types have distinct visual signatures:
- Type 1 (cube): small red square from any angle
- Type 2 (cuboid): green rectangle (2:1 aspect from side)
- Type 3 (mortise): blue with V-notch visible from front
- Type 4 (tenon): orange with triangle protrusion at top

The detection head classifies patch clusters into {cube, cuboid, mortise, tenon, background}.
Diagonal placement (§0.2) ensures no mutual occlusion from the overhead camera.

### 3.3 Training data for detection head

```python
def generate_detection_dataset(scene_xml, n_samples=10000):
    """Render random block configurations with ground-truth labels."""
    m = mujoco.MjModel.from_xml_path(scene_xml)
    d = mujoco.MjData(m)
    for _ in range(n_samples):
        randomize_block_poses(d)        # random positions on table
        randomize_lighting(m)            # domain randomisation
        rgb = render(m, d, 'overhead')   # or 'side' camera
        labels = extract_gt_labels(m, d) # {type, bbox, pose} per block
        yield rgb, labels
```

Domain randomisation: lighting, camera jitter, texture variation, block colour noise.
All generated within MuJoCo — no real data needed for initial training.

### 3.4 FOV computation

```python
def blocks_in_fov(model, data, camera_name, block_ids):
    """Which blocks are visible from the camera?"""
    cam_pos, cam_rot = get_camera_pose(model, data, camera_name)
    fov_y = model.cam_fovy[cam_id]  # from XML
    for bid in block_ids:
        block_pos = data.xpos[bid]
        in_fov = is_in_frustum(block_pos, cam_pos, cam_rot, fov_y, aspect=4/3)
        occluded = is_occluded(block_pos, depth_buffer, cam_intrinsics)
```

### 3.5 Verification

- V4.9: blocks in FOV detected, blocks outside FOV classified invisible
- V4.10: pose error decreases with diverse viewpoints
- V4.13: detection head achieves >95% classification accuracy on held-out sim renders
- V4.14: end-to-end latency (backbone + head) < 10 ms on target GPU

---

## Link 4: Planner — `execution_dag.py` + `plan_generator.py`

### 4.1 `execution_dag.py`

**Input:** Goal configuration `{g_i*}`.

**Output:** Dependency DAG + valid topological orders.

```python
def build_dag(goal_config):
    """Block j rests on block k iff g_j*.z > g_k*.z and overlap(j,k)."""
    G = nx.DiGraph()
    for j, k in all_pairs:
        if supports(k, j, goal_config):  # k supports j
            G.add_edge(k, j)  # k must be placed before j
    return G

def valid_orders(G):
    """All topological sorts of the DAG."""
    return list(nx.all_topological_sorts(G))
```

### 4.2 `plan_generator.py`

**Input:** Number of blocks N, block dimensions, workspace bounds.

**Output:** Feasible plan P = [(block_idx, g_target, γ_grasp), ...].

**Feasibility checks (F1-F4):**
```
F1 (Topological): plan respects DAG order
F2 (Stability):   CoM(P_{1:i}) ∈ ConvHull(support) for every prefix
F3 (Reachability): IK(g_target) has solution within joint limits
F4 (Observable):   g_target ∈ D(q_approach) — visible from approach config
```

**Grasp type space Γ (for parallel jaw on cuboid):**
```
Γ = {TOP_DOWN, SIDE_X+, SIDE_X-, SIDE_Y+, SIDE_Y-}  # |Γ| = 5
```
5 orientations: 1 top-down + 4 side approaches (±x, ±y). No bottom grasp (table blocks).

### 4.3 MPPI over DAG

```python
def mppi_plan(goal_config, K=64, alpha=10.0):
    """Sample K plans, weight by cost, return weighted average."""
    dag = build_dag(goal_config)
    plans = [sample_plan(dag, goal_config) for _ in range(K)]
    costs = [evaluate_plan(p) for p in plans]
    weights = softmax(-np.array(costs) / alpha)
    return plans[np.argmax(weights)]  # best plan (discrete)
```

**Cost function J(P):**
```python
def evaluate_plan(plan):
    """Cost = total path length + stability margin + reachability margin."""
    J = 0
    for (block, g_target, gamma) in plan:
        J += path_length(q_0, ik_solve(g_target, gamma))  # joint-space distance
        J -= stability_margin(plan_prefix)                  # bonus for stable stacks
        J += reachability_penalty(g_target, gamma)          # penalty near singularity
    return J
```

### 4.4 Verification

- V4.7: DAG respected (no block placed before its support)
- PlanGen produces feasible plans for L=0,1,2

---

## Link 5: Controller — `velocity_field.py`

### 5.1 Network architecture

```python
class VelocityField(nn.Module):
    """v_θ: R^26 → R^7 (joint velocities)."""
    def __init__(self, K_fourier=8, hidden=256):
        # Input: q(7) + dq(7) + g_target(6) + t(1) + φ(5) = 26
        # Fourier embedding: t → [sin(ωₖt), cos(ωₖt)]_{k=1}^K  → 2K
        # Total input: 26 + 2K - 1 = 25 + 2K
        self.fourier_freqs = 2**torch.arange(K_fourier).float()  # log-spaced
        self.net = nn.Sequential(
            nn.Linear(25 + 2*K_fourier, hidden),
            nn.SiLU(),
            nn.Linear(hidden, hidden),
            nn.SiLU(),
            nn.Linear(hidden, 7),
        )
```

**Architecture decisions:**

| Hyperparameter | Value | Rationale |
|----------------|-------|-----------|
| Hidden width | 256 | Middle of 128-512 range from calculus.tex |
| Depth | 3 layers | Minimal; v_θ is a smooth field |
| K_fourier | 8 | 16 Fourier features, covers 1 Hz to 128 Hz |
| ω_k | 2^k, k=0..7 | Log-spaced (standard positional encoding) |
| Activation | SiLU | Smooth, works well with flow matching |
| Output | 7 (joint velocities) | dq_des ∈ R^7 |

### 5.2 Inverse dynamics

```python
def inverse_dynamics(model, data, q, dq, ddq_des):
    """τ = M(q)·ddq + C(q,dq)·dq + g(q)"""
    mujoco.mj_inverse(model, data)  # fills data.qfrc_inverse
    return data.qfrc_inverse[:7]    # 7 arm joints
```

**ddq_des from dq_des:** finite difference (grjl3 pattern).
```python
ddq_des = (dq_des - dq_des_prev) / dt  # + optional EMA filter
```

### 5.3 Verification

- V4.4: RANK=6, NULL=1 from Jacobian decomposition
- V4.5: [S,A] ≠ 0 for elbow reconfiguration

---

## Link 6: Training — `train.py`

### 6.1 Flow matching training loop

```python
for epoch in range(N_epochs):
    plan = plan_generator.sample()       # random feasible plan
    X_0 = sample_initial(mu_0)           # random block poses
    X_T = plan.goal_config               # target from plan

    t = torch.rand(1) * T               # random time
    X_t = (1 - t/T) * X_0 + (t/T) * X_T # OT interpolation (in R^6)
    u_t = (X_T - X_0) / T               # conditional velocity

    dq_pred = v_theta(state(q, dq, X_t, t, phase))
    loss = (dq_pred - u_t_joint).pow(2).mean()  # flow matching loss
    loss.backward()
    optimizer.step()
```

### 6.1b Wind during training rollouts

```python
# Wind is NOT in the flow matching loss (which is supervised).
# Wind acts during ROLLOUT EVALUATION (MMD computation + curriculum graduation).
wind = Wind(F_max=F_max_schedule(epoch))

def rollout_with_wind(v_theta, config, wind):
    """Execute full pipeline with stochastic wind perturbation."""
    env.reset(config)
    plan = mppi_plan(config.goal)
    for block in plan:
        fsm.reset()
        while not fsm.done:
            # Apply wind to all placed blocks
            wind.apply(env.data, env.placed_block_ids)
            # Normal control loop
            rho, lambda1 = kinematics(env)
            phase = fsm.update(rho, lambda1)
            if phase == REPLAN:
                # Wind toppled a block — replan from current state
                plan = mppi_plan(observe(env))
                break  # restart block loop with new plan
            dq = v_theta(state(env, block.goal, phase))
            tau = inverse_dynamics(env, dq)
            env.step(tau)
    return env.block_errors()
```

The wind broadens μ₀ to include partially toppled stacks.
v_θ sees these states during evaluation rollouts and must learn
to recover. No reward engineering — MMD already penalises deviation.

### 6.2 Task-space → joint-space bridge (resolves T1)

The flow matching target `u_t` is in task-space R^6.
The network output is in joint-space R^7.

**Bridge: Jacobian pseudoinverse + null-space projection.**
```python
# u_t is task-space velocity (R^6)
# Convert to joint-space target:
J = task_jacobian(q)                    # 6 × 7
J_pinv = np.linalg.pinv(J)             # 7 × 6
dq_target = J_pinv @ u_t               # minimum-norm IK velocity
# Optional: add null-space term
dq_target += (I - J_pinv @ J) @ dq_null  # elbow preference
```

Training loss becomes: `‖v_θ(z,t) - dq_target‖²` — both in R^7.

### 6.3 MMD evaluation (not training loss — resolves T4)

**Clarification:** Flow matching loss trains v_θ. MMD is the **evaluation metric** that drives curriculum progression.

```python
def mmd_eval(v_theta, test_configs, kernel_sigma=0.1):
    """MMD² between achieved and target distributions."""
    achieved = rollout(v_theta, test_configs)
    target = test_configs.goals
    # Gaussian kernel, σ = 0.1 (in SE(3) log-error units, ~5.7°/5.7cm)
    return mmd_squared(achieved, target, sigma=kernel_sigma)
```

| Decision | Value | Rationale |
|----------|-------|-----------|
| Kernel | Gaussian RBF | Simplest characteristic kernel |
| σ (bandwidth) | 0.1 (in SE(3) log-map units) | 0.1 rad ≈ 5.7°, 0.1 m = 10 cm; sensitive to goal-scale errors |
| Role | Evaluation metric for curriculum graduation | Not a training loss (flow matching is the training loss) |

### 6.4 Verification

- Loss converges for L=0 single-block task
- MMD → 0 on training distribution

---

## Link 7: Curriculum — `curriculum.py`

### 7.1 Six orthogonal axes

| Axis | Symbol | Range | Observable by | Tests |
|------|--------|-------|---------------|-------|
| Layers | L | 0, 1, 2, 3 | vision | Stability, DAG depth, error amplification |
| Count | N | 1, 2, 3, 4, 6 | vision | Mean field ū, MPPI scaling |
| Types | K_type | 1, 2, 3, 4 | vision | Observer, identifiability quotient |
| Wind | F_max | 0 → 0.5·m_k·g | haptics (λ₁) | Robustness, recovery from perturbation |
| Density | ρ_mat | uniform → 4× spread | haptics (τ_ext) | Active perception, smart placement |
| Size | σ_vol | 1.0 → [0.7, 1.3] | vision | Grip aperture, stability geometry |

**Two perception channels:**
- **Vision** (observable before contact): L, N, K_type, σ_vol — the robot can see these
- **Haptics** (observable only through interaction): ρ_mat, F_max — the robot must touch/lift to sense these

Size variation for box types (cube, cuboid) is runtime: `model.geom_size[gid] *= scale`.
Size variation for mesh types (mortise, tenon) uses pre-generated meshes at discrete scales
(0.7×, 1.0×, 1.3×) produced by `generate_meshes.py`.

### 7.2 Density variation — "How to do the task smartly"

The key insight: **visually identical blocks with different densities force
the robot to interact before it can plan.** Vision alone cannot distinguish
a 50g cube from a 200g cube — they look the same. The robot must touch,
lift, or swing the block to feel the inertia difference through its
proprioceptive channels (joint torques, ρ trajectory shape).

**Why this matters for stacking:**
- Stability requires heavy blocks on the bottom (lower CoM)
- The planner needs mass estimates to compute stability margins
- Mass is hidden state — only revealed through physical interaction

**The active perception loop:**
```
for each block on the table:
    1. APPROACH + TOUCH (Phase 1-2): ρ trajectory during contact
       reveals contact dynamics → infer mass from τ_ext = F_contact
    2. LIFT + SWING (Phase 3 probe): short exploratory lift
       → M(q)·ddq gives inertia → mass estimate m̂_k
    3. PUT BACK or CARRY: based on m̂_k, decide:
       - Is this the right block for the current stack position?
       - If not, put it back, try another

Smart ordering: heaviest-first placement = most stable stack.
```

**Implementation (runtime, no XML changes needed):**
```python
def randomize_density(model, block_geom_ids, density_range=(0.5, 2.0)):
    """Randomize block densities at episode start.

    Same visual appearance (color, mesh), different mass.
    The robot must infer mass through interaction.
    """
    base_densities = {
        'cube':    625,   # kg/m³ (base: 0.1 kg for 4cm cube)
        'cuboid':  625,   # kg/m³ (base: 0.2 kg for 4×4×8cm)
        'mortise': 625,   # kg/m³ (base: 0.088 kg)
        'tenon':   625,   # kg/m³ (base: 0.113 kg)
    }
    for gid in block_geom_ids:
        scale = np.random.uniform(*density_range)
        model.geom_mass[gid] *= scale
        # Visual appearance unchanged — same rgba, same mesh
    mujoco.mj_setConst(model, data)  # recompute inertias


def estimate_mass_from_lift(data, block_body_id, q, dq, ddq):
    """Infer block mass from joint torques during lift.

    During Phase 3 (CARRY), the block is grasped and moving.
    From inverse dynamics: τ = M(q)·ddq + C·dq + g
    The residual τ_ext = τ_cmd - τ_expected includes block weight.
    Block mass ≈ ||F_z_ext|| / g  (vertical component of external force).
    """
    tau_expected = mujoco.mj_inverse(model, data)  # robot-only dynamics
    tau_ext = data.ctrl[:7] - tau_expected[:7]      # residual
    J = get_jacobian(model, data, block_body_id)
    F_ext = np.linalg.pinv(J.T) @ tau_ext
    m_hat = abs(F_ext[2]) / 9.81   # vertical force / g
    return m_hat
```

**Signal pathway — how ρ reveals mass:**
```
Same shape, different density:
  Light block (50g):  ρ rises fast at contact, low τ_ext during lift
  Heavy block (200g): ρ rises slow at contact, high τ_ext during lift

  ρ(t) for light:    ___/‾‾‾‾‾‾‾‾    (fast transition)
  ρ(t) for heavy:    _____/‾‾‾‾‾‾    (slow transition, higher plateau)

  τ_ext during lift:
    light: ||F_ext|| ≈ 0.5 N
    heavy: ||F_ext|| ≈ 2.0 N

The ρ transition speed + τ_ext magnitude = mass fingerprint.
```

### 7.3 Exploration order (one axis at a time)

```
Phase 1: Fix L=0, K=1, F=0, ρ=uni, σ=1.  Grow N = 1,2,3,4.    (mean field)
Phase 2: Fix N≈L², K=1, F=0, ρ=uni, σ=1. Grow L = 1,2,3.      (stability)
Phase 3: Fix N=3, L=1, F=0, ρ=uni, σ=1.  Grow K = 1,2,3,4.    (types)
Phase 4: Fix N=3, L=2, K=1, ρ=uni, σ=1.  Grow F = 0→0.5·mg.   (wind)
Phase 5: Fix N=3, L=2, K=1, F=0, σ=1.    Grow ρ_mat spread.    (density / haptics)
Phase 6: Fix N=3, L=2, K=1, F=0, ρ=uni.  Grow σ = [0.7,1.3].  (size / vision)
Phase 7: Joint growth.  All 6 axes together.                     (integration)
```

**Perception decomposition:**
- Phases 1-3 grow task complexity (vision-only: what to stack, where, in what order)
- Phase 4 adds the adversary (wind: haptic feedback via λ₁)
- Phase 5 adds hidden state (density: haptic inference via τ_ext)
- Phase 6 adds visible variation (size: vision-based grip adaptation)
- Phase 7 combines everything

**Phase 5 detail (density variation — haptic channel):**
```
5a: N=2 same-type cubes, density ratio 1:2.  Robot must put heavy first.
5b: N=3 same-type cubes, density ratio 1:2:4. Heaviest-first ordering.
5c: N=3 mixed types, density randomized.      Type + mass inference.
5d: N=4, all types, density 0.5× to 2×.      Full active perception.
```

**Phase 6 detail (size variation — vision channel):**
```
6a: N=2 same-type cubes, one at 0.7×, one at 1.3×. Adjust grip aperture.
6b: N=3 mixed types at random scales.               Size-aware placement.
6c: N=4 mixed types, size + density randomised.      Both channels active.
```

For box types (cube, cuboid): `model.geom_size[gid] *= scale` at runtime.
For mesh types (mortise, tenon): select from pre-generated meshes at discrete
scales {0.7×, 1.0×, 1.3×}. Meshes produced by `generate_meshes.py` maintain
the complementarity constraint (mortise + tenon = cuboid) at every scale.

### 7.4 Progression

```python
levels = [
    Level(L=0, N=1, K=1, F_max=0.0, rho_spread=1.0, desc="single block pick-place"),
    Level(L=1, N=2, K=1, F_max=0.0, rho_spread=1.0, desc="2-block stack"),
    Level(L=2, N=3, K=1, F_max=0.0, rho_spread=1.0, desc="3-block pyramid"),
    Level(L=3, N=6, K=1, F_max=0.0, rho_spread=1.0, desc="6-block pyramid"),
]

# Wind annealing (after graduating L=2 without wind)
wind_levels = [
    Level(L=2, N=3, K=1, F_max=0.1*M*G, rho_spread=1.0, desc="light breeze"),
    Level(L=2, N=3, K=1, F_max=0.3*M*G, rho_spread=1.0, desc="moderate wind"),
    Level(L=2, N=3, K=1, F_max=0.5*M*G, rho_spread=1.0, desc="strong gust"),
]

# Density variation (after graduating wind)
density_levels = [
    Level(L=1, N=2, K=1, F_max=0.0, rho_spread=2.0, desc="2 cubes, 1:2 density"),
    Level(L=1, N=3, K=1, F_max=0.0, rho_spread=4.0, desc="3 cubes, 1:2:4 density"),
    Level(L=2, N=3, K=4, F_max=0.0, rho_spread=2.0, desc="mixed types + density"),
    Level(L=2, N=4, K=4, F_max=0.3*M*G, rho_spread=2.0, desc="full challenge"),
]

def graduate(level, v_theta, wind, n_test=100):
    """Graduate if ≥90% success with max_error < 5mm."""
    successes = 0
    for _ in range(n_test):
        config = plan_generator.sample(level)
        result = rollout_with_wind(v_theta, config, wind)
        if max(result.errors) < 0.005:  # 5mm
            successes += 1
    return successes / n_test >= 0.9
```

### 7.5 Wind graduation criterion

A level with F_max > 0 graduates when the robot achieves ≥90%
success **including recovery from wind-induced topples**. This
means the REPLAN transition fires, the DAG is recomputed, and
the toppled block is re-placed — all within the time budget.

### 7.6 Density graduation criterion

A level with ρ_spread > 1 graduates when the robot achieves ≥90%
success **with correct placement ordering** (heavy-first).
The planner must use mass estimates from the active perception
loop to determine stacking order. Wrong order = unstable stack
= failure under the 5mm error criterion.

### 7.7 Verification

- V4.8: N=1,2,3 stacking with max error < 5mm (no wind)
- V4.11: Wind at F_max = 0.3·m_k·g → λ₁ drop detected, recovery successful
- V4.12: Wind at F_max = 0.5·m_k·g → block topples, REPLAN fires, rebuild succeeds ≥90%
- V4.15: Robot identifies heavier block (from 2 same-type) via lift and places it first
- V4.16: With 4× density spread, stacking order matches heaviest-first ≥90% of time
- M1–M6 milestones from grjl4_manipulation.md

---

## Execution Order

```
Week 1:  [0] Scene XML + sanity render                              ← DONE
         [1] ρ + λ₁ with scripted (hard-coded) grasp trajectories
              + wind.py: verify λ₁ drop under applied wrench
         [3] Observer (ground-truth mode) — parallel with [1]

Week 2:  [2] FSM — detect 5 phases from [1] output
              + REPLAN state: trigger on λ₁(placed) ≤ 0
         [4] DAG + PlanGen — uses [3] output
              + replan capability: recompute DAG from current state

Week 3:  [5] v_θ network + inverse dynamics
         [6] Training loop (L=0 single block, no wind)

Week 4:  [7] Curriculum phases 1-4: L × N × K_type × F_max
         Integration + comparison (compare_v3_v4.py)

Week 5:  [3] Vision observer: DINOv2-small backbone + det head
         [7] Curriculum phase 5: density variation (active perception)
         [7] Curriculum phase 6: joint growth (all axes)
```

---

## File manifest

```
grjl4/
├── grjl4_impl_plan.md                ← this file
├── __init__.py
│
│   # [0] Scene XML — THE fixed point (at root for MuJoCo path resolution)
├── franka_scene.xml                   ← CPU MuJoCo (implicit integrator)
├── franka_scene_mjx.xml               ← MJX/JAX variant (implicitfast)
├── generate_meshes.py                 ← generates mortise_L/R + tenon STLs
│
├── scene/                             ← test fixtures (XML scenes for unit tests)
│   └── floating_gripper.xml           ← mocap gripper + 1 block (no arm)
│
├── assets/                            ← meshes + visual verification
│   ├── mortise_L.stl                  ← left convex half of mortise
│   ├── mortise_R.stl                  ← right convex half of mortise
│   ├── tenon.stl                      ← tenon mesh
│   ├── link{0..7}.stl, hand.stl       ← symlinks → Franka visual meshes
│   └── visual_reads/                  ← rendered images + videos
│
├── mujoco_menagerie/                  ← git submodule (Franka Panda MJCF)
│
├── kinematics/                        ← [1] Kinematics — DONE
│   ├── __init__.py
│   ├── kinematic_rho_franka.py        ← ρ from (q, dq, ddq, u)
│   ├── contact_laplacian.py           ← λ₁ from contact graph
│   └── wind.py                        ← stochastic wind (xfrc_applied)
│
├── fsm/                               ← [2] Finite State Machine
│   ├── __init__.py
│   └── five_phase_fsm.py             ← 5 phases + REPLAN state
│
├── observer/                          ← [3] Vision Observer — GT DONE
│   ├── __init__.py
│   ├── block_detector.py              ← pretrained backbone + det head (TODO)
│   └── wrist_observer.py             ← GT mode (done) + vision mode (TODO)
│
├── planner/                           ← [4] Planning
│   ├── __init__.py
│   ├── execution_dag.py               ← dependency DAG
│   └── plan_generator.py             ← MPPI plan sampling
│
├── controller/                        ← [5] Controller
│   ├── __init__.py
│   ├── velocity_field.py              ← v_θ MLP (flow matching)
│   └── task_jacobian.py              ← J(q), RANK/NULL, [S,A]
│
├── training/                          ← [6] Training
│   ├── __init__.py
│   └── train.py                       ← flow matching + MMD + wind rollouts
│
├── curriculum/                        ← [7] Curriculum
│   ├── __init__.py
│   └── curriculum.py                  ← 5 axes: L × N × K_type × F_max × ρ_mat
│
├── verification/                      ← all verification & rendering scripts
│   ├── verify_link1.py                ← static scene: ρ + λ₁ (Franka arm)
│   ├── verify_link1_pick_place.py     ← scripted pick-place (floating gripper)
│   └── render_pick_place.py           ← render MP4 video of pick-place
│
├── block_stacking.py                  ← main entry: ties [0]-[7] together
├── compare_v3_v4.py                   ← comparison with grjl3
└── outputs/                           ← plots, videos, logs
```

**Note:** XMLs stay at project root because MuJoCo resolves `meshdir`, `<include>`,
and `<mesh file="">` relative to the XML file's directory. Moving XMLs into a
subdirectory breaks the Franka include chain (panda.xml references its own
`assets/` directory). Python modules go into subdirectories by function.

---

## Resolved consistency-check items

| Item | Resolution in this plan |
|------|------------------------|
| T1: task→joint bridge | §6.2: J† pseudoinverse + null-space projection |
| T2: FSM transitions | §2.2: ρ crossing + EMA + dwell time + REPLAN on topple |
| T3: MPPI cost | §4.3: path_length + stability_margin + reachability_penalty |
| T4: MMD vs flow matching | §6.3: flow matching = training loss, MMD = evaluation metric |
| C3: MMD kernel+bandwidth | §6.3: Gaussian RBF, σ=0.1 in SE(3) log units |
| C4: FSM detection | §2.2: zero-crossing on filtered ρ, 50ms dwell |
| C5: Grasp space Γ | §4.2: |Γ|=5 (top-down + 4 sides) |
| C9: ε threshold | §2.3: ε=0.05 (normalised, 5% of block weight per finger) |
| C10: MLP hyperparams | §5.1: hidden=256, K=8, ω_k=2^k log-spaced |

## Verification criteria

| ID | Criterion | Link | Status |
|----|-----------|------|--------|
| V4.0a | Scene loads, keyframe works, blocks at diagonal positions | [0] | **PASS** |
| V4.0b | Volume: mortise + tenon = cuboid (128 cm³) | [0] | **PASS** |
| V4.0c | Convex hull preserves V-notch (mjVIS_CONVEXHULL check) | [0] | **PASS** |
| V4.1 | ρ_contact tracks grasp phases (floating gripper test) | [1] | **PASS** |
| V4.2 | 5 phases detected for scripted pick-and-place | [2] | |
| V4.3 | λ₁ ≥ ε during lift+hold (no wind) | [1] | **PASS** (λ₁=1.0, ε=0.05) |
| V4.4 | RANK=6, NULL=1 from Jacobian | [5] | |
| V4.5 | [S,A] ≠ 0 for elbow | [5] | |
| V4.6 | q(t₅) ≈ q₀, g_block changed | [2] | |
| V4.7 | DAG order respected | [4] | |
| V4.8 | N=1,2,3 stacking, max error < 5mm | [7] | |
| V4.9 | Blocks in FOV detected; outside FOV invisible | [3] | |
| V4.10 | Pose error decreases with diverse viewpoints | [3] | |
| V4.11 | Wind F_max → measurable λ₁_eff drop (0.2mg→0.88, 0.8mg→0.21) | [1] | **PASS** |
| V4.12 | Wind topple → REPLAN fires → rebuild succeeds ≥90% | [2]+[7] | |
| V4.13 | Detection head >95% classification on held-out sim renders | [3] | |
| V4.14 | End-to-end observer latency < 10 ms on target GPU | [3] | |
| V4.15 | Robot identifies heavier block via lift, places it first | [7] | |
| V4.16 | With 4× density spread, stacking order = heaviest-first ≥90% | [7] | |
| V4.17 | Scaled meshes: volume(mortise) + volume(tenon) = volume(cuboid) at each scale | [0] | **PASS** (0.7×, 1.0×, 1.3×) |
| V4.18 | Robot adjusts grip aperture for 0.7× and 1.3× blocks | [7] | |

---

## Immediate Next Step (2026-03-03)

**Link [2]: FSM — implement the 5-phase finite state machine with ρ/λ₁ guards**

The bi-level formulation is now formalised (§10.5 in grjl4_manipulation.md, sec:m-bilevel in the thesis). The floating-gripper scene validates the inner level (force closure). The next step is the **FSM that orchestrates the five-phase cycle using ρ and λ₁ as transition guards**.

Concretely:
1. Write `grjl4/fsm.py`: a `PhaseState` enum (APPROACH, GRASP, LIFT, TRANSPORT, PLACE) with transition rules:
   - APPROACH → GRASP: ρ crosses Σ (ρ ≥ 1)
   - GRASP → LIFT: λ₁ ≥ ε (force closure achieved)
   - LIFT → TRANSPORT: z ≥ z_lift
   - TRANSPORT → PLACE: ‖pos - goal_pos‖ < δ
   - PLACE → APPROACH: λ₁ < ε after opening (object released)
   - Any phase → REPLAN: λ₁ drops below ε unexpectedly (wind topple)
2. Unit test with the floating-gripper scene: run the scripted pick-place, verify all 5 transitions fire at the correct times
3. Also resolve the CLOSE value inconsistency: main loop uses 0.015, keyframes use 0.010 — pick one

This closes the link between the verified inner level (force closure from Link [1]) and the outer trajectory (Link [5]).
