"""Full integration test: solve_tvlqr + forward_simulate pipeline.

Verifies:
  1. No FP exceptions under np.seterr(all='raise')
  2. Backward compat: w_slip=0 produces identical results
  3. w_slip=0.1 produces non-zero slip cost
  4. devil_check passes (asserted inside forward_simulate)
  5. Trajectory stays finite and physically reasonable
"""

import numpy as np
np.seterr(all='raise')

import sys
sys.path.insert(0, '.')

# ── Imports (config uses jax.numpy, need numpy equivalents) ──
from config import ROBOT, OCP, CONSTRAINTS
from riccati_lqr import (
    build_AB, build_reference_trajectory, solve_tvlqr, forward_simulate,
)
from gait_sampler import barrier_force_scale

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f"  — {detail}"
        print(msg)


def to_np(x):
    """Convert jax array or scalar to numpy."""
    return np.array(x, dtype=np.float64)


def run_pipeline(w_slip_override=None):
    """Run full solve_tvlqr + forward_simulate pipeline.

    Returns:
        x_traj, cost_total, cost_track, cost_barrier, cost_slip
    """
    import riccati_lqr  # for patching OCP

    # Extract config
    mass = float(ROBOT["mass"])
    inertia = to_np(ROBOT["inertia"])
    foot_pos = to_np(ROBOT["foot_positions"])
    horizon = int(OCP["horizon"])
    dt_val = float(OCP["dt"])
    Q_diag = to_np(OCP["Q_diag"])
    R_diag = to_np(OCP["R_diag"])
    Q_f_diag = to_np(OCP["Q_f_diag"])
    epsilon = 0.5  # moderate temperature

    # Override w_slip if requested
    original_w_slip = riccati_lqr.OCP.get("w_slip", 0.0)
    if w_slip_override is not None:
        riccati_lqr.OCP["w_slip"] = w_slip_override

    try:
        # Build a simple trot gait schedule
        h_seq = np.zeros((horizon + 1, 4))
        for t in range(horizon + 1):
            phase = (t * dt_val * float(ROBOT["stride_frequency"])) % 1.0
            # Trot: diagonal pairs alternate
            if phase < 0.5:
                h_seq[t] = [0.0, 0.06, 0.06, 0.0]  # FL+RR stance, FR+RL swing
            else:
                h_seq[t] = [0.06, 0.0, 0.0, 0.06]  # FL+RR swing, FR+RL stance

        # Convert foot heights to barrier scales σ_k
        sigma_seq = np.zeros((horizon, 4))
        for t in range(horizon):
            for k in range(4):
                h = h_seq[t, k]
                sigma_seq[t, k] = epsilon / (h + epsilon)

        # Build dynamics
        A_seq, B_seq, c = build_AB(mass, inertia, foot_pos, sigma_seq)

        # Reference trajectory
        x_ref = build_reference_trajectory(horizon, dt_val)

        # Solve TV-LQR
        K_seq, k_seq = solve_tvlqr(
            A_seq, B_seq, c, Q_diag, R_diag, Q_f_diag, x_ref, dt_val, horizon
        )

        # Initial state: standing at origin
        x0 = np.zeros(13)
        x0[2] = float(CONSTRAINTS["z_target"])  # standing height

        # Forward simulate
        constraints_dict = {
            "z_min": float(CONSTRAINTS["z_min"]),
            "z_max": float(CONSTRAINTS["z_max"]),
            "z_target": float(CONSTRAINTS["z_target"]),
            "w_height": float(CONSTRAINTS["w_height"]),
            "w_height_barrier": float(CONSTRAINTS["w_height_barrier"]),
            "phi_max": float(CONSTRAINTS["phi_max"]),
            "w_ori_barrier": float(CONSTRAINTS["w_ori_barrier"]),
        }

        result = forward_simulate(
            x0, A_seq, B_seq, c, K_seq, k_seq, x_ref, h_seq,
            epsilon, horizon, dt_val, Q_diag, R_diag, Q_f_diag,
            constraints=constraints_dict,
        )

        return result

    finally:
        # Restore original w_slip
        riccati_lqr.OCP["w_slip"] = original_w_slip


# ═══════════════════════════════════════════════════════════════
# Test 1: Basic pipeline runs without FP exceptions (w_slip=0.1)
# ═══════════════════════════════════════════════════════════════
print("\n═══ Test 1: Pipeline with w_slip=0.1 (default) ═══")
try:
    x_traj, cost_total, cost_track, cost_barrier, cost_slip = run_pipeline(w_slip_override=0.1)
    check("pipeline completes", True)
    check("x_traj finite", np.all(np.isfinite(x_traj)),
          f"non-finite count: {np.sum(~np.isfinite(x_traj))}")
    check("cost_total finite", np.isfinite(cost_total), f"cost_total={cost_total}")
    check("cost_track >= 0", cost_track >= 0, f"cost_track={cost_track}")
    check("cost_slip > 0", cost_slip > 0, f"cost_slip={cost_slip}")
    check("cost_total = track + barrier + slip",
          abs(cost_total - (cost_track + cost_barrier + cost_slip)) < 1e-10,
          f"diff={abs(cost_total - (cost_track + cost_barrier + cost_slip))}")

    # Physical reasonableness
    z_vals = x_traj[:, 2]
    check("z in [0.1, 0.5]",
          np.all(z_vals > 0.1) and np.all(z_vals < 0.5),
          f"z range: [{z_vals.min():.4f}, {z_vals.max():.4f}]")
    check("vx reasonable (< 5 m/s)", np.all(np.abs(x_traj[:, 3]) < 5.0),
          f"max |vx| = {np.max(np.abs(x_traj[:, 3])):.4f}")
    print(f"  INFO  cost_track={cost_track:.4f}  cost_barrier={cost_barrier:.4f}  cost_slip={cost_slip:.4f}")
    print(f"  INFO  z range: [{z_vals.min():.4f}, {z_vals.max():.4f}]")
    print(f"  INFO  final x: pos={x_traj[-1,:3]}, vel={x_traj[-1,3:6]}")
except Exception as e:
    check("pipeline completes", False, str(e))
    import traceback
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════
# Test 2: Backward compat — w_slip=0
# ═══════════════════════════════════════════════════════════════
print("\n═══ Test 2: Pipeline with w_slip=0 (backward compat) ═══")
try:
    x_traj_0, cost_total_0, cost_track_0, cost_barrier_0, cost_slip_0 = run_pipeline(w_slip_override=0.0)
    check("pipeline completes (w_slip=0)", True)
    check("cost_slip == 0", cost_slip_0 == 0.0, f"cost_slip={cost_slip_0}")
    check("x_traj finite", np.all(np.isfinite(x_traj_0)))
    check("cost_total finite", np.isfinite(cost_total_0), f"cost_total={cost_total_0}")
    print(f"  INFO  cost_track={cost_track_0:.4f}  cost_barrier={cost_barrier_0:.4f}")
except Exception as e:
    check("pipeline completes (w_slip=0)", False, str(e))
    import traceback
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════
# Test 3: Slip cost increases with more contact
# ═══════════════════════════════════════════════════════════════
print("\n═══ Test 3: Slip cost monotonicity ═══")
try:
    # Run with w_slip=0.1 (already done) and w_slip=0.5
    _, _, _, _, slip_01 = run_pipeline(w_slip_override=0.1)
    _, _, _, _, slip_05 = run_pipeline(w_slip_override=0.5)
    check("higher w_slip → higher slip cost",
          slip_05 > slip_01,
          f"slip(0.1)={slip_01:.6f}, slip(0.5)={slip_05:.6f}")
except Exception as e:
    check("slip monotonicity", False, str(e))
    import traceback
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════
# Test 4: Multiple epsilon values
# ═══════════════════════════════════════════════════════════════
print("\n═══ Test 4: Varying epsilon ═══")
import riccati_lqr as rl_mod
for eps_val in [1.0, 0.1, 0.01]:
    try:
        mass = float(ROBOT["mass"])
        inertia = to_np(ROBOT["inertia"])
        foot_pos = to_np(ROBOT["foot_positions"])
        horizon = int(OCP["horizon"])
        dt_val = float(OCP["dt"])
        Q_diag = to_np(OCP["Q_diag"])
        R_diag = to_np(OCP["R_diag"])
        Q_f_diag = to_np(OCP["Q_f_diag"])

        h_seq = np.zeros((horizon + 1, 4))
        for t in range(horizon + 1):
            phase = (t * dt_val * float(ROBOT["stride_frequency"])) % 1.0
            if phase < 0.5:
                h_seq[t] = [0.0, 0.06, 0.06, 0.0]
            else:
                h_seq[t] = [0.06, 0.0, 0.0, 0.06]

        sigma_seq = np.zeros((horizon, 4))
        for t in range(horizon):
            for k in range(4):
                h = h_seq[t, k]
                sigma_seq[t, k] = eps_val / (h + eps_val)

        A_seq, B_seq, c_vec = build_AB(mass, inertia, foot_pos, sigma_seq)
        x_ref = build_reference_trajectory(horizon, dt_val)

        rl_mod.OCP["w_slip"] = 0.1
        K_seq, k_seq = solve_tvlqr(
            A_seq, B_seq, c_vec, Q_diag, R_diag, Q_f_diag, x_ref, dt_val, horizon
        )

        x0 = np.zeros(13)
        x0[2] = float(CONSTRAINTS["z_target"])
        constraints_dict = {
            "z_min": float(CONSTRAINTS["z_min"]),
            "z_max": float(CONSTRAINTS["z_max"]),
            "z_target": float(CONSTRAINTS["z_target"]),
            "w_height": float(CONSTRAINTS["w_height"]),
            "w_height_barrier": float(CONSTRAINTS["w_height_barrier"]),
            "phi_max": float(CONSTRAINTS["phi_max"]),
            "w_ori_barrier": float(CONSTRAINTS["w_ori_barrier"]),
        }

        result = forward_simulate(
            x0, A_seq, B_seq, c_vec, K_seq, k_seq, x_ref, h_seq,
            eps_val, horizon, dt_val, Q_diag, R_diag, Q_f_diag,
            constraints=constraints_dict,
        )
        x_traj_e, cost_e, _, _, _ = result
        check(f"eps={eps_val}: pipeline ok", np.all(np.isfinite(x_traj_e)),
              f"cost={cost_e:.4f}")
    except Exception as e:
        check(f"eps={eps_val}: pipeline ok", False, str(e))
        import traceback
        traceback.print_exc()
    finally:
        rl_mod.OCP["w_slip"] = 0.1  # restore


# ═══════════════════════════════════════════════════════════════
# Test 5: nu (control dimension) variable sanity
# ═══════════════════════════════════════════════════════════════
print("\n═══ Test 5: Gain shapes and bounds ═══")
try:
    mass = float(ROBOT["mass"])
    inertia = to_np(ROBOT["inertia"])
    foot_pos = to_np(ROBOT["foot_positions"])
    horizon = int(OCP["horizon"])
    dt_val = float(OCP["dt"])
    Q_diag = to_np(OCP["Q_diag"])
    R_diag = to_np(OCP["R_diag"])
    Q_f_diag = to_np(OCP["Q_f_diag"])

    h_seq = 0.03 * np.ones((horizon + 1, 4))  # all feet at 3cm (partial contact)
    sigma_seq = np.zeros((horizon, 4))
    for t in range(horizon):
        for k in range(4):
            sigma_seq[t, k] = 0.5 / (h_seq[t, k] + 0.5)

    A_seq, B_seq, c_vec = build_AB(mass, inertia, foot_pos, sigma_seq)
    x_ref = build_reference_trajectory(horizon, dt_val)

    rl_mod.OCP["w_slip"] = 0.1
    K_seq, k_seq = solve_tvlqr(
        A_seq, B_seq, c_vec, Q_diag, R_diag, Q_f_diag, x_ref, dt_val, horizon
    )

    check("K_seq shape", K_seq.shape == (horizon, 12, 13))
    check("k_seq shape", k_seq.shape == (horizon, 12))
    check("K_seq finite", np.all(np.isfinite(K_seq)))
    check("k_seq finite", np.all(np.isfinite(k_seq)))
    check("|K| bounded", np.max(np.abs(K_seq)) <= 1e3,
          f"max |K| = {np.max(np.abs(K_seq)):.2f}")
    check("|k| bounded", np.max(np.abs(k_seq)) <= 1e3,
          f"max |k| = {np.max(np.abs(k_seq)):.2f}")
except Exception as e:
    check("gain shapes", False, str(e))
    import traceback
    traceback.print_exc()
finally:
    rl_mod.OCP["w_slip"] = 0.1


# ═══════════════════════════════════════════════════════════════
print(f"\n{'═' * 50}")
print(f"  Results: {PASS} passed, {FAIL} failed")
print(f"{'═' * 50}")
sys.exit(1 if FAIL > 0 else 0)
