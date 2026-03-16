"""Run MPPI re-cycle experiment and record trajectory for visualization.

Usage:
    python run_experiment.py [--n_iters 50] [--seed 0] [--no-viz]

Runs the barrier-smoothed MPPI loop on the Go2 quadruped,
records MuJoCo states at each timestep of the best trajectory per iteration,
then launches a Flask server to visualize the result.
"""

import argparse
import json
import time
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np

from config import ROBOT, OCP, MPPI, CONSTRAINTS
from gait_sampler import (
    sample_student_t_torus,
    foot_height_schedule,
    barrier_foot_forces_reference,
    barrier_force_scale,
    entropy_empirical,
    effective_sample_size,
    weighted_circular_mean,
    weighted_circular_variance,
    trust_region_step,
)
from bspline_gait import (
    periodic_bspline_height, sample_bspline_gaits,
    periodic_bspline_logcontact, sample_logspace_gaits,
)
from riccati_lqr import build_AB, build_reference_trajectory, solve_tvlqr, forward_simulate
from quadruped_dynamics import (
    MuJoCoQuadruped, normalize_joints, _Q_NORM_MIN, _Q_NORM_MAX,
    _STANDING_QPOS_JOINTS,
)
from scipy.spatial.transform import Rotation


def run_rollout(n_iters: int = 50, seed: int = 0,
                verbose: bool = True) -> dict:
    """Run MPPI re-cycle and record the best trajectory at each iteration.

    Returns:
        result dict with:
          'trajectories': list of (H+1, nq+nv) arrays (best per iteration)
          'diagnostics': dict of lists (holonomy, entropy, epsilon, etc.)
          'final_trajectory': (H+1, nq+nv) from the last iteration's best
          'best_phi': final best gait phase
    """
    sim = MuJoCoQuadruped()
    N = MPPI["N_samples"]
    horizon = OCP["horizon"]
    dt = float(OCP["dt"])
    beta = ROBOT["duty_factor"]
    mass = ROBOT["mass"]

    # Student-t state
    nu = MPPI["nu_init"]
    mu = jnp.array([0.5, 0.5, 0.0])
    sigma = 0.5 * jnp.ones(3)  # diagonal std (Sigma = diag(sigma^2))
    Sigma = jnp.diag(sigma**2)
    delta_kl = MPPI["delta_kl"]

    # Dual ascent state
    epsilon = MPPI["epsilon_init"]
    # alpha_up/alpha_down read from MPPI dict at dual ascent step
    H_target = float(jnp.log(N))
    compression_rate = MPPI["compression_rate"]
    h_min = MPPI.get("h_min", 1e-4)

    # Initial state: standing
    x0 = np.zeros(13)
    x0[2] = ROBOT["standing_height"]

    # Storage
    all_trajectories = []
    diagnostics = {
        'holonomy': [], 'entropy': [], 'epsilon': [], 'ess': [],
        'cost_mean': [], 'cost_std': [], 'cost_best': [],
        'best_gait': [], 'mu': [],
        'kl': [], 'tr_alpha': [],
        # Cost decomposition (best sample per iteration)
        'best_vel': [], 'best_height': [],
        'best_height_bar': [], 'best_ori_bar': [], 'best_joint_bar': [],
        # Cost decomposition (mean across samples)
        'mean_vel': [], 'mean_height': [],
        'mean_height_bar': [], 'mean_ori_bar': [], 'mean_joint_bar': [],
    }

    key = jax.random.PRNGKey(seed)

    for k in range(n_iters):
        key, subkey = jax.random.split(key)
        t0 = time.time()

        # 1. Sample N gaits from student-t on T^3
        phis = sample_student_t_torus(nu, mu, Sigma, N, subkey)

        # 2. Evaluate each gait
        costs = np.zeros(N)
        best_cost = float('inf')
        best_traj = None
        best_phi = None

        # Per-sample cost components (for best sample diagnostics)
        comp_vel = np.zeros(N)
        comp_height = np.zeros(N)
        comp_height_bar = np.zeros(N)
        comp_ori_bar = np.zeros(N)
        comp_joint_bar = np.zeros(N)

        for i in range(N):
            phi_i = np.array(phis[i])

            # Continuous foot height schedule
            heights = np.array(foot_height_schedule(
                jnp.array(phi_i), beta, horizon, dt
            ))
            scales = np.array(barrier_force_scale(
                jnp.array(heights), epsilon, h_min
            ))
            h_max = ROBOT["swing_height"]
            height_fracs = np.clip(heights / h_max, 0.0, 1.0)

            # Simulate with impedance control (same as playback)
            sim.reset(x0)
            traj_qpos = np.zeros((horizon + 1, sim.model.nq))
            traj_qvel = np.zeros((horizon + 1, sim.model.nv))
            traj_qpos[0] = sim.data.qpos.copy()
            traj_qvel[0] = sim.data.qvel.copy()

            for t in range(horizon):
                sim.step_impedance(scales[t], height_fracs[t], dt, epsilon=epsilon)
                traj_qpos[t + 1] = sim.data.qpos.copy()
                traj_qvel[t + 1] = sim.data.qvel.copy()

            # Compute cost from recorded states — track components
            c_vel = 0.0
            c_height = 0.0
            c_height_bar = 0.0
            c_ori_bar = 0.0
            c_joint_bar = 0.0
            states_cent = np.zeros((horizon + 1, 13))
            sim.reset(x0)
            states_cent[0] = sim.get_centroidal_state()
            for t in range(horizon):
                sim.step_impedance(scales[t], height_fracs[t], dt, epsilon=epsilon)
                states_cent[t + 1] = sim.get_centroidal_state()
                vel_err = states_cent[t, 3:6] - np.array(OCP["target_velocity"])
                c_vel += float(np.sum(vel_err**2))

                # Height tracking (quadratic)
                z_err = states_cent[t, 2] - CONSTRAINTS["z_target"]
                c_height += CONSTRAINTS["w_height"] * float(z_err**2)

                # Height barrier (log-barrier, same ε as contact)
                pz = float(states_cent[t, 2])
                z_lo = max(pz - CONSTRAINTS["z_min"], 1e-6)
                z_hi = max(CONSTRAINTS["z_max"] - pz, 1e-6)
                c_height_bar -= CONSTRAINTS["w_height_barrier"] * epsilon * (
                    np.log(z_lo) + np.log(z_hi)
                )

                # Orientation barrier (pitch/roll within ±30°)
                phi_x = float(states_cent[t, 6])
                phi_y = float(states_cent[t, 7])
                phi_max2 = CONSTRAINTS["phi_max"]**2
                ori_x = max(phi_max2 - phi_x**2, 1e-6)
                ori_y = max(phi_max2 - phi_y**2, 1e-6)
                c_ori_bar -= CONSTRAINTS["w_ori_barrier"] * epsilon * (
                    np.log(ori_x) + np.log(ori_y)
                )

                # Joint-limit barrier (same ε as contact and height)
                q_joints = sim.data.qpos[7:19].copy()
                q_norm = normalize_joints(q_joints)
                q_lo_j = np.maximum(q_norm - _Q_NORM_MIN, 1e-4)
                q_hi_j = np.maximum(_Q_NORM_MAX - q_norm, 1e-4)
                c_joint_bar -= CONSTRAINTS["w_joint_barrier"] * epsilon * float(
                    np.sum(np.log(q_lo_j) + np.log(q_hi_j))
                )

            costs[i] = c_vel + c_height + c_height_bar + c_ori_bar + c_joint_bar
            comp_vel[i] = c_vel
            comp_height[i] = c_height
            comp_height_bar[i] = c_height_bar
            comp_ori_bar[i] = c_ori_bar
            comp_joint_bar[i] = c_joint_bar

            if costs[i] < best_cost:
                best_cost = costs[i]
                best_traj = np.concatenate([traj_qpos, traj_qvel], axis=1)
                best_phi = phi_i
                best_idx = i

        costs_jnp = jnp.array(costs)

        # 3. Boltzmann reweight
        log_w = -(costs_jnp - costs_jnp.min()) / epsilon
        weights = jax.nn.softmax(log_w)

        # 4. Diagnostics
        cost_var = float(jnp.var(costs_jnp))
        entropy = float(entropy_empirical(weights))
        ess = float(effective_sample_size(weights))

        # 5. Multiplicative dual ascent  [paper step 7]
        if entropy < H_target:
            epsilon *= MPPI["alpha_up"]
        else:
            epsilon *= MPPI["alpha_down"]
        epsilon = float(jnp.clip(epsilon, MPPI["epsilon_min"], MPPI["epsilon_max"]))

        # 6. Compress entropy bound
        H_target *= compression_rate

        # 7-8. Proposed update (unconstrained)
        mu_prop = weighted_circular_mean(phis, weights)
        circ_var = weighted_circular_variance(phis, weights)
        sigma_prop = jnp.sqrt(jnp.clip(circ_var, 0.01, 0.5))

        # KL trust region projection
        mu, sigma, kl_actual, tr_alpha = trust_region_step(
            mu, sigma, mu_prop, sigma_prop, delta_kl
        )
        Sigma = jnp.diag(sigma**2)

        # Record
        all_trajectories.append(best_traj)
        diagnostics['holonomy'].append(cost_var)
        diagnostics['entropy'].append(entropy)
        diagnostics['epsilon'].append(epsilon)
        diagnostics['ess'].append(ess)
        diagnostics['cost_mean'].append(float(costs_jnp.mean()))
        diagnostics['cost_std'].append(float(costs_jnp.std()))
        diagnostics['cost_best'].append(float(costs_jnp.min()))
        diagnostics['best_gait'].append(best_phi.tolist())
        diagnostics['mu'].append(mu.tolist())
        diagnostics['kl'].append(kl_actual)
        diagnostics['tr_alpha'].append(tr_alpha)
        # Cost decomposition — best sample
        diagnostics['best_vel'].append(float(comp_vel[best_idx]))
        diagnostics['best_height'].append(float(comp_height[best_idx]))
        diagnostics['best_height_bar'].append(float(comp_height_bar[best_idx]))
        diagnostics['best_ori_bar'].append(float(comp_ori_bar[best_idx]))
        diagnostics['best_joint_bar'].append(float(comp_joint_bar[best_idx]))
        # Cost decomposition — mean across samples
        diagnostics['mean_vel'].append(float(comp_vel.mean()))
        diagnostics['mean_height'].append(float(comp_height.mean()))
        diagnostics['mean_height_bar'].append(float(comp_height_bar.mean()))
        diagnostics['mean_ori_bar'].append(float(comp_ori_bar.mean()))
        diagnostics['mean_joint_bar'].append(float(comp_joint_bar.mean()))

        elapsed = time.time() - t0
        if verbose and (k % 5 == 0 or k == n_iters - 1):
            print(
                f"iter {k:3d} ({elapsed:.1f}s): "
                f"cost={diagnostics['cost_mean'][-1]:.2f}±{diagnostics['cost_std'][-1]:.2f}  "
                f"best={diagnostics['cost_best'][-1]:.2f}  "
                f"S={entropy:.2f}  "
                f"ε={epsilon:.4f}  "
                f"ESS={ess:.1f}  "
                f"KL={kl_actual:.3f} α={tr_alpha:.2f}  "
                f"φ*={np.array(best_phi).round(3)}  "
                f"μ={np.array(mu).round(3)}"
            )

    return {
        'trajectories': all_trajectories,
        'diagnostics': diagnostics,
        'final_trajectory': all_trajectories[-1],
        'best_phi': best_phi.tolist(),
        'n_iters': n_iters,
        'N_samples': N,
        'nq': sim.model.nq,
        'nv': sim.model.nv,
    }


def run_rollout_bspline(n_iters: int = 50, seed: int = 0,
                        verbose: bool = True) -> dict:
    """Run MPPI with B-spline foot height parameterization.

    Instead of sampling gait phases on T^3 and using a sinusoidal foot
    height schedule, sample periodic cubic B-spline control points.
    Boltzmann reweight operates on control points (Euclidean R^{4*n_knots}).

    Returns same structure as run_rollout for compatibility.
    """
    sim = MuJoCoQuadruped()
    N = MPPI["N_samples"]
    horizon = OCP["horizon"]
    dt = float(OCP["dt"])
    beta = ROBOT["duty_factor"]
    mass = ROBOT["mass"]
    n_knots = MPPI["n_knots"]
    T_stride = ROBOT["stride_period"]
    h_max = ROBOT["swing_height"]

    # Dual ascent state
    epsilon = MPPI["epsilon_init"]
    # alpha_up/alpha_down read from MPPI dict at dual ascent step
    H_target = float(jnp.log(N))
    compression_rate = MPPI["compression_rate"]
    h_min = MPPI.get("h_min", 1e-4)

    # Initial state: standing
    x0 = np.zeros(13)
    x0[2] = ROBOT["standing_height"]

    # B-spline mean and variance (Euclidean, not circular)
    beta_scale = MPPI.get("beta_scale", 3.0)
    cp_mean = np.zeros((4, n_knots))
    cp_std = beta_scale * 0.5 * np.ones((4, n_knots))

    rng = np.random.default_rng(seed)

    # Storage
    all_trajectories = []
    diagnostics = {
        'holonomy': [], 'entropy': [], 'epsilon': [], 'ess': [],
        'cost_mean': [], 'cost_std': [], 'cost_best': [],
        'best_gait': [], 'mu': [],
    }

    for k in range(n_iters):
        t0 = time.time()

        # 1. Sample N gaits as B-spline control points
        if k == 0:
            all_cp = sample_logspace_gaits(
                n_knots, N, T_stride, rng, beta_scale=beta_scale
            )
        else:
            # Sample around current mean with current variance (log-space, unconstrained)
            all_cp = np.zeros((N, 4, n_knots))
            for i in range(N):
                noise = rng.normal(0, 1, size=(4, n_knots)) * cp_std
                all_cp[i] = cp_mean + noise

        # 2. Evaluate each gait
        costs = np.zeros(N)
        best_cost = float('inf')
        best_traj = None
        best_cp = None

        for i in range(N):
            # Evaluate log-space B-spline → contact modes
            beta_i, sigma_i, heights = periodic_bspline_logcontact(
                all_cp[i], horizon + 1, T_stride, epsilon=epsilon
            )
            scales = sigma_i
            height_fracs = np.clip(heights / h_max, 0.0, 1.0)  # for impedance interpolation

            # Simulate with impedance control
            sim.reset(x0)
            traj_qpos = np.zeros((horizon + 1, sim.model.nq))
            traj_qvel = np.zeros((horizon + 1, sim.model.nv))
            traj_qpos[0] = sim.data.qpos.copy()
            traj_qvel[0] = sim.data.qvel.copy()

            for t in range(horizon):
                sim.step_impedance(scales[t], height_fracs[t], dt, epsilon=epsilon)
                traj_qpos[t + 1] = sim.data.qpos.copy()
                traj_qvel[t + 1] = sim.data.qvel.copy()

            # Compute cost
            cost = 0.0
            sim.reset(x0)
            states_cent = np.zeros((horizon + 1, 13))
            states_cent[0] = sim.get_centroidal_state()
            for t in range(horizon):
                sim.step_impedance(scales[t], height_fracs[t], dt, epsilon=epsilon)
                states_cent[t + 1] = sim.get_centroidal_state()
                vel_err = states_cent[t, 3:6] - np.array(OCP["target_velocity"])
                cost += float(np.sum(vel_err**2))

                z_err = states_cent[t, 2] - CONSTRAINTS["z_target"]
                cost += CONSTRAINTS["w_height"] * float(z_err**2)

                pz = float(states_cent[t, 2])
                z_lo = max(pz - CONSTRAINTS["z_min"], 1e-6)
                z_hi = max(CONSTRAINTS["z_max"] - pz, 1e-6)
                cost -= CONSTRAINTS["w_height_barrier"] * epsilon * (
                    np.log(z_lo) + np.log(z_hi)
                )

                phi_x = float(states_cent[t, 6])
                phi_y = float(states_cent[t, 7])
                phi_max2 = CONSTRAINTS["phi_max"]**2
                ori_x = max(phi_max2 - phi_x**2, 1e-6)
                ori_y = max(phi_max2 - phi_y**2, 1e-6)
                cost -= CONSTRAINTS["w_ori_barrier"] * epsilon * (
                    np.log(ori_x) + np.log(ori_y)
                )

                q_joints = sim.data.qpos[7:19].copy()
                q_norm = normalize_joints(q_joints)
                q_lo_j = np.maximum(q_norm - _Q_NORM_MIN, 1e-4)
                q_hi_j = np.maximum(_Q_NORM_MAX - q_norm, 1e-4)
                cost -= CONSTRAINTS["w_joint_barrier"] * epsilon * float(
                    np.sum(np.log(q_lo_j) + np.log(q_hi_j))
                )

            # Contact budget penalty (emergent periodicity constraint)
            C_min = CONSTRAINTS.get("C_min", 0.3)
            C_max = CONSTRAINTS.get("C_max", 0.7)
            avg_sigma_k = np.mean(sigma_i, axis=0)  # (4,) average contact per foot
            budget_lo = np.maximum(avg_sigma_k - C_min, 1e-8)
            budget_hi = np.maximum(C_max - avg_sigma_k, 1e-8)
            cost -= epsilon * float(
                np.sum(np.log(budget_lo) + np.log(budget_hi))
            )

            costs[i] = cost
            if cost < best_cost:
                best_cost = cost
                best_traj = np.concatenate([traj_qpos, traj_qvel], axis=1)
                best_cp = all_cp[i].copy()

        costs_jnp = jnp.array(costs)

        # 3. Boltzmann reweight
        log_w = -(costs_jnp - costs_jnp.min()) / epsilon
        weights = np.array(jax.nn.softmax(log_w))

        # 4. Diagnostics
        cost_var = float(jnp.var(costs_jnp))
        entropy = float(entropy_empirical(jnp.array(weights)))
        ess = float(effective_sample_size(jnp.array(weights)))

        # 5. Multiplicative dual ascent  [paper step 7]
        if entropy < H_target:
            epsilon *= MPPI["alpha_up"]
        else:
            epsilon *= MPPI["alpha_down"]
        epsilon = float(jnp.clip(epsilon, MPPI["epsilon_min"], MPPI["epsilon_max"]))

        # 6. Compress entropy bound
        H_target *= compression_rate

        # 7. Weighted mean in spline coefficient space (Euclidean)
        cp_mean = np.sum(weights[:, None, None] * all_cp, axis=0)

        # 8. Weighted variance in spline coefficient space
        diffs = all_cp - cp_mean[None, :, :]
        cp_var = np.sum(weights[:, None, None] * diffs**2, axis=0)
        cp_std = np.clip(np.sqrt(cp_var), 0.1, beta_scale)

        # Record
        all_trajectories.append(best_traj)
        diagnostics['holonomy'].append(cost_var)
        diagnostics['entropy'].append(entropy)
        diagnostics['epsilon'].append(epsilon)
        diagnostics['ess'].append(ess)
        diagnostics['cost_mean'].append(float(costs_jnp.mean()))
        diagnostics['cost_std'].append(float(costs_jnp.std()))
        diagnostics['cost_best'].append(float(costs_jnp.min()))
        diagnostics['best_gait'].append(best_cp.flatten().tolist())
        diagnostics['mu'].append(cp_mean.flatten().tolist())

        elapsed = time.time() - t0
        if verbose and (k % 5 == 0 or k == n_iters - 1):
            print(
                f"iter {k:3d} ({elapsed:.1f}s): "
                f"cost={diagnostics['cost_mean'][-1]:.2f}±{diagnostics['cost_std'][-1]:.2f}  "
                f"best={diagnostics['cost_best'][-1]:.2f}  "
                f"H={cost_var:.4f}  "
                f"S={entropy:.2f}  "
                f"ε={epsilon:.4f}  "
                f"ESS={ess:.1f}"
            )

    return {
        'trajectories': all_trajectories,
        'diagnostics': diagnostics,
        'final_trajectory': all_trajectories[-1],
        'best_phi': best_cp.flatten().tolist(),
        'best_cp': best_cp,
        'n_iters': n_iters,
        'N_samples': N,
        'nq': sim.model.nq,
        'nv': sim.model.nv,
        'mode': 'bspline',
    }


def run_rollout_tvlqr(n_iters: int = 50, seed: int = 0,
                      verbose: bool = True) -> dict:
    """MPPI with Riccati inner solve (TV-LQR) — log-space B-spline parameterization.

    For each MPPI iteration:
      1. Sample N log-space B-spline coefficients β_k ∈ ℝ^{4×n_knots}
      2. For each sample:
         a. β_k → σ_k = sigmoid(β_k) via periodic_bspline_logcontact
         b. Build A(t), B(t) from σ_k(t) on centroidal model
         c. Solve TV-LQR → K(t), k(t) via backward Riccati (expm discretization)
         d. Forward simulate on centroidal model (no MuJoCo)
         e. Evaluate cost (tracking + barrier + no-slip + contact budget)
      3. Boltzmann reweight on B-spline coefficients (path integral)
      4. Update mean/std of B-spline distribution
      5. Dual ascent on ε

    MuJoCo is NOT used during optimization. The centroidal model is
    exactly linear — forward simulation is a 13×13 matrix multiply per step.
    MuJoCo is only the plant (used in playback after convergence).
    """
    N = MPPI["N_samples"]
    horizon = OCP["horizon"]
    dt = float(OCP["dt"])
    mass = float(ROBOT["mass"])
    inertia = np.array(ROBOT["inertia"])
    foot_pos = np.array(ROBOT["foot_positions"])
    n_knots = MPPI["n_knots"]
    T_stride = ROBOT["stride_period"]
    h_max = ROBOT["swing_height"]

    Q_diag = np.array(OCP["Q_diag"])
    R_diag = np.array(OCP["R_diag"])
    Q_f_diag = np.array(OCP["Q_f_diag"])

    # Dual ascent state
    epsilon = MPPI["epsilon_init"]
    # alpha_up/alpha_down read from MPPI dict at dual ascent step
    H_target = float(jnp.log(N))
    compression_rate = MPPI["compression_rate"]
    h_min = MPPI.get("h_min", 1e-4)

    # Initial state: standing
    x0 = np.zeros(13)
    x0[2] = ROBOT["standing_height"]

    # Reference trajectory for Riccati
    x_ref = build_reference_trajectory(horizon, dt)

    # Log-space B-spline mean and variance
    beta_scale = float(MPPI.get("beta_scale", 3.0))
    cp_mean = np.zeros((4, n_knots))
    cp_std = beta_scale * 0.5 * np.ones((4, n_knots))

    rng = np.random.default_rng(seed)

    # Storage
    all_trajectories = []
    diagnostics = {
        'holonomy': [], 'entropy': [], 'epsilon': [], 'ess': [],
        'cost_mean': [], 'cost_std': [], 'cost_best': [],
        'best_gait': [], 'mu': [],
        # Cost decomposition (best sample per iteration)
        'best_vel': [], 'best_height': [],
        'best_height_bar': [], 'best_ori_bar': [], 'best_joint_bar': [],
        'best_control': [], 'best_contact_bar': [], 'best_slip': [],
        # Cost decomposition (mean across samples)
        'mean_vel': [], 'mean_height': [],
        'mean_height_bar': [], 'mean_ori_bar': [], 'mean_joint_bar': [],
        'mean_control': [], 'mean_contact_bar': [], 'mean_slip': [],
    }

    for k in range(n_iters):
        t0 = time.time()

        # 1. Sample N gaits as log-space B-spline coefficients
        if k == 0:
            all_cp = sample_logspace_gaits(
                n_knots, N, T_stride, rng, beta_scale=beta_scale
            )
        else:
            all_cp = np.zeros((N, 4, n_knots))
            for i in range(N):
                noise = rng.normal(0, 1, size=(4, n_knots)) * cp_std
                all_cp[i] = cp_mean + noise  # unconstrained in log space

        # 2. Evaluate each gait with Riccati inner solve
        costs = np.zeros(N)
        best_cost = float('inf')
        best_traj_centroidal = None
        best_cp = None
        best_idx = 0

        # Per-sample cost components
        comp_vel = np.zeros(N)
        comp_height = np.zeros(N)
        comp_height_bar = np.zeros(N)
        comp_ori_bar = np.zeros(N)
        comp_joint_bar = np.zeros(N)
        comp_control = np.zeros(N)
        comp_contact_bar = np.zeros(N)
        comp_slip = np.zeros(N)

        for i in range(N):
            # a. Log-space B-spline → β_k → σ_k (action-cycle → state-cycle)
            beta_i, sigma_i, heights = periodic_bspline_logcontact(
                all_cp[i], horizon + 1, T_stride, epsilon=epsilon
            )
            scales = sigma_i  # σ_k = sigmoid(β_k), already in (0,1)
            height_fracs = np.clip(heights / h_max, 0.0, 1.0)

            # b-c. Build A(t), B(t) and solve TV-LQR
            sigma_seq = scales[:horizon]  # (H, 4)
            A_seq, B_seq, c_dyn = build_AB(mass, inertia, foot_pos, sigma_seq)
            K_seq, k_seq = solve_tvlqr(
                A_seq, B_seq, c_dyn, Q_diag, R_diag, Q_f_diag, x_ref, dt, horizon
            )

            # Reject samples where Riccati produced NaN
            if not (np.all(np.isfinite(K_seq)) and np.all(np.isfinite(k_seq))):
                costs[i] = 1e8
                comp_vel[i] = 1e8
                continue

            # d. Forward simulate on centroidal model (no MuJoCo)
            x_traj, cost_total, cost_track, cost_barrier, cost_slip = forward_simulate(
                x0, A_seq, B_seq, c_dyn, K_seq, k_seq, x_ref, heights,
                epsilon, horizon, dt, Q_diag, R_diag, Q_f_diag,
                constraints=CONSTRAINTS
            )
            # Contact budget penalty (emergent periodicity constraint)
            C_min = CONSTRAINTS.get("C_min", 0.3)
            C_max = CONSTRAINTS.get("C_max", 0.7)
            avg_sigma_k = np.mean(sigma_i, axis=0)  # (4,)
            budget_lo = np.maximum(avg_sigma_k - C_min, 1e-8)
            budget_hi = np.maximum(C_max - avg_sigma_k, 1e-8)
            cost_budget = -epsilon * float(
                np.sum(np.log(budget_lo) + np.log(budget_hi))
            )
            cost_total += cost_budget

            costs[i] = cost_total
            comp_vel[i] = cost_track
            comp_height[i] = 0.0
            comp_height_bar[i] = 0.0
            comp_ori_bar[i] = 0.0
            comp_joint_bar[i] = 0.0
            comp_control[i] = 0.0
            comp_contact_bar[i] = cost_barrier + cost_budget
            comp_slip[i] = cost_slip

            if costs[i] < best_cost:
                best_cost = costs[i]
                # Store centroidal trajectory (no MuJoCo qpos/qvel during optimization)
                best_traj_centroidal = x_traj.copy()
                best_cp = all_cp[i].copy()
                best_heights = heights.copy()
                best_scales = scales.copy()
                best_idx = i

        costs_jnp = jnp.array(costs)

        # 3. Boltzmann reweight
        log_w = -(costs_jnp - costs_jnp.min()) / epsilon
        weights = np.array(jax.nn.softmax(log_w))

        # 4. Diagnostics
        cost_var = float(jnp.var(costs_jnp))
        entropy = float(entropy_empirical(jnp.array(weights)))
        ess = float(effective_sample_size(jnp.array(weights)))

        # 5. Multiplicative dual ascent  [paper step 7]
        if entropy < H_target:
            epsilon *= MPPI["alpha_up"]
        else:
            epsilon *= MPPI["alpha_down"]
        epsilon = float(jnp.clip(epsilon, MPPI["epsilon_min"], MPPI["epsilon_max"]))

        # 6. Compress entropy bound
        H_target *= compression_rate

        # 7. Weighted mean in B-spline coefficient space
        cp_mean = np.sum(weights[:, None, None] * all_cp, axis=0)

        # 8. Weighted variance (in log space — unconstrained)
        diffs = all_cp - cp_mean[None, :, :]
        cp_var = np.sum(weights[:, None, None] * diffs**2, axis=0)
        cp_std = np.clip(np.sqrt(cp_var), 0.1, beta_scale)

        # Record (centroidal trajectories during optimization, no MuJoCo)
        all_trajectories.append(best_traj_centroidal)
        diagnostics['holonomy'].append(cost_var)
        diagnostics['entropy'].append(entropy)
        diagnostics['epsilon'].append(epsilon)
        diagnostics['ess'].append(ess)
        diagnostics['cost_mean'].append(float(costs_jnp.mean()))
        diagnostics['cost_std'].append(float(costs_jnp.std()))
        diagnostics['cost_best'].append(float(costs_jnp.min()))
        diagnostics['best_gait'].append(best_cp.flatten().tolist())
        diagnostics['mu'].append(cp_mean.flatten().tolist())
        diagnostics['best_vel'].append(float(comp_vel[best_idx]))
        diagnostics['best_height'].append(float(comp_height[best_idx]))
        diagnostics['best_height_bar'].append(float(comp_height_bar[best_idx]))
        diagnostics['best_ori_bar'].append(float(comp_ori_bar[best_idx]))
        diagnostics['best_joint_bar'].append(float(comp_joint_bar[best_idx]))
        diagnostics['best_control'].append(float(comp_control[best_idx]))
        diagnostics['best_contact_bar'].append(float(comp_contact_bar[best_idx]))
        diagnostics['best_slip'].append(float(comp_slip[best_idx]))
        diagnostics['mean_vel'].append(float(comp_vel.mean()))
        diagnostics['mean_height'].append(float(comp_height.mean()))
        diagnostics['mean_height_bar'].append(float(comp_height_bar.mean()))
        diagnostics['mean_ori_bar'].append(float(comp_ori_bar.mean()))
        diagnostics['mean_joint_bar'].append(float(comp_joint_bar.mean()))
        diagnostics['mean_control'].append(float(comp_control.mean()))
        diagnostics['mean_contact_bar'].append(float(comp_contact_bar.mean()))
        diagnostics['mean_slip'].append(float(comp_slip.mean()))

        elapsed = time.time() - t0
        if verbose and (k % 5 == 0 or k == n_iters - 1):
            print(
                f"iter {k:3d} ({elapsed:.1f}s): "
                f"cost={diagnostics['cost_mean'][-1]:.2f}±{diagnostics['cost_std'][-1]:.2f}  "
                f"best={diagnostics['cost_best'][-1]:.2f}  "
                f"S={entropy:.2f}  "
                f"ε={epsilon:.4f}  "
                f"ESS={ess:.1f}"
            )

    return {
        'trajectories': all_trajectories,
        'diagnostics': diagnostics,
        'final_trajectory': all_trajectories[-1],
        'best_phi': best_cp.flatten().tolist(),
        'best_cp': best_cp,
        'best_heights': best_heights,
        'best_scales': best_scales,
        'x_ref': x_ref,
        'n_iters': n_iters,
        'N_samples': N,
        'nq': 19,  # Go2: 7 (base) + 12 (joints)
        'nv': 18,  # Go2: 6 (base) + 12 (joints)
        'mode': 'tvlqr',
    }


def playback_trajectory_tvlqr(sim, cp, epsilon, duration=2.0,
                               verbose=True):
    """Playback using pure impedance controller (step_impedance).

    The Riccati gains are no longer needed at playback — the impedance
    controller realizes the gait autonomously via barrier-modulated PID.
    MuJoCo is ONLY the plant here.
    """
    dt = float(OCP["dt"])
    h_min = MPPI.get("h_min", 1e-4)
    h_max = ROBOT["swing_height"]
    T_stride = ROBOT["stride_period"]
    n_steps = int(duration / dt)

    if verbose:
        print(f"\nPlayback (impedance): ε={epsilon:.4f}, "
              f"duration={duration}s, {n_steps} steps")

    # Build gait schedule (log-space B-spline → contact modes)
    beta_sched, sigma_sched, heights = periodic_bspline_logcontact(
        cp, n_steps + 1, T_stride, epsilon=epsilon
    )
    scales = sigma_sched
    height_fracs = np.clip(heights / h_max, 0.0, 1.0)  # for impedance interpolation

    # Simulate with impedance controller (no Riccati gains needed)
    x0 = np.zeros(13)
    x0[2] = ROBOT["standing_height"]
    sim.reset(x0)

    traj_qpos = np.zeros((n_steps + 1, sim.model.nq))
    traj_qvel = np.zeros((n_steps + 1, sim.model.nv))
    traj_torques = np.zeros((n_steps, 12))
    traj_contacts = np.zeros((n_steps, 4))
    traj_com = np.zeros((n_steps + 1, 13))
    traj_qpos[0] = sim.data.qpos.copy()
    traj_qvel[0] = sim.data.qvel.copy()
    traj_com[0] = sim.get_centroidal_state()

    for t in range(n_steps):
        sim.step_impedance(scales[t], height_fracs[t], dt, epsilon=epsilon)
        traj_qpos[t + 1] = sim.data.qpos.copy()
        traj_qvel[t + 1] = sim.data.qvel.copy()
        traj_torques[t] = sim.data.ctrl[:12].copy()
        traj_contacts[t] = sim.get_contact_feet()
        traj_com[t + 1] = sim.get_centroidal_state()

        if verbose and (t + 1) % 50 == 0:
            pos = sim.data.qpos[:3]
            print(f"  t={dt*(t+1):.2f}s  pos=[{pos[0]:.3f}, "
                  f"{pos[1]:.3f}, {pos[2]:.3f}]")

    trajectory = np.concatenate([traj_qpos, traj_qvel], axis=1)

    if verbose:
        final_pos = sim.data.qpos[:3]
        print(f"  Final pos: [{final_pos[0]:.3f}, {final_pos[1]:.3f}, "
              f"{final_pos[2]:.3f}]")
        print(f"  Avg forward speed: {final_pos[0]/duration:.3f} m/s")

    return {
        'trajectory': trajectory,
        'torques': traj_torques,
        'contacts': traj_contacts,
        'com': traj_com,
        'barrier_scales': scales,
        'foot_heights': heights,
        'height_fracs': height_fracs,
        'dt': dt,
        'cp': cp,
        'epsilon': epsilon,
    }


def playback_trajectory_bspline(sim, cp, epsilon, duration=2.0,
                                verbose=True):
    """Playback using B-spline foot height schedule."""
    dt = float(OCP["dt"])
    h_min = MPPI.get("h_min", 1e-4)
    h_max = ROBOT["swing_height"]
    T_stride = ROBOT["stride_period"]
    n_steps = int(duration / dt)

    if verbose:
        print(f"\nPlayback (B-spline): ε={epsilon:.4f}, "
              f"duration={duration}s, {n_steps} steps")

    beta_sched, sigma_sched, heights = periodic_bspline_logcontact(
        cp, n_steps + 1, T_stride, epsilon=epsilon
    )
    scales = sigma_sched
    height_fracs = np.clip(heights / h_max, 0.0, 1.0)  # for impedance interpolation

    x0 = np.zeros(13)
    x0[2] = ROBOT["standing_height"]
    sim.reset(x0)

    traj_qpos = np.zeros((n_steps + 1, sim.model.nq))
    traj_qvel = np.zeros((n_steps + 1, sim.model.nv))
    traj_torques = np.zeros((n_steps, 12))
    traj_contacts = np.zeros((n_steps, 4))
    traj_com = np.zeros((n_steps + 1, 13))
    traj_qpos[0] = sim.data.qpos.copy()
    traj_qvel[0] = sim.data.qvel.copy()
    traj_com[0] = sim.get_centroidal_state()

    for t in range(n_steps):
        sim.step_impedance(scales[t], height_fracs[t], dt, epsilon=epsilon)
        traj_qpos[t + 1] = sim.data.qpos.copy()
        traj_qvel[t + 1] = sim.data.qvel.copy()
        traj_torques[t] = sim.data.ctrl[:12].copy()
        traj_contacts[t] = sim.get_contact_feet()
        traj_com[t + 1] = sim.get_centroidal_state()

        if verbose and (t + 1) % 50 == 0:
            pos = sim.data.qpos[:3]
            print(f"  t={dt*(t+1):.2f}s  pos=[{pos[0]:.3f}, "
                  f"{pos[1]:.3f}, {pos[2]:.3f}]")

    trajectory = np.concatenate([traj_qpos, traj_qvel], axis=1)

    if verbose:
        final_pos = sim.data.qpos[:3]
        print(f"  Final pos: [{final_pos[0]:.3f}, {final_pos[1]:.3f}, "
              f"{final_pos[2]:.3f}]")
        print(f"  Avg forward speed: {final_pos[0]/duration:.3f} m/s")

    return {
        'trajectory': trajectory,
        'torques': traj_torques,
        'contacts': traj_contacts,
        'com': traj_com,
        'barrier_scales': scales,
        'foot_heights': heights,
        'height_fracs': height_fracs,
        'dt': dt,
        'cp': cp,
        'epsilon': epsilon,
    }


def playback_trajectory(sim: 'MuJoCoQuadruped', phi: np.ndarray,
                        epsilon: float, duration: float = 2.0,
                        verbose: bool = True) -> np.ndarray:
    """Solve-then-play: impedance-controlled open-loop trajectory from φ*.

    The gait phase φ defines a periodic contact pattern. We generate the
    barrier-smoothed height schedule and use impedance control (PD with
    barrier-modulated gains) to realize it in MuJoCo. No force-to-torque
    mapping — MuJoCo's contact solver provides ground reaction forces
    naturally when stiff stance legs press against the ground.

    The PD controller IS the impedance controller:
        τ = K_p(q_des - q) - K_d q̇
    with gains modulated by the barrier scale σ_k = λ_k/(λ_k + 1):
        K_p(t) = K_p^swing + (K_p^stance - K_p^swing) · σ_k(t)

    Args:
        sim: MuJoCo quadruped simulator
        phi: (3,) converged gait phase offsets
        epsilon: converged barrier/temperature parameter
        duration: total simulation time (seconds)
        verbose: print progress

    Returns:
        dict with 'trajectory' (n_steps+1, nq+nv) and diagnostic arrays
    """
    dt = float(OCP["dt"])
    beta = ROBOT["duty_factor"]
    h_min = MPPI.get("h_min", 1e-4)
    h_max = ROBOT["swing_height"]
    n_steps = int(duration / dt)

    if verbose:
        print(f"\nPlayback (impedance): φ*={phi.round(3)}, ε={epsilon:.4f}, "
              f"duration={duration}s, {n_steps} steps")

    # Generate foot height schedule for the full duration
    heights = np.array(foot_height_schedule(
        jnp.array(phi), beta, n_steps, dt
    ))
    # Barrier scale: σ_k = λ_k/(λ_k+1), ≈1 stance, ≈0 swing
    scales = np.array(barrier_force_scale(
        jnp.array(heights), epsilon, h_min
    ))
    # Normalized foot height fraction: 0 = ground, 1 = peak swing
    height_fracs = np.clip(heights / h_max, 0.0, 1.0)

    # Simulate open-loop from standing with impedance control
    x0 = np.zeros(13)
    x0[2] = ROBOT["standing_height"]
    sim.reset(x0)

    traj_qpos = np.zeros((n_steps + 1, sim.model.nq))
    traj_qvel = np.zeros((n_steps + 1, sim.model.nv))
    traj_torques = np.zeros((n_steps, 12))
    traj_contacts = np.zeros((n_steps, 4))
    traj_com = np.zeros((n_steps + 1, 13))
    traj_qpos[0] = sim.data.qpos.copy()
    traj_qvel[0] = sim.data.qvel.copy()
    traj_com[0] = sim.get_centroidal_state()

    for t in range(n_steps):
        sim.step_impedance(scales[t], height_fracs[t], dt, epsilon=epsilon)
        traj_qpos[t + 1] = sim.data.qpos.copy()
        traj_qvel[t + 1] = sim.data.qvel.copy()
        traj_torques[t] = sim.data.ctrl[:12].copy()
        traj_contacts[t] = sim.get_contact_feet()
        traj_com[t + 1] = sim.get_centroidal_state()

        if verbose and (t + 1) % 50 == 0:
            pos = sim.data.qpos[:3]
            print(f"  t={dt*(t+1):.2f}s  pos=[{pos[0]:.3f}, "
                  f"{pos[1]:.3f}, {pos[2]:.3f}]")

    trajectory = np.concatenate([traj_qpos, traj_qvel], axis=1)

    if verbose:
        final_pos = sim.data.qpos[:3]
        print(f"  Final pos: [{final_pos[0]:.3f}, {final_pos[1]:.3f}, "
              f"{final_pos[2]:.3f}]")
        print(f"  Avg forward speed: {final_pos[0]/duration:.3f} m/s")

    return {
        'trajectory': trajectory,
        'torques': traj_torques,
        'contacts': traj_contacts,
        'com': traj_com,
        'barrier_scales': scales,
        'foot_heights': heights,
        'height_fracs': height_fracs,
        'dt': dt,
        'phi': phi,
        'epsilon': epsilon,
    }


def centroidal_to_mujoco(x_traj_cent):
    """Convert centroidal trajectory (N,13) to MuJoCo qpos+qvel (N,37).

    Sets base position/orientation from centroidal state,
    joints at standing configuration, velocities from centroidal.
    """
    N = x_traj_cent.shape[0]
    nq, nv = 19, 18
    traj = np.zeros((N, nq + nv))

    for i in range(N):
        x = x_traj_cent[i]
        p = x[0:3]
        phi = x[6:9]  # Euler angles (roll, pitch, yaw)
        v = x[3:6]
        omega = x[9:12]

        # qpos: [x,y,z, qw,qx,qy,qz, 12 joints]
        traj[i, 0:3] = p
        quat = Rotation.from_euler('xyz', phi).as_quat()  # [x,y,z,w]
        traj[i, 3] = quat[3]   # w
        traj[i, 4:7] = quat[:3]  # x,y,z
        traj[i, 7:19] = _STANDING_QPOS_JOINTS

        # qvel: [vx,vy,vz, wx,wy,wz, 12 joint vels]
        traj[i, nq:nq+3] = v
        traj[i, nq+3:nq+6] = omega

    return traj


def solve_trajectory_mujoco(sim, cp, epsilon, best_centroidal, duration=2.0,
                             verbose=True):
    """Replay solved gait in MuJoCo with impedance BUT drive base from centroidal.

    This shows what the optimizer 'intended' — the centroidal trajectory
    sets the base, while joints follow the impedance controller.
    """
    dt = float(OCP["dt"])
    h_min = MPPI.get("h_min", 1e-4)
    h_max = ROBOT["swing_height"]
    T_stride = ROBOT["stride_period"]
    n_steps = int(duration / dt)

    if verbose:
        print(f"\nSolve trajectory: {n_steps} steps")

    beta_sched, sigma_sched, heights = periodic_bspline_logcontact(
        cp, n_steps + 1, T_stride, epsilon=epsilon
    )
    scales = sigma_sched
    height_fracs = np.clip(heights / h_max, 0.0, 1.0)  # for impedance interpolation

    # Build centroidal reference for the full duration
    horizon = OCP["horizon"]
    mass = float(ROBOT["mass"])
    inertia = np.array(ROBOT["inertia"])
    foot_pos = np.array(ROBOT["foot_positions"])
    Q_diag = np.array(OCP["Q_diag"])
    R_diag = np.array(OCP["R_diag"])
    Q_f_diag = np.array(OCP["Q_f_diag"])
    x_ref = build_reference_trajectory(horizon, dt)

    # Use the first horizon steps of the gait to get the solve trajectory
    sigma_seq = scales[:horizon]
    A_seq, B_seq, c_dyn = build_AB(mass, inertia, foot_pos, sigma_seq)
    K_seq, k_seq = solve_tvlqr(
        A_seq, B_seq, c_dyn, Q_diag, R_diag, Q_f_diag, x_ref, dt, horizon
    )

    x0 = np.zeros(13)
    x0[2] = ROBOT["standing_height"]
    x_traj, _, _, _, _ = forward_simulate(
        x0, A_seq, B_seq, c_dyn, K_seq, k_seq, x_ref,
        heights[:horizon+1], epsilon, horizon, dt, Q_diag, R_diag, Q_f_diag,
        constraints=CONSTRAINTS
    )

    # Convert centroidal trajectory to MuJoCo format
    # For steps beyond horizon, hold the final state
    full_cent = np.zeros((n_steps + 1, 13))
    n_copy = min(x_traj.shape[0], n_steps + 1)
    full_cent[:n_copy] = x_traj[:n_copy]
    for t in range(n_copy, n_steps + 1):
        full_cent[t] = x_traj[-1]

    solve_traj = centroidal_to_mujoco(full_cent)

    if verbose:
        print(f"  Solve vx at t=0.5s: {full_cent[50, 3]:.3f} m/s")
        print(f"  Solve final pos: [{full_cent[-1,0]:.3f}, "
              f"{full_cent[-1,1]:.3f}, {full_cent[-1,2]:.3f}]")

    return solve_traj


def save_result(result: dict, path: str = "rollout_data.npz"):
    """Save rollout data for visualization."""
    save_dict = {
        'final_trajectory': result['final_trajectory'],
        'all_trajectories': np.array(result['trajectories']),
    }
    if 'x_ref' in result:
        save_dict['x_ref'] = np.array(result['x_ref'])
    if 'best_heights' in result:
        save_dict['best_heights'] = np.array(result['best_heights'])
    if 'best_scales' in result:
        save_dict['best_scales'] = np.array(result['best_scales'])
    if 'playback_trajectory' in result:
        save_dict['playback_trajectory'] = result['playback_trajectory']
    if 'solve_trajectory' in result:
        save_dict['solve_trajectory'] = result['solve_trajectory']
    if 'playback_details' in result:
        pb = result['playback_details']
        save_dict['pb_torques'] = pb['torques']
        save_dict['pb_contacts'] = pb['contacts']
        save_dict['pb_com'] = pb['com']
        save_dict['pb_barrier_scales'] = pb['barrier_scales']
        save_dict['pb_foot_heights'] = pb['foot_heights']
        save_dict['pb_height_fracs'] = pb['height_fracs']

    np.savez(path, **save_dict)

    diag_path = Path(path).with_suffix('.json')
    meta = {
        'diagnostics': result['diagnostics'],
        'best_phi': result['best_phi'],
        'n_iters': result['n_iters'],
        'N_samples': result.get('N_samples', MPPI['N_samples']),
        'nq': result['nq'],
        'nv': result['nv'],
        'has_playback': 'playback_trajectory' in result,
        'has_solve': 'solve_trajectory' in result,
        'playback_duration': result.get('playback_duration', 0),
    }
    with open(diag_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"Saved trajectory to {path}")
    print(f"Saved diagnostics to {diag_path}")


def main():
    parser = argparse.ArgumentParser(description="Run MPPI re-cycle experiment")
    parser.add_argument('--n_iters', type=int, default=30,
                        help='Number of MPPI iterations')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--no-viz', action='store_true',
                        help='Skip Flask visualization')
    parser.add_argument('--output', type=str, default='rollout_data.npz')
    parser.add_argument('--playback', type=float, default=2.0,
                        help='Playback duration in seconds (0 to skip)')
    parser.add_argument('--bspline', action='store_true',
                        help='Use B-spline foot height parameterization')
    parser.add_argument('--simple', action='store_true',
                        help='Use phase-only mode (no Riccati)')
    args = parser.parse_args()

    if args.simple:
        mode_str = "phase"
    elif args.bspline:
        mode_str = "B-spline"
    else:
        mode_str = "TV-LQR"
    print(f"Running MPPI re-cycle ({mode_str}): {args.n_iters} iterations, "
          f"N={MPPI['N_samples']} samples, seed={args.seed}")
    print(f"Target velocity: {np.array(OCP['target_velocity'])}")
    if not args.simple:
        print(f"B-spline: n_knots={MPPI['n_knots']}")
    print()

    if args.simple:
        result = run_rollout(n_iters=args.n_iters, seed=args.seed)
    elif args.bspline:
        result = run_rollout_bspline(n_iters=args.n_iters, seed=args.seed)
    else:
        result = run_rollout_tvlqr(n_iters=args.n_iters, seed=args.seed)

    # Solve-then-play: use converged result for a long open-loop trajectory
    if args.playback > 0:
        sim = MuJoCoQuadruped()
        final_epsilon = result['diagnostics']['epsilon'][-1]

        if args.simple:
            best_phi = np.array(result['best_phi'])
            pb = playback_trajectory(
                sim, best_phi, final_epsilon,
                duration=args.playback
            )
        elif args.bspline:
            best_cp = result['best_cp']
            pb = playback_trajectory_bspline(
                sim, best_cp, final_epsilon,
                duration=args.playback
            )
        else:
            best_cp = result['best_cp']
            pb = playback_trajectory_tvlqr(
                sim, best_cp, final_epsilon,
                duration=args.playback
            )
        result['playback_trajectory'] = pb['trajectory']
        result['playback_duration'] = args.playback
        result['playback_details'] = pb
        result['final_trajectory'] = pb['trajectory']

        # Also generate the solved (centroidal) trajectory for comparison
        if not args.simple:
            best_cent = result['trajectories'][-1]  # last iter centroidal traj
            solve_traj = solve_trajectory_mujoco(
                sim, result['best_cp'], final_epsilon,
                best_cent, duration=args.playback
            )
            result['solve_trajectory'] = solve_traj

    save_result(result, args.output)

    if not args.no_viz:
        print("\nLaunching visualization server...")
        from visualizer import create_app
        app = create_app(args.output)
        app.run(host='127.0.0.1', port=5001)


if __name__ == '__main__':
    main()
