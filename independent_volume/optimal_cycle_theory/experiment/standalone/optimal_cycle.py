"""Optimal Cycle Algorithm for Quadruped Locomotion.

Pure-math implementation derived entirely from the paper
(§articulated, §mppi, §riccati, §forward-only, §cycle)
parameterized by go2.xml (Unitree Go2).

Every equation has a section reference. No MuJoCo dependency.
Runs on the centroidal model ẋ = Ax + B(σ(t))u + c  [exactly linear].

Usage:
    python optimal_cycle.py [--n_iters 30] [--seed 0]
"""

import argparse
import json
import time

import numpy as np


# ═══════════════════════════════════════════════════════════════════════
# §0. Robot Parameters (from go2.xml)
# ═══════════════════════════════════════════════════════════════════════

TOTAL_MASS = 6.921 + 4 * (0.678 + 1.152 + 0.241)  # ≈ 15.205 kg
BODY_INERTIA = np.array([0.107027, 0.0980771, 0.0244531])  # Ixx, Iyy, Izz

# Forward kinematics at standing config (abd=0, hip=0.9, knee=-1.8)
# See plan §0 for derivation
L = 0.213  # thigh = calf length
_HIP_POS = np.array([
    [+0.1934, +0.0465, 0.0],
    [+0.1934, -0.0465, 0.0],
    [-0.1934, +0.0465, 0.0],
    [-0.1934, -0.0465, 0.0],
])
_LAT_OFF = np.array([
    [0.0, +0.0955, 0.0],
    [0.0, -0.0955, 0.0],
    [0.0, +0.0955, 0.0],
    [0.0, -0.0955, 0.0],
])

def _compute_foot_positions():
    """FK at standing: thigh + calf through hip=0.9, knee=-1.8."""
    th, kn = 0.9, -1.8
    r = np.zeros((4, 3))
    for k in range(4):
        p = _HIP_POS[k] + _LAT_OFF[k]
        p += np.array([-L * np.sin(th), 0.0, -L * np.cos(th)])
        p += np.array([-L * np.sin(th + kn), 0.0, -L * np.cos(th + kn)])
        r[k] = p
    return r

FOOT_POS = _compute_foot_positions()  # (4, 3) relative to base

STANDING_HEIGHT = 0.27  # m (from keyframe)
STRIDE_FREQ = 2.0       # Hz


# ═══════════════════════════════════════════════════════════════════════
# §12. Hyperparameters (tuning knobs — NOT part of the algorithm)
# ═══════════════════════════════════════════════════════════════════════

DT = 0.02           # s, 50 Hz
T_STRIDE = 0.5      # s
HORIZON = 25         # H = T_stride / dt
DUTY = 0.5           # β
H_MAX = 0.08         # m, max foot swing height
N_SAMPLES = 64       # MPPI samples
PHASE_NOISE = 0.1    # std dev for gait perturbation

# Cost weights [§4]
Q_DIAG = np.array([
    1.0, 1.0, 50.0,     # position (pz heavily weighted)
    2.0, 2.0, 2.0,      # velocity
    10.0, 10.0, 10.0,   # orientation (stay upright)
    1.0, 1.0, 1.0,      # angular velocity
    0.0,                 # phase
])
R_DIAG = np.full(12, 0.01)
QF_SCALE = 2.0

V_TARGET = np.array([0.5, 0.0, 0.0])  # m/s forward
Z_TARGET = 0.27

# Barrier / dual ascent [§8]
EPS_INIT = 1.0
ALPHA_UP = 1.1
ALPHA_DOWN = 0.95
GAMMA = 0.99


# ═══════════════════════════════════════════════════════════════════════
# §2. Centroidal Dynamics  [ẋ = Ax + B(σ(t))u + c,  exactly linear]
# ═══════════════════════════════════════════════════════════════════════

def skew(r):
    """3×3 skew-symmetric [r]× of vector r."""
    return np.array([
        [0,    -r[2],  r[1]],
        [r[2],  0,    -r[0]],
        [-r[1], r[0],  0   ],
    ])


def build_dynamics():
    """Return constant A (13×13), c (13,), and precomputed per-foot data.

    A encodes:  ṗ = v  (rows 0-2, cols 3-5)
                φ̇ = ω  (rows 6-8, cols 9-11)
    c encodes:  gravity c[5] = -9.81
                phase clock c[12] = stride_frequency
    """
    A = np.zeros((13, 13))
    A[0:3, 3:6] = np.eye(3)   # ṗ = v
    A[6:9, 9:12] = np.eye(3)  # φ̇ = ω

    c = np.zeros(13)
    c[5] = -9.81              # gravity in v̇_z
    c[12] = STRIDE_FREQ       # phase clock

    # Precompute per-foot rotation matrix: diag(1/I) [r_k]×
    inv_I = 1.0 / BODY_INERTIA
    rot_mats = [np.diag(inv_I) @ skew(FOOT_POS[k]) for k in range(4)]

    return A, c, rot_mats


def build_B(sigma, rot_mats):
    """Build B ∈ R^{13×12} for one timestep.  [§2 of plan]

    B[3:6, 3k:3(k+1)]  = (σ_k / M) · I₃         translational
    B[9:12, 3k:3(k+1)] = σ_k · diag(1/I) · [r_k]×  rotational
    """
    B = np.zeros((13, 12))
    for k in range(4):
        s = sigma[k]
        cols = slice(3 * k, 3 * (k + 1))
        B[3:6, cols] = (s / TOTAL_MASS) * np.eye(3)
        B[9:12, cols] = s * rot_mats[k]
    return B


# ═══════════════════════════════════════════════════════════════════════
# §3. Barrier-Smoothed Contacts (the exponential bridge)
# ═══════════════════════════════════════════════════════════════════════

def foot_height(t, phi_k, T_s=T_STRIDE, beta=DUTY, h_max=H_MAX):
    """Foot height h_k(t; φ_k).  [eq:foot-height in §articulated]

    h_k = h_max · (½ − ½ cos(2π · [η_k]₊ / (1−β)))
    η_k = (t/T_s + φ_k) mod 1 − β
    """
    eta = (t / T_s + phi_k) % 1.0 - beta
    if eta <= 0:
        return 0.0  # stance
    return h_max * (0.5 - 0.5 * np.cos(2 * np.pi * eta / (1 - beta)))


def barrier_scale(h_k, eps):
    """σ_k = ε / (h_k + ε).  [§3c, eq:impedance]

    σ_k → 1 when h_k → 0 (stance), σ_k → 0 when h_k large (swing).
    """
    return eps / (h_k + eps)


def compute_gait_schedule(phi, eps, H=HORIZON):
    """For a 3-vector φ = (φ_FL, φ_RL, φ_RR), FR at phase 0:

    Returns:
        h_seq: (H, 4) foot heights
        sigma_seq: (H, 4) barrier scales
    """
    # Phase offsets: FR=0, FL=phi[0], RL=phi[1], RR=phi[2]
    phases = np.array([phi[0], 0.0, phi[1], phi[2]])  # FL, FR, RL, RR

    h_seq = np.zeros((H, 4))
    sigma_seq = np.zeros((H, 4))
    for t_idx in range(H):
        t = t_idx * DT
        for k in range(4):
            h = foot_height(t, phases[k])
            h_seq[t_idx, k] = h
            sigma_seq[t_idx, k] = barrier_scale(h, eps)

    return h_seq, sigma_seq


# ═══════════════════════════════════════════════════════════════════════
# §4. Cost Function
# ═══════════════════════════════════════════════════════════════════════

def build_reference(H=HORIZON):
    """Reference trajectory x_ref(t) for t = 0..H.  [§4 of plan]"""
    x_ref = np.zeros((H + 1, 13))
    for t in range(H + 1):
        time = t * DT
        x_ref[t, 0] = V_TARGET[0] * time     # px
        x_ref[t, 1] = V_TARGET[1] * time     # py
        x_ref[t, 2] = Z_TARGET               # pz
        x_ref[t, 3:6] = V_TARGET             # velocity
        # orientation, angular velocity: zero
        x_ref[t, 12] = STRIDE_FREQ * time % 1.0  # phase
    return x_ref


# ═══════════════════════════════════════════════════════════════════════
# §5. Backward Riccati Recursion (TV-LQR)
# ═══════════════════════════════════════════════════════════════════════

def solve_riccati(A_d, B_d_seq, c_d, Q, R, Q_f, x_ref, H):
    """Backward Riccati → K_seq (H, 12, 13), k_seq (H, 12).

    [eq:riccati-tvlqr in §articulated]

    S_t = R + B_d^T P_{t+1} B_d
    K_t = S_t⁻¹ B_d^T P_{t+1} A_d
    P_t = Q + A_d^T P_{t+1} (A_d − B_d K_t)
    """
    nx, nu = 13, 12
    P_MAX = 1e4

    K_seq = np.zeros((H, nu, nx))
    k_seq = np.zeros((H, nu))

    # Terminal conditions [§5b]
    P = Q_f.copy()
    p = -Q_f @ x_ref[H]

    # Minimum R for conditioning
    R_safe = np.maximum(np.diag(R), 1e-2)
    R_mat = np.diag(R_safe)

    for t in range(H - 1, -1, -1):
        # NaN recovery
        if not np.all(np.isfinite(P)):
            P = Q_f.copy()
            p = -Q_f @ x_ref[H]

        # Clip P before matmul [numerical stability]
        np.clip(P, -P_MAX, P_MAX, out=P)
        np.clip(p, -P_MAX, P_MAX, out=p)

        B_d = B_d_seq[t]

        # S = R + B_d^T P B_d  [12×12]
        S = R_mat + B_d.T @ P @ B_d
        S = 0.5 * (S + S.T) + 1e-6 * np.eye(nu)  # symmetrize + regularize

        # Robust inversion
        try:
            S_inv = np.linalg.solve(S, np.eye(nu))
        except np.linalg.LinAlgError:
            S_inv = np.diag(1.0 / R_safe)

        # Feedback gain K_t [§5c]
        K_t = S_inv @ B_d.T @ P @ A_d
        np.clip(K_t, -1e3, 1e3, out=K_t)
        K_seq[t] = K_t

        # Feedforward η_t [§5c]
        Pc_p = P @ c_d + p
        eta_t = S_inv @ B_d.T @ Pc_p

        # Output feedforward: u = k_out − K(x − x_ref) [§5d]
        k_seq[t] = -(K_t @ x_ref[t] + eta_t)
        np.clip(k_seq[t], -1e3, 1e3, out=k_seq[t])

        # Closed-loop dynamics
        F_t = A_d - B_d @ K_t

        # Riccati update P_t [§5c]
        P_new = Q + A_d.T @ P @ A_d - K_t.T @ S @ K_t
        P = 0.5 * (P_new + P_new.T)

        # Affine update p_t [§5c]
        p = F_t.T @ Pc_p - Q @ x_ref[t]

    return K_seq, k_seq


# ═══════════════════════════════════════════════════════════════════════
# §6. Forward Simulation (centroidal model, exactly linear)
# ═══════════════════════════════════════════════════════════════════════

def forward_simulate(x0, A_d, B_d_seq, c_d, K_seq, k_seq, x_ref,
                     h_seq, eps, H):
    """Forward sweep with optimal Riccati gains.  [§6 of plan]

    u_t = k_t − K_t (x_t − x_ref(t))
    x_{t+1} = A_d x_t + B_d(t) u_t + c_d
    J accumulates tracking + control + barrier costs.

    Returns:
        x_traj: (H+1, 13) state trajectory
        u_traj: (H, 12) control trajectory
        J: scalar total cost
        J_track: scalar tracking cost
        J_barrier: scalar barrier cost
    """
    Q = np.diag(Q_DIAG)
    R = np.diag(R_DIAG)

    x_traj = np.zeros((H + 1, 13))
    u_traj = np.zeros((H, 12))
    x_traj[0] = x0.copy()

    J_track = 0.0
    J_barrier = 0.0

    for t in range(H):
        x = x_traj[t]
        dx = x - x_ref[t]

        # Optimal control [§6b]
        u = k_seq[t] - K_seq[t] @ dx
        u_traj[t] = u

        # Exactly linear dynamics step
        x_traj[t + 1] = A_d @ x + B_d_seq[t] @ u + c_d

        # Cost accumulation [§6b]
        J_track += DT * (dx @ Q @ dx + u @ R @ u)

        # Barrier penalty: −ε Σ_k log(h_k + ε)  [§4, Remark 1]
        for k in range(4):
            h = h_seq[t, k]
            J_barrier -= DT * eps * np.log(h + eps)

    # Terminal cost [§6c]
    dx_T = x_traj[H] - x_ref[H]
    Q_f = np.diag(QF_SCALE * Q_DIAG)
    J_track += dx_T @ Q_f @ dx_T

    return x_traj, u_traj, J_track + J_barrier, J_track, J_barrier


# ═══════════════════════════════════════════════════════════════════════
# §7. MPPI Outer Loop (Boltzmann reweighting)
# ═══════════════════════════════════════════════════════════════════════

def mppi_step(phi_current, eps, x0, x_ref, A_d, c_d, rot_mats, rng):
    """One MPPI iteration: sample N gaits, evaluate, reweight.  [§7]

    Returns:
        phi_new: (3,) updated gait phase
        costs: (N,) cost per sample
        weights: (N,) Boltzmann weights
        best_traj: (H+1, 13) best trajectory
        J_tracks: (N,) tracking costs
        J_barriers: (N,) barrier costs
    """
    H = HORIZON
    N = N_SAMPLES
    Q = np.diag(Q_DIAG)
    R = np.diag(R_DIAG)
    Q_f = np.diag(QF_SCALE * Q_DIAG)

    costs = np.zeros(N)
    J_tracks = np.zeros(N)
    J_barriers = np.zeros(N)
    best_cost = np.inf
    best_traj = None
    all_phis = np.zeros((N, 3))

    for i in range(N):
        # Step 7a: sample gait phase
        phi_i = phi_current + rng.normal(0, PHASE_NOISE, size=3)
        phi_i = phi_i % 1.0  # wrap to [0, 1)
        all_phis[i] = phi_i

        # Step 3: compute gait schedule
        h_seq, sigma_seq = compute_gait_schedule(phi_i, eps, H)

        # Step 2: build time-varying B_d
        B_d_seq = np.zeros((H, 13, 12))
        for t in range(H):
            B_d_seq[t] = DT * build_B(sigma_seq[t], rot_mats)

        # Step 5: backward Riccati
        K_seq, k_seq = solve_riccati(A_d, B_d_seq, c_d, Q, R, Q_f, x_ref, H)

        # Reject NaN Riccati
        if not (np.all(np.isfinite(K_seq)) and np.all(np.isfinite(k_seq))):
            costs[i] = 1e8
            J_tracks[i] = 1e8
            continue

        # Step 6: forward simulate
        x_traj, u_traj, J, J_t, J_b = forward_simulate(
            x0, A_d, B_d_seq, c_d, K_seq, k_seq, x_ref, h_seq, eps, H
        )

        costs[i] = J
        J_tracks[i] = J_t
        J_barriers[i] = J_b

        if J < best_cost:
            best_cost = J
            best_traj = x_traj.copy()

    # Step 7c: Boltzmann reweighting
    log_w = -(costs - costs.min()) / max(eps, 1e-8)
    log_w -= log_w.max()  # numerical stability
    w = np.exp(log_w)
    w /= w.sum()

    # Step 7d: weighted mean on torus
    # Circular mean: atan2(Σ w sin(2π φ), Σ w cos(2π φ)) / (2π)
    phi_new = np.zeros(3)
    for d in range(3):
        angles = 2 * np.pi * all_phis[:, d]
        s = np.sum(w * np.sin(angles))
        c = np.sum(w * np.cos(angles))
        phi_new[d] = (np.arctan2(s, c) / (2 * np.pi)) % 1.0

    return phi_new, costs, w, best_traj, J_tracks, J_barriers


# ═══════════════════════════════════════════════════════════════════════
# §8. Dual Ascent on ε (the re-cycle)
# ═══════════════════════════════════════════════════════════════════════

def dual_ascent(eps, weights, H_target):
    """Update ε based on entropy of weight distribution.  [§8]

    S = −Σ w log w  (entropy)
    If S < H_target: ε ← ε · α_up  (more exploration)
    Else:            ε ← ε · α_down (sharpen contacts)
    H_target ← γ · H_target
    """
    # Entropy
    w_safe = np.clip(weights, 1e-30, None)
    S = -np.sum(weights * np.log(w_safe))

    if S < H_target:
        eps_new = eps * ALPHA_UP
    else:
        eps_new = eps * ALPHA_DOWN

    eps_new = np.clip(eps_new, 1e-4, 100.0)
    H_target_new = H_target * GAMMA

    return eps_new, H_target_new, S


# ═══════════════════════════════════════════════════════════════════════
# §10. The Complete Algorithm
# ═══════════════════════════════════════════════════════════════════════

def run_optimal_cycle(n_iters=30, seed=0, verbose=True):
    """Full optimal cycle algorithm for quadruped locomotion.

    Three-level hierarchy:
      Level 1: MPPI samples gait schedules, Boltzmann reweights
      Level 2: TV-LQR via backward Riccati (exact for linear centroidal)
      Level 3: (Kalman estimation — omitted in this centroidal-only version)

    The re-cycle (dual ascent on ε) controls convergence.

    Returns:
        dict with trajectories, diagnostics, converged parameters
    """
    rng = np.random.default_rng(seed)

    # Precompute constant dynamics [§2]
    A, c_vec, rot_mats = build_dynamics()
    A_d = np.eye(13) + DT * A      # Euler discretization
    c_d = DT * c_vec

    # Reference trajectory [§4]
    x_ref = build_reference(HORIZON)

    # Initial state: standing
    x0 = np.zeros(13)
    x0[2] = STANDING_HEIGHT

    # Initialize [plan §10]
    phi = np.array([0.5, 0.5, 0.0])  # trot gait
    eps = EPS_INIT
    H_target = np.log(N_SAMPLES) * 0.8

    # Diagnostics storage
    diag = {
        'cost_mean': [], 'cost_std': [], 'cost_best': [],
        'J_track_best': [], 'J_barrier_best': [],
        'J_track_mean': [], 'J_barrier_mean': [],
        'entropy': [], 'epsilon': [], 'ess': [],
        'phi': [], 'H_target': [],
        'final_vx': [], 'final_z': [],
    }

    if verbose:
        print(f"Optimal Cycle Algorithm: {n_iters} iterations, "
              f"N={N_SAMPLES} samples")
        print(f"Target: v_x={V_TARGET[0]} m/s, z={Z_TARGET} m")
        print(f"Robot: M={TOTAL_MASS:.1f} kg, "
              f"I={BODY_INERTIA.round(3)}")
        print(f"Foot positions (standing):")
        for k, name in enumerate(['FL', 'FR', 'RL', 'RR']):
            print(f"  {name}: {FOOT_POS[k].round(4)}")
        print()

    best_overall_traj = None
    best_overall_cost = np.inf

    for it in range(n_iters):
        t0 = time.time()

        # One MPPI step [§7]
        phi_new, costs, weights, best_traj, J_ts, J_bs = mppi_step(
            phi, eps, x0, x_ref, A_d, c_d, rot_mats, rng
        )

        best_idx = np.argmin(costs)

        # Dual ascent [§8]
        eps_new, H_target, S = dual_ascent(eps, weights, H_target)

        # ESS = 1 / Σ w²
        ess = 1.0 / np.sum(weights**2)

        # Record
        diag['cost_mean'].append(float(costs.mean()))
        diag['cost_std'].append(float(costs.std()))
        diag['cost_best'].append(float(costs[best_idx]))
        diag['J_track_best'].append(float(J_ts[best_idx]))
        diag['J_barrier_best'].append(float(J_bs[best_idx]))
        diag['J_track_mean'].append(float(J_ts.mean()))
        diag['J_barrier_mean'].append(float(J_bs.mean()))
        diag['entropy'].append(S)
        diag['epsilon'].append(eps)
        diag['ess'].append(ess)
        diag['phi'].append(phi_new.tolist())
        diag['H_target'].append(H_target)

        # Best trajectory final state
        if best_traj is not None:
            diag['final_vx'].append(float(best_traj[-1, 3]))
            diag['final_z'].append(float(best_traj[-1, 2]))
            if costs[best_idx] < best_overall_cost:
                best_overall_cost = costs[best_idx]
                best_overall_traj = best_traj.copy()
        else:
            diag['final_vx'].append(0.0)
            diag['final_z'].append(STANDING_HEIGHT)

        # Update
        phi = phi_new
        eps = eps_new

        elapsed = time.time() - t0
        if verbose and (it % 5 == 0 or it == n_iters - 1):
            print(
                f"iter {it:3d} ({elapsed:.2f}s): "
                f"J={diag['cost_mean'][-1]:.1f}±{diag['cost_std'][-1]:.1f}  "
                f"best={diag['cost_best'][-1]:.1f}  "
                f"J_t={diag['J_track_best'][-1]:.1f}  "
                f"J_b={diag['J_barrier_best'][-1]:.1f}  "
                f"S={S:.2f}  ε={eps:.4f}  ESS={ess:.1f}  "
                f"φ={phi.round(3)}  "
                f"v_x={diag['final_vx'][-1]:.3f}  "
                f"z={diag['final_z'][-1]:.3f}"
            )

    if verbose:
        print(f"\nConverged: φ*={phi.round(4)}, ε*={eps:.6f}")
        if best_overall_traj is not None:
            print(f"Best trajectory: v_x={best_overall_traj[-1,3]:.4f} m/s, "
                  f"z={best_overall_traj[-1,2]:.4f} m")

    return {
        'phi': phi.tolist(),
        'epsilon': eps,
        'diagnostics': diag,
        'best_trajectory': best_overall_traj,
        'x_ref': x_ref,
    }


# ═══════════════════════════════════════════════════════════════════════
# §13. Verification
# ═══════════════════════════════════════════════════════════════════════

def verify_dynamics():
    """Unit test: standing config with zero forces → gravity descent only."""
    A, c_vec, rot_mats = build_dynamics()
    A_d = np.eye(13) + DT * A
    c_d = DT * c_vec

    x = np.zeros(13)
    x[2] = STANDING_HEIGHT

    # No forces, all stance
    sigma = np.ones(4)
    B = build_B(sigma, rot_mats)
    B_d = DT * B
    u = np.zeros(12)

    # One step
    x1 = A_d @ x + B_d @ u + c_d

    assert abs(x1[0]) < 1e-10, f"px should be 0, got {x1[0]}"
    assert abs(x1[1]) < 1e-10, f"py should be 0, got {x1[1]}"
    assert abs(x1[2] - STANDING_HEIGHT) < 1e-10, f"pz unchanged (v=0)"
    assert abs(x1[5] - (-9.81 * DT)) < 1e-10, f"v_z = g*dt, got {x1[5]}"
    assert abs(x1[12] - STRIDE_FREQ * DT) < 1e-10, f"phase clock"
    print("dynamics: PASS")


def verify_barrier():
    """Unit test: σ_k ∈ [0,1], limits correct."""
    assert abs(barrier_scale(0.0, 1.0) - 1.0) < 1e-10
    assert abs(barrier_scale(1e6, 1.0)) < 1e-4
    assert abs(barrier_scale(1.0, 1.0) - 0.5) < 1e-10
    print("barrier:  PASS")


def verify_riccati():
    """Unit test: constant σ (all stance) → P converges."""
    A, c_vec, rot_mats = build_dynamics()
    A_d = np.eye(13) + DT * A
    c_d = DT * c_vec

    Q = np.diag(Q_DIAG)
    R = np.diag(R_DIAG)
    Q_f = np.diag(QF_SCALE * Q_DIAG)
    x_ref = build_reference(HORIZON)

    sigma = np.ones(4)  # all stance
    B = build_B(sigma, rot_mats)
    B_d = DT * B
    B_d_seq = np.tile(B_d, (HORIZON, 1, 1))

    K_seq, k_seq = solve_riccati(A_d, B_d_seq, c_d, Q, R, Q_f, x_ref, HORIZON)

    assert np.all(np.isfinite(K_seq)), "K has NaN/inf"
    assert np.all(np.isfinite(k_seq)), "k has NaN/inf"
    assert K_seq.shape == (HORIZON, 12, 13)
    assert k_seq.shape == (HORIZON, 12)
    print("riccati:  PASS")


def verify_forward():
    """Integration test: single gait → forward motion."""
    A, c_vec, rot_mats = build_dynamics()
    A_d = np.eye(13) + DT * A
    c_d = DT * c_vec
    x_ref = build_reference(HORIZON)
    Q = np.diag(Q_DIAG)
    R = np.diag(R_DIAG)
    Q_f = np.diag(QF_SCALE * Q_DIAG)

    x0 = np.zeros(13)
    x0[2] = STANDING_HEIGHT

    phi = np.array([0.5, 0.5, 0.0])  # trot
    eps = 1.0

    h_seq, sigma_seq = compute_gait_schedule(phi, eps, HORIZON)

    B_d_seq = np.zeros((HORIZON, 13, 12))
    for t in range(HORIZON):
        B_d_seq[t] = DT * build_B(sigma_seq[t], rot_mats)

    K_seq, k_seq = solve_riccati(A_d, B_d_seq, c_d, Q, R, Q_f, x_ref, HORIZON)
    x_traj, u_traj, J, J_t, J_b = forward_simulate(
        x0, A_d, B_d_seq, c_d, K_seq, k_seq, x_ref, h_seq, eps, HORIZON
    )

    print(f"forward:  J={J:.1f} (track={J_t:.1f}, barrier={J_b:.1f})")
    print(f"          final v_x={x_traj[-1,3]:.4f}, z={x_traj[-1,2]:.4f}")
    print(f"          PASS")


def run_verification():
    """Run all unit and integration tests."""
    print("Running verification suite...\n")
    verify_dynamics()
    verify_barrier()
    verify_riccati()
    verify_forward()
    print("\nAll tests passed.")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Optimal Cycle Algorithm for Quadruped Locomotion"
    )
    parser.add_argument('--n_iters', type=int, default=30)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--verify', action='store_true',
                        help='Run verification suite only')
    parser.add_argument('--output', type=str, default='optimal_cycle_result.json')
    args = parser.parse_args()

    if args.verify:
        run_verification()
    else:
        result = run_optimal_cycle(n_iters=args.n_iters, seed=args.seed)

        # Save diagnostics
        save_data = {
            'phi': result['phi'],
            'epsilon': result['epsilon'],
            'diagnostics': result['diagnostics'],
        }
        with open(args.output, 'w') as f:
            json.dump(save_data, f, indent=2)
        print(f"\nSaved to {args.output}")
