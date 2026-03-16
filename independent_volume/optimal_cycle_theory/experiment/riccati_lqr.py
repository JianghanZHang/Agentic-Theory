"""Centroidal TV-LQR via backward Riccati recursion.

The centroidal quadruped dynamics is *exactly* linear (not linearized):
    ẋ = A(σ(t)) x + B(σ(t)) u + c

where σ_k(t) is the barrier-smoothed contact scale from the gait schedule.
A(t) is time-varying: the double-integrator structure plus viscous ground
friction F = -Σ_k σ_k(t) · η · v makes A[3:6, 3:6] depend on σ(t).
B(t) is time-varying through σ_k(t) as before.

The backward Riccati gives optimal time-varying feedback K(t) and
feedforward k(t) for tracking a reference trajectory x_ref(t).

Usage in the MPPI loop:
    1. MPPI samples gait schedules h_k (B-spline coefficients)
    2. h_k → σ_k(t) via barrier_force_scale
    3. build_AB(σ_k) → A_seq, B_seq, c
    4. solve_tvlqr(A_seq, B_seq, ...) → K_seq, k_seq
    5. Forward simulate: u_t = k_t - K_t @ (x_t - x_ref_t)
"""

import numpy as np
from scipy.linalg import solve_discrete_are, expm

from config import ROBOT, OCP, CONSTRAINTS
from xla_inf import smooth_where, safe_log, devil_check


def solve_dare_nominal(A_seq, B_seq, Q, R, dt):
    """Steady-state DARE from time-averaged dynamics (coverage terminal cost).

    P_∞ = Q + Ā_d^T P_∞ Ā_d - Ā_d^T P_∞ B̄_d (R + B̄_d^T P_∞ B̄_d)^{-1} B̄_d^T P_∞ Ā_d

    where Ā = H⁻¹ Σ_t A(t), B̄ = H⁻¹ Σ_t B(t), discretized via Euler.

    Returns P_∞ or None if DARE fails (non-stabilizable pair).
    """
    nx = A_seq.shape[1]
    A_d_nom = np.eye(nx) + dt * np.mean(A_seq, axis=0)
    B_d_nom = dt * np.mean(B_seq, axis=0)
    # Phase clock (dim 12) is uncontrollable (B[:,12]=0, eigenvalue=1).
    # Shrink its eigenvalue inside the unit circle so DARE can stabilize.
    A_d_nom[12, 12] *= 0.99
    R_safe = np.maximum(R, 1e-6 * np.eye(R.shape[0]))
    try:
        P_inf = solve_discrete_are(A_d_nom, B_d_nom, Q, R_safe)
        P_inf = 0.5 * (P_inf + P_inf.T)
        if np.any(np.linalg.eigvalsh(P_inf) < -1e-6) or not np.all(np.isfinite(P_inf)):
            return None
        np.clip(P_inf, -1e4, 1e4, out=P_inf)
        return P_inf
    except (np.linalg.LinAlgError, ValueError):
        return None


def skew(r):
    """3×3 skew-symmetric (cross-product) matrix of vector r."""
    return np.array([
        [0, -r[2], r[1]],
        [r[2], 0, -r[0]],
        [-r[1], r[0], 0],
    ])


def matrix_exp_discretize(A_ct, dt):
    """Compute exact discretization via matrix exponential.

    Returns A_d = expm(A·dt).  B_d is computed as dt·B (first-order) since
    A has eigenvalues O(η/m) ≈ 0.3 and dt = 0.01, giving error O(A·dt²) ≈ 3e-5.

    For the affine term, uses the augmented matrix trick:
        expm([[A·dt, c·dt], [0, 0]]) = [[expm(A·dt), V·c], [0, 1]]
    where V = A⁻¹(expm(A·dt) - I), avoiding explicit inversion.
    """
    return expm(A_ct * dt)


def matrix_exp_step(A_ct, B_ct, c, x, u, dt):
    """Exact one-step integration via augmented matrix exponential.

    x(t+dt) = expm(A·dt)·x + V·(B·u + c)
    where V = A⁻¹(expm(A·dt) - I).

    Uses the augmented (nx+1)×(nx+1) matrix for numerical stability:
        expm([[A·dt, (Bu+c)·dt], [0, 0]]) = [[expm(A·dt), V·(Bu+c)], [0, 1]]
    """
    nx = A_ct.shape[0]
    rhs = B_ct @ u + c
    M = np.zeros((nx + 1, nx + 1))
    M[:nx, :nx] = A_ct * dt
    M[:nx, nx] = rhs * dt
    eM = expm(M)
    x_new = eM[:nx, :nx] @ x + eM[:nx, nx]
    return x_new


def build_AB(mass, inertia, foot_pos, sigma_seq, eta=None, contact_normals=None):
    """Build A_seq (H, 13, 13) and B_seq (H, 13, 12) from barrier scales.

    A(t) = A_kin - (η/m) Σ_k σ_k(t) · Π_k,  where Π_k = I₃ - n̂_k n̂_k^T
    is the per-foot contact tangent-plane projector.

    Args:
        mass: scalar robot mass
        inertia: (3,) diagonal moments of inertia [Ixx, Iyy, Izz]
        foot_pos: (4, 3) foot positions in body frame
        sigma_seq: (H, 4) barrier scales per timestep
        eta: viscous ground coefficient [N·s/m]. Defaults to ROBOT["eta"].
        contact_normals: (4, 3) unit surface normals per foot.
                         Default None → flat ground (ê_z).

    Returns:
        A_seq: (H, 13, 13) time-varying state matrices
        B_seq: (H, 13, 12) time-varying input matrices
        c: (13,) constant affine term (gravity + phase clock)
    """
    if eta is None:
        eta = ROBOT.get("eta", 0.0)
    H = sigma_seq.shape[0]

    # A_base: constant kinematic part (double integrator)
    A_base = np.zeros((13, 13))
    A_base[0:3, 3:6] = np.eye(3)   # ṗ = v
    A_base[6:9, 9:12] = np.eye(3)  # φ̇ = ω

    # Default: flat ground normals (vertical)
    if contact_normals is None:
        contact_normals = np.tile(np.array([0.0, 0.0, 1.0]), (4, 1))

    # Precompute per-foot projectors: Π_k = I₃ - n̂_k n̂_k^T
    projectors = np.zeros((4, 3, 3))
    for k in range(4):
        n = contact_normals[k].copy()
        norm = np.linalg.norm(n)
        if norm < 1e-8:
            n = np.array([0.0, 0.0, 1.0])
        else:
            n = n / norm
        projectors[k] = np.eye(3) - np.outer(n, n)

    # A_seq: time-varying through per-foot contact projectors
    # Π_k projects velocity onto the tangent plane at foot k.
    # Flat ground (n̂_k = ê_z): Π_k = diag(1,1,0) → horizontal friction only.
    A_seq = np.tile(A_base, (H, 1, 1))  # (H, 13, 13)
    for t in range(H):
        weighted_proj = np.zeros((3, 3))
        for k in range(4):
            weighted_proj += sigma_seq[t, k] * projectors[k]
        A_seq[t, 3:6, 3:6] = -(eta / mass) * weighted_proj

    # c: gravity + stride clock
    c = np.zeros(13)
    c[5] = -9.81  # gravity in z
    c[12] = ROBOT["stride_frequency"]  # phase clock

    # Precompute per-foot rotation contribution: diag(1/I) @ [r_k]×
    inv_I = 1.0 / inertia  # (3,)
    rot_mats = []  # (4,) list of (3,3) matrices
    for k in range(4):
        # [r_k]× maps f → r_k × f; then divide by I per-axis
        rot_mats.append(np.diag(inv_I) @ skew(foot_pos[k]))

    # B_seq: time-varying through σ_k
    B_seq = np.zeros((H, 13, 12))
    for t in range(H):
        for k in range(4):
            s = sigma_seq[t, k]
            cols = slice(3 * k, 3 * (k + 1))
            # Translational: dv += σ_k f_k / m
            B_seq[t, 3:6, cols] = s / mass * np.eye(3)
            # Rotational: dω += σ_k diag(1/I) [r_k]× f_k
            B_seq[t, 9:12, cols] = s * rot_mats[k]

    return A_seq, B_seq, c


def build_reference_trajectory(horizon, dt):
    """Build reference trajectory for tracking.

    Reference: linear velocity ramp over [0, T_ramp], then constant.
    Position is the exact integral of the velocity profile, so (x_ref, v_ref)
    is dynamically consistent — the LQR tracks a physically achievable path.

    Args:
        horizon: number of timesteps H
        dt: timestep

    Returns:
        x_ref: (H+1, 13) reference trajectory
    """
    v_target = np.array(OCP["target_velocity"])
    z_target = CONSTRAINTS["z_target"]
    T_ramp = float(OCP.get("T_ramp", 0.5))  # ramp-up period [s]

    x_ref = np.zeros((horizon + 1, 13))
    for t in range(horizon + 1):
        time = t * dt
        # Velocity: linear ramp then constant
        alpha = min(time / max(T_ramp, 1e-30), 1.0)
        v_ref = alpha * v_target
        x_ref[t, 3:6] = v_ref
        # Position: integral of ramp profile
        #   t < T_ramp: p = v_target * t² / (2 T_ramp)
        #   t ≥ T_ramp: p = v_target * T_ramp / 2 + v_target * (t - T_ramp)
        #             = v_target * (t - T_ramp / 2)
        if time < T_ramp:
            x_ref[t, 0] = v_target[0] * time**2 / (2.0 * T_ramp)
            x_ref[t, 1] = v_target[1] * time**2 / (2.0 * T_ramp)
        else:
            x_ref[t, 0] = v_target[0] * (time - T_ramp / 2.0)
            x_ref[t, 1] = v_target[1] * (time - T_ramp / 2.0)
        x_ref[t, 2] = z_target  # pz (constant height)
        # Orientation: upright
        x_ref[t, 6:9] = 0.0
        # Angular velocity: zero
        x_ref[t, 9:12] = 0.0
        # Phase clock
        x_ref[t, 12] = ROBOT["stride_frequency"] * time % 1.0

    return x_ref


def solve_tvlqr(A_seq, B_seq, c, Q_diag, R_diag, Q_f_diag, x_ref, dt, horizon):
    """Discrete-time TV-LQR via backward Riccati recursion.

    Solves the tracking problem:
        min Σ (x_t - x_ref_t)^T Q (x_t - x_ref_t) + u_t^T R u_t
            + (x_H - x_ref_H)^T Q_f (x_H - x_ref_H)
    subject to: x_{t+1} = A_d(t) x_t + B_d(t) u_t + c_d

    Both A_d(t) and B_d(t) are time-varying through the barrier scale σ_k(t).

    The optimal control is: u_t = k_t - K_t @ (x_t - x_ref_t)

    Args:
        A_seq: (H, 13, 13) continuous-time state matrices (time-varying)
        B_seq: (H, 13, 12) continuous-time input matrices
        c: (13,) continuous-time affine term
        Q_diag: (13,) diagonal running cost weights
        R_diag: (12,) diagonal control cost weights
        Q_f_diag: (13,) diagonal terminal cost weights
        x_ref: (H+1, 13) reference trajectory
        dt: timestep
        horizon: H

    Returns:
        K_seq: (H, 12, 13) feedback gains
        k_seq: (H, 12) feedforward terms
    """
    nx, nu = 13, 12

    # Discretize affine term (constant)
    c_d = dt * c

    # Cost matrices (diagonal → full for matrix ops)
    Q = np.diag(Q_diag)
    # Light R floor — just enough for conditioning when B ≈ 0.
    # The S += 1e-6*I regularization handles the rest.
    R_diag_safe = np.maximum(R_diag, 1e-6)
    R = np.diag(R_diag_safe)
    Q_f = np.diag(Q_f_diag)

    # Contact no-slip cost: time-varying Q(t) = Q + w_slip * σ_sum(t) * E_slip
    w_slip = float(OCP.get("w_slip", 0.0))
    mass_val = float(ROBOT["mass"])
    E_slip = np.zeros((nx, nx))
    E_slip[3, 3] = 1.0  # vx
    E_slip[4, 4] = 1.0  # vy

    # Storage
    K_seq = np.zeros((horizon, nu, nx))
    k_seq = np.zeros((horizon, nu))

    # Terminal conditions — coverage terminal cost via DARE
    # DARE with time-averaged Q (includes slip cost)
    if w_slip > 0:
        sigma_sum_avg = sum(
            np.mean(B_seq[:, 3, 3*k]) * mass_val for k in range(4)
        )
        Q_dare = Q + w_slip * sigma_sum_avg * E_slip
    else:
        Q_dare = Q
    P_inf = solve_dare_nominal(A_seq, B_seq, Q_dare, R, dt)
    assert P_inf is not None, "DARE failed — non-stabilizable (Ā_d, B̄_d)"
    P = P_inf.copy()
    p = -P @ x_ref[horizon]

    # Backward Riccati recursion
    #
    # All matrix products use np.dot instead of the @ operator.
    # On ARM64 macOS (Apple Accelerate BLAS), the @ operator raises
    # spurious "divide by zero encountered in matmul" warnings —
    # results are correct but the FP exception flag is tripped.
    # np.dot delegates to a different code path that avoids this.
    dot = np.dot
    for t in range(horizon - 1, -1, -1):
        A_d = matrix_exp_discretize(A_seq[t], dt)  # expm(A·dt), exact
        B_d = dt * B_seq[t]  # first-order B_d (error O(A·dt²) ≈ 3e-5)

        # S = R + B_d^T P_{t+1} B_d  (12×12)
        PB = dot(P, B_d)  # (13, 12)
        S = R + dot(PB.T, B_d)
        S = 0.5 * (S + S.T)  # symmetrize
        S += 1e-6 * np.eye(nu)  # regularize for conditioning

        # Feedback gain: K_t = S^{-1} B_d^T P_{t+1} A_d  (12×13)
        K_t = np.linalg.solve(S, dot(PB.T, A_d))
        np.clip(K_t, -1e3, 1e3, out=K_t)  # bound gains
        K_seq[t] = K_t

        # Raw feedforward: η_t = S^{-1} B_d^T (P_{t+1} c_d + p_{t+1})
        Pc_plus_p = dot(P, c_d) + p
        eta_t = np.linalg.solve(S, dot(PB.T, c_d) + dot(B_d.T, p))

        # Output feedforward for interface: u = k_out - K(x - x_ref)
        k_seq[t] = -(dot(K_t, x_ref[t]) + eta_t)
        np.clip(k_seq[t], -1e3, 1e3, out=k_seq[t])

        # Closed-loop dynamics
        F_t = A_d - dot(B_d, K_t)  # (13, 13)

        # Time-varying Q: contact no-slip cost
        if w_slip > 0:
            sigma_sum_t = sum(B_seq[t, 3, 3*k] * mass_val for k in range(4))
            Q_t = Q + w_slip * sigma_sum_t * E_slip
        else:
            Q_t = Q

        # Update P_t — Joseph form with Q(t) (manifestly PSD)
        P_new = Q_t + dot(dot(F_t.T, P), F_t) + dot(dot(K_t.T, R), K_t)
        P = 0.5 * (P_new + P_new.T)  # symmetrize

        # Update p_t — affine uses Q (not Q_t): slip penalizes absolute v, not v-v_ref
        p = dot(F_t.T, Pc_plus_p) - dot(Q, x_ref[t])

    return K_seq, k_seq


def forward_simulate(x0, A_seq, B_seq, c, K_seq, k_seq, x_ref, h_seq,
                     epsilon, horizon, dt, Q_diag, R_diag, Q_f_diag,
                     constraints=None):
    """Centroidal forward simulation with Riccati gains. No MuJoCo.

    Computes the closed-loop trajectory and cost under the TV-LQR policy
    on the exactly-linear centroidal model:
        u_t = k_t - K_t @ (x_t - x_ref_t)
        x_{t+1} = A_d(t) @ x_t + B_d(t) @ u_t + c_d

    Both A_d(t) and B_d(t) are time-varying through σ_k(t).

    Args:
        x0: (13,) initial centroidal state
        A_seq: (H, 13, 13) continuous-time state matrices (time-varying)
        B_seq: (H, 13, 12) continuous-time input matrices
        c: (13,) continuous-time affine term
        K_seq: (H, 12, 13) feedback gains
        k_seq: (H, 12) feedforward terms
        x_ref: (H+1, 13) reference trajectory
        h_seq: (H+1, 4) foot heights per timestep
        epsilon: barrier/temperature parameter
        horizon: H
        dt: timestep
        Q_diag: (13,) running cost weights
        R_diag: (12,) control cost weights
        Q_f_diag: (13,) terminal cost weights
        constraints: optional dict with z_min, z_max, w_height,
                     w_height_barrier, phi_max, w_ori_barrier

    Returns:
        x_traj: (H+1, 13) state trajectory
        cost_total: scalar total cost (track + barrier + slip)
        cost_track: scalar tracking cost
        cost_barrier: scalar barrier cost
        cost_slip: scalar contact no-slip cost
    """
    nx, nu = 13, 12
    mass = float(ROBOT["mass"])
    g = 9.81

    Q = np.diag(Q_diag)
    R = np.diag(R_diag)
    Q_f = np.diag(Q_f_diag)

    x_traj = np.zeros((horizon + 1, nx))
    x_traj[0] = x0.copy()

    w_slip = float(OCP.get("w_slip", 0.0))
    J_track = 0.0
    J_barrier = 0.0
    J_slip = 0.0

    # Palindrome compile width: shared ε for all smooth blends.
    # Controls the transition sharpness of force clip, support floor,
    # and barrier floors.  As blend_eps → 0, recovers the hard ops.
    blend_eps = max(epsilon, 1e-4)
    force_limit = 100.0

    for t in range(horizon):
        x = x_traj[t]
        dx = x - x_ref[t]
        u = k_seq[t] - K_seq[t] @ dx

        # ── Smooth force clip (replaces np.clip(u, -100, 100)) ──
        # smooth_where(u + M, ...) ≈ max(u, -M)
        # smooth_where(M - u, ...) ≈ min(u, M)
        for j in range(nu):
            u[j] = smooth_where(u[j] + force_limit, u[j], -force_limit,
                                blend_eps)
            u[j] = smooth_where(force_limit - u[j], u[j], force_limit,
                                blend_eps)

        # ── Smooth support floor: Σ_k σ_k f_{k,z} ≥ mg ──
        sigma_t = np.array([B_seq[t, 3, 3*k] * mass for k in range(4)])
        eff_fz = sum(sigma_t[k] * u[3*k + 2] for k in range(4))
        required_fz = mass * g
        deficit = required_fz - eff_fz
        sigma_sum = max(sigma_t.sum(), 1e-6)
        # smooth_where(-deficit, 0, boost, ε): boost only when deficit > 0
        boost = smooth_where(-deficit, 0.0, deficit / sigma_sum, blend_eps)
        for k in range(4):
            u[3*k + 2] += boost
        # Re-clip after boost
        for j in range(nu):
            u[j] = smooth_where(u[j] + force_limit, u[j], -force_limit,
                                blend_eps)
            u[j] = smooth_where(force_limit - u[j], u[j], force_limit,
                                blend_eps)

        # Matrix exponential integrator: exact for the linear system
        x_traj[t + 1] = matrix_exp_step(A_seq[t], B_seq[t], c, x, u, dt)

        # Tracking cost
        J_track += dt * (dx @ Q @ dx + u @ R @ u)

        # Contact barrier: -ε Σ_k log(h_k + ε)  (already smooth)
        for k in range(4):
            h = h_seq[t, k]
            J_barrier -= dt * epsilon * safe_log(h + epsilon)

        # Height and orientation barriers (smooth via safe_log)
        if constraints is not None:
            pz = x_traj[t + 1, 2]

            # Height barrier — smooth floor via smooth_where
            z_lo_raw = pz - constraints["z_min"]
            z_hi_raw = constraints["z_max"] - pz
            z_lo = smooth_where(z_lo_raw - 1e-6, z_lo_raw, 1e-6, 1e-6)
            z_hi = smooth_where(z_hi_raw - 1e-6, z_hi_raw, 1e-6, 1e-6)
            J_barrier -= dt * constraints["w_height_barrier"] * epsilon * (
                safe_log(z_lo) + safe_log(z_hi)
            )

            # Height tracking (quadratic — already smooth)
            z_err = pz - constraints["z_target"]
            J_track += dt * constraints["w_height"] * z_err**2

            # Orientation barrier — smooth floor via smooth_where
            phi_x = x_traj[t + 1, 6]
            phi_y = x_traj[t + 1, 7]
            phi_max2 = constraints["phi_max"]**2
            ori_x_raw = phi_max2 - phi_x**2
            ori_y_raw = phi_max2 - phi_y**2
            ori_x = smooth_where(ori_x_raw - 1e-6, ori_x_raw, 1e-6, 1e-6)
            ori_y = smooth_where(ori_y_raw - 1e-6, ori_y_raw, 1e-6, 1e-6)
            J_barrier -= dt * constraints["w_ori_barrier"] * epsilon * (
                safe_log(ori_x) + safe_log(ori_y)
            )

        # Contact no-slip cost: penalize absolute velocity during contact
        if w_slip > 0:
            sigma_sum_t = sum(B_seq[t, 3, 3*k] * mass for k in range(4))
            J_slip += dt * w_slip * sigma_sum_t * (x[3]**2 + x[4]**2)

    # Terminal cost
    dx_T = x_traj[horizon] - x_ref[horizon]
    J_track += dx_T @ Q_f @ dx_T

    assert devil_check(x_traj, np.array([J_track, J_barrier, J_slip])), \
        "devil escaped in forward_simulate"

    return x_traj, J_track + J_barrier + J_slip, J_track, J_barrier, J_slip
