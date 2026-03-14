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
)
from quadruped_dynamics import (
    MuJoCoQuadruped, normalize_joints, _Q_NORM_MIN, _Q_NORM_MAX,
)


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
    Sigma = 0.25 * jnp.eye(3)

    # Dual ascent state
    epsilon = MPPI["epsilon_init"]
    alpha_dual = MPPI["alpha_dual"]
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

            # Compute cost from recorded states
            cost = 0.0
            states_cent = np.zeros((horizon + 1, 13))
            sim.reset(x0)
            states_cent[0] = sim.get_centroidal_state()
            for t in range(horizon):
                sim.step_impedance(scales[t], height_fracs[t], dt, epsilon=epsilon)
                states_cent[t + 1] = sim.get_centroidal_state()
                vel_err = states_cent[t, 3:6] - np.array(OCP["target_velocity"])
                cost += float(np.sum(vel_err**2))

                # Height tracking (quadratic)
                z_err = states_cent[t, 2] - CONSTRAINTS["z_target"]
                cost += CONSTRAINTS["w_height"] * float(z_err**2)

                # Height barrier (log-barrier, same ε as contact)
                pz = float(states_cent[t, 2])
                z_lo = max(pz - CONSTRAINTS["z_min"], 1e-6)
                z_hi = max(CONSTRAINTS["z_max"] - pz, 1e-6)
                cost -= CONSTRAINTS["w_height_barrier"] * epsilon * (
                    np.log(z_lo) + np.log(z_hi)
                )

                # Orientation barrier (pitch/roll within ±30°)
                phi_x = float(states_cent[t, 6])
                phi_y = float(states_cent[t, 7])
                phi_max2 = CONSTRAINTS["phi_max"]**2
                ori_x = max(phi_max2 - phi_x**2, 1e-6)
                ori_y = max(phi_max2 - phi_y**2, 1e-6)
                cost -= CONSTRAINTS["w_ori_barrier"] * epsilon * (
                    np.log(ori_x) + np.log(ori_y)
                )

                # Joint-limit barrier (same ε as contact and height)
                q_joints = sim.data.qpos[7:19].copy()
                q_norm = normalize_joints(q_joints)
                q_lo_j = np.maximum(q_norm - _Q_NORM_MIN, 1e-4)
                q_hi_j = np.maximum(_Q_NORM_MAX - q_norm, 1e-4)
                cost -= CONSTRAINTS["w_joint_barrier"] * epsilon * float(
                    np.sum(np.log(q_lo_j) + np.log(q_hi_j))
                )

            costs[i] = cost
            if cost < best_cost:
                best_cost = cost
                best_traj = np.concatenate([traj_qpos, traj_qvel], axis=1)
                best_phi = phi_i

        costs_jnp = jnp.array(costs)

        # 3. Boltzmann reweight
        log_w = -(costs_jnp - costs_jnp.min()) / epsilon
        weights = jax.nn.softmax(log_w)

        # 4. Diagnostics
        cost_var = float(jnp.var(costs_jnp))
        entropy = float(entropy_empirical(weights))
        ess = float(effective_sample_size(weights))

        # 5. Dual ascent
        epsilon += alpha_dual * (H_target - entropy)
        epsilon = float(jnp.clip(epsilon, MPPI["epsilon_min"], MPPI["epsilon_max"]))

        # 6. Compress entropy bound
        H_target *= compression_rate

        # 7. Update student-t center
        mu = weighted_circular_mean(phis, weights)

        # 8. Update scale matrix
        circ_var = weighted_circular_variance(phis, weights)
        Sigma = jnp.diag(jnp.clip(circ_var, 0.01, 0.5))

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

        elapsed = time.time() - t0
        if verbose and (k % 5 == 0 or k == n_iters - 1):
            print(
                f"iter {k:3d} ({elapsed:.1f}s): "
                f"cost={diagnostics['cost_mean'][-1]:.2f}±{diagnostics['cost_std'][-1]:.2f}  "
                f"best={diagnostics['cost_best'][-1]:.2f}  "
                f"H={cost_var:.4f}  "
                f"S={entropy:.2f}  "
                f"ε={epsilon:.4f}  "
                f"ESS={ess:.1f}  "
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
        trajectory: (n_steps+1, nq+nv) full MuJoCo state trajectory
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
    traj_qpos[0] = sim.data.qpos.copy()
    traj_qvel[0] = sim.data.qvel.copy()

    for t in range(n_steps):
        sim.step_impedance(scales[t], height_fracs[t], dt, epsilon=epsilon)
        traj_qpos[t + 1] = sim.data.qpos.copy()
        traj_qvel[t + 1] = sim.data.qvel.copy()

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

    return trajectory


def save_result(result: dict, path: str = "rollout_data.npz"):
    """Save rollout data for visualization."""
    save_dict = {
        'final_trajectory': result['final_trajectory'],
        'all_trajectories': np.array(result['trajectories']),
    }
    if 'playback_trajectory' in result:
        save_dict['playback_trajectory'] = result['playback_trajectory']

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
    args = parser.parse_args()

    print(f"Running MPPI re-cycle: {args.n_iters} iterations, "
          f"N={MPPI['N_samples']} samples, seed={args.seed}")
    print(f"Target velocity: {np.array(OCP['target_velocity'])}")
    print()

    result = run_rollout(n_iters=args.n_iters, seed=args.seed)

    # Solve-then-play: use converged φ* for a long open-loop trajectory
    if args.playback > 0:
        sim = MuJoCoQuadruped()
        best_phi = np.array(result['best_phi'])
        # Use the final epsilon from MPPI convergence
        final_epsilon = result['diagnostics']['epsilon'][-1]
        playback_traj = playback_trajectory(
            sim, best_phi, final_epsilon,
            duration=args.playback
        )
        result['playback_trajectory'] = playback_traj
        result['playback_duration'] = args.playback
        # Use playback as the "final" trajectory for visualization
        result['final_trajectory'] = playback_traj

    save_result(result, args.output)

    if not args.no_viz:
        print("\nLaunching visualization server...")
        from visualizer import create_app
        app = create_app(args.output)
        app.run(host='127.0.0.1', port=5001)


if __name__ == '__main__':
    main()
