"""
Three-Body Gravity Damper — 顿开金绳，扯断玉锁

Demonstrates the gravity damper OCP from Appendix J of
"The Knife Is the Mean."

Three bodies interact gravitationally. Without a damper, the system
is unstable: λ₁ → 0 (mass gap closure). With a damper (controlled
fourth body), the spectral gap is maintained via the three-term
control law: gravity + least-action + spectral kick.

Solver modes:
    --solver reactive   Three-term controller (real-time fallback)
    --solver pmp        Full stack: B-spline + MPPI + PMP + analytical gradients

Usage:
    python threebody_damper.py                          # reactive (default)
    python threebody_damper.py --solver pmp --headless  # full stack
    python threebody_damper.py --no-damper              # shows instability

Requirements: numpy, scipy, matplotlib
"""

import argparse
import os
import sys
import numpy as np
from numpy.linalg import eigvalsh, norm
import matplotlib
import matplotlib.pyplot as plt

# Ensure sibling modules are importable regardless of how the script is invoked
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)
_OUTPUT_DIR = os.path.join(_CODE_DIR, 'outputs')
os.makedirs(_OUTPUT_DIR, exist_ok=True)


# ── Physical constants ──────────────────────────────────────
G = 0.5            # gravitational constant (normalised)
M_BODY = 1.0       # mass of each celestial body
M_DAMPER = 0.5     # mass of damper (needs sufficient authority)
EPSILON = 0.02     # spectral gap threshold
U_MAX = 5.0        # box constraint on damper thrust
ALPHA = 0.05       # control cost weight
DT = 0.002         # time step
T_FINAL = 8.0      # simulation duration
N_STEPS = int(T_FINAL / DT)


def gravitational_force(qi, qj, mi, mj):
    """Compute gravitational force on body i due to body j."""
    r = qj - qi
    d = norm(r)
    if d < 0.05:  # softening to avoid singularity
        d = 0.05
    return G * mi * mj / d**2 * r / d


def tidal_weight(qi, qj, mi, mj):
    """Tidal coupling weight: w_ij = G m_i m_j / |q_i - q_j|^3."""
    d = norm(qi - qj)
    if d < 0.05:
        d = 0.05
    return G * mi * mj / d**3


def graph_laplacian(positions, masses):
    """
    Compute the weighted graph Laplacian of the gravitational system.
    Returns L_G (n x n) and its Fiedler eigenvalue λ₁.
    """
    n = len(masses)
    L = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            w = tidal_weight(positions[i], positions[j],
                             masses[i], masses[j])
            L[i, i] += w
            L[j, j] += w
            L[i, j] -= w
            L[j, i] -= w
    evals = eigvalsh(L)
    lambda1 = evals[1]  # Fiedler eigenvalue (second smallest)
    return L, lambda1


def spectral_gradient(positions, masses, damper_idx=3, delta=1e-4):
    """
    Compute ∇_{q_*} λ₁ via finite differences.
    Returns the 3D gradient vector.
    """
    grad = np.zeros(3)
    for k in range(3):
        pos_plus = [p.copy() for p in positions]
        pos_minus = [p.copy() for p in positions]
        pos_plus[damper_idx][k] += delta
        pos_minus[damper_idx][k] -= delta
        _, l1_plus = graph_laplacian(pos_plus, masses)
        _, l1_minus = graph_laplacian(pos_minus, masses)
        grad[k] = (l1_plus - l1_minus) / (2 * delta)
    return grad


def saturate(v, u_max):
    """Componentwise saturation: sat_{u_max}(v)."""
    return np.clip(v, -u_max, u_max)


# ══════════════════════════════════════════════════════════════
# Reactive simulator (existing three-term controller)
# ══════════════════════════════════════════════════════════════

def simulate(use_damper=True, headless=False):
    """
    Run the three-body + gravity damper simulation (reactive controller).

    Returns: dict with time series of positions, λ₁, control effort.
    """
    # ── Initial conditions: perturbed equilateral triangle ──
    r0 = 1.5  # initial separation
    positions = [
        np.array([r0 * np.cos(2 * np.pi * k / 3),
                   r0 * np.sin(2 * np.pi * k / 3),
                   0.0])
        for k in range(3)
    ]
    # Asymmetric perturbation to trigger instability
    positions[0] += np.array([0.3, 0.1, 0.0])
    positions[2] += np.array([-0.1, -0.2, 0.0])

    # Damper at centroid, slightly above plane
    positions.append(np.array([0.0, 0.0, 0.3]))

    velocities = [np.zeros(3) for _ in range(4)]
    # Give bodies tangential velocities (asymmetric)
    for k in range(3):
        theta = 2 * np.pi * k / 3 + np.pi / 2
        v_mag = 0.25 + 0.15 * k  # asymmetric speeds
        velocities[k] = v_mag * np.array([np.cos(theta),
                                           np.sin(theta), 0.0])

    masses = [M_BODY, M_BODY, M_BODY, M_DAMPER]
    n_bodies = 4 if use_damper else 3

    # ── Logging ──
    log = {
        'time': [],
        'lambda1': [],
        'control_norm': [],
        'positions': [],
        'arc_type': [],  # 0=singular, 1=bang, -1=infeasible
        'total_cost': 0.0,
    }

    # ── Main loop ──
    for step in range(N_STEPS):
        t = step * DT

        # Compute graph Laplacian and λ₁
        pos_active = positions[:n_bodies]
        masses_active = masses[:n_bodies]
        _, lambda1 = graph_laplacian(pos_active, masses_active)

        # ── Control law (three-term decomposition) ──
        u = np.zeros(3)
        arc_type = 0  # singular

        if use_damper:
            if lambda1 < EPSILON:
                # Bang arc: saturated spectral gradient kick
                grad = spectral_gradient(positions, masses)
                g_norm = norm(grad)
                if g_norm > 1e-8:
                    u = U_MAX * grad / g_norm
                else:
                    u = np.zeros(3)
                arc_type = 1
            elif lambda1 < 2 * EPSILON:
                # Transition: proportional spectral kick
                grad = spectral_gradient(positions, masses)
                gain = (2 * EPSILON - lambda1) / EPSILON
                u_raw = gain * grad / ALPHA
                u = saturate(u_raw, U_MAX)
                arc_type = 0
            # else: singular arc, u = 0

        # ── Compute gravitational forces ──
        forces = [np.zeros(3) for _ in range(n_bodies)]
        for i in range(n_bodies):
            for j in range(n_bodies):
                if i != j:
                    forces[i] += gravitational_force(
                        positions[i], positions[j],
                        masses[i], masses[j])

        # Add control force to damper
        if use_damper:
            forces[3] += u

        # ── Symplectic Euler integration ──
        for i in range(n_bodies):
            velocities[i] += (forces[i] / masses[i]) * DT
            positions[i] += velocities[i] * DT

        # ── Accumulate cost ──
        log['total_cost'] += (0.5 * ALPHA * np.dot(u, u)) * DT

        # ── Log ──
        log['time'].append(t)
        log['lambda1'].append(lambda1)
        log['control_norm'].append(norm(u))
        log['positions'].append([p.copy() for p in positions])
        log['arc_type'].append(arc_type)

        # Early exit if system has clearly escaped
        max_dist = max(norm(positions[i] - positions[j])
                       for i in range(3) for j in range(i + 1, 3))
        if max_dist > 20.0:
            print(f"System escaped at t={t:.2f}, "
                  f"max_dist={max_dist:.1f}")
            break

    return log


# ══════════════════════════════════════════════════════════════
# PMP simulator (full solver stack)
# ══════════════════════════════════════════════════════════════

def simulate_pmp(headless=False):
    """
    Run the three-body + gravity damper simulation using the full
    solver stack: PMP + MPPI + B-spline + analytical spectral gradients.

    The PMP solver plans over a receding horizon, while MPPI handles
    contact mode selection.  The analytical spectral gradient replaces
    finite differences.

    Returns: dict with time series (same format as simulate()).
    """
    from pmp_solver import PontryaginSolver
    from mppi_sampler import MPPISampler
    from spectral_analytical import spectral_gradient_analytical
    from bspline_trajectory import BSplineTrajectory

    # ── Initial conditions (same as reactive) ──
    r0 = 1.5
    positions = [
        np.array([r0 * np.cos(2 * np.pi * k / 3),
                   r0 * np.sin(2 * np.pi * k / 3),
                   0.0])
        for k in range(3)
    ]
    positions[0] += np.array([0.3, 0.1, 0.0])
    positions[2] += np.array([-0.1, -0.2, 0.0])
    positions.append(np.array([0.0, 0.0, 0.3]))

    velocities = [np.zeros(3) for _ in range(4)]
    for k in range(3):
        theta = 2 * np.pi * k / 3 + np.pi / 2
        v_mag = 0.25 + 0.15 * k
        velocities[k] = v_mag * np.array([np.cos(theta),
                                           np.sin(theta), 0.0])

    masses = [M_BODY, M_BODY, M_BODY, M_DAMPER]

    # ── Solvers ──
    pmp = PontryaginSolver(
        masses, G=G, alpha=ALPHA, epsilon=EPSILON,
        u_max=U_MAX, dt=DT)

    # MPPI dynamics wrapper
    def mppi_dynamics(state, control, dt):
        x_new = state.copy()
        pos, vel = pmp.pos_vel_from_state(state)
        n = len(masses)
        for i in range(n):
            force = np.zeros(3)
            for j in range(n):
                if i != j:
                    force += gravitational_force(
                        pos[i], pos[j], masses[i], masses[j])
            if i == 3:
                force += control
            vel[i] += (force / masses[i]) * dt
            pos[i] += vel[i] * dt
        return pmp.state_from_pos_vel(pos, vel)

    def mppi_cost(state, control):
        pos, vel = pmp.pos_vel_from_state(state)
        _, l1 = graph_laplacian(pos, masses)
        barrier = 0.0
        if l1 < EPSILON:
            barrier = 100.0 * (EPSILON - l1) / EPSILON
        return 0.5 * ALPHA * np.dot(control, control) + barrier

    mppi = MPPISampler(
        mppi_dynamics, mppi_cost,
        state_dim=24, control_dim=3,
        alpha=ALPHA, u_max=U_MAX, beta=10.0)

    # ── Planning parameters ──
    PLAN_HORIZON = 50     # steps to plan ahead
    REPLAN_EVERY = 25     # re-plan every N steps
    MPPI_K = 32           # number of MPPI samples
    PMP_ITERS = 5         # PMP iterations per plan

    # ── Logging ──
    log = {
        'time': [],
        'lambda1': [],
        'control_norm': [],
        'positions': [],
        'arc_type': [],
        'total_cost': 0.0,
        'pmp_cost_history': [],
        'mppi_cost_history': [],
    }

    # ── Planned control buffer ──
    planned_controls = np.zeros((PLAN_HORIZON, 3))
    plan_step = 0  # index into planned_controls

    # ── Main simulation loop ──
    for step in range(N_STEPS):
        t = step * DT

        # Compute current λ₁
        _, lambda1 = graph_laplacian(positions, masses)

        # ── Re-plan if needed ──
        if step % REPLAN_EVERY == 0:
            x0 = pmp.state_from_pos_vel(positions, velocities)

            # Phase 1: MPPI for rough trajectory / mode selection
            u_mppi, mppi_costs = mppi.solve(
                x0, PLAN_HORIZON, DT, K=MPPI_K,
                noise_std=2.0, n_iters=3, u_init=planned_controls)
            log['mppi_cost_history'].extend(mppi_costs)

            # Phase 2: PMP refinement over the MPPI warm-start
            # Use a shorter PMP horizon for speed
            pmp_horizon = min(PLAN_HORIZON, N_STEPS - step)
            pmp_result = pmp.solve(
                x0, pmp_horizon, max_iter=PMP_ITERS, verbose=False)
            log['pmp_cost_history'].extend(pmp_result['cost_history'])

            # Blend: use PMP controls where λ₁ > ε (smooth arcs),
            # fall back to MPPI near constraint boundary
            planned_controls = np.zeros((PLAN_HORIZON, 3))
            for i in range(min(pmp_horizon, PLAN_HORIZON)):
                if (i < len(pmp_result['lambda1s']) and
                        pmp_result['lambda1s'][i] > 1.5 * EPSILON):
                    planned_controls[i] = pmp_result['controls'][i]
                else:
                    planned_controls[i] = u_mppi[i]
            plan_step = 0

        # ── Apply planned control ──
        if plan_step < len(planned_controls):
            u = planned_controls[plan_step]
            plan_step += 1
        else:
            u = np.zeros(3)

        # ── Safety override: reactive fallback if λ₁ critical ──
        if lambda1 < EPSILON:
            grad = spectral_gradient_analytical(
                positions, masses, damper_idx=3, G=G)
            g_norm = norm(grad)
            if g_norm > 1e-8:
                u = U_MAX * grad / g_norm
            arc_type = 1  # bang
        elif lambda1 < 1.5 * EPSILON:
            grad = spectral_gradient_analytical(
                positions, masses, damper_idx=3, G=G)
            gain = (1.5 * EPSILON - lambda1) / (0.5 * EPSILON)
            u_reactive = saturate(gain * grad / ALPHA, U_MAX)
            # Blend reactive with planned
            u = 0.5 * u + 0.5 * u_reactive
            u = saturate(u, U_MAX)
            arc_type = 0
        else:
            arc_type = 0

        # ── Compute gravitational forces ──
        forces = [np.zeros(3) for _ in range(4)]
        for i in range(4):
            for j in range(4):
                if i != j:
                    forces[i] += gravitational_force(
                        positions[i], positions[j],
                        masses[i], masses[j])
        forces[3] += u

        # ── Symplectic Euler ──
        for i in range(4):
            velocities[i] += (forces[i] / masses[i]) * DT
            positions[i] += velocities[i] * DT

        # ── Accumulate cost ──
        log['total_cost'] += (0.5 * ALPHA * np.dot(u, u)) * DT

        # ── Log ──
        log['time'].append(t)
        log['lambda1'].append(lambda1)
        log['control_norm'].append(norm(u))
        log['positions'].append([p.copy() for p in positions])
        log['arc_type'].append(arc_type)

        # Early exit if system escaped
        max_dist = max(norm(positions[i] - positions[j])
                       for i in range(3) for j in range(i + 1, 3))
        if max_dist > 20.0:
            print(f"System escaped at t={t:.2f}, max_dist={max_dist:.1f}")
            break

    return log


# ══════════════════════════════════════════════════════════════
# Plotting
# ══════════════════════════════════════════════════════════════

def plot_results(log, log_compare=None, compare_label='Without damper'):
    """Plot λ₁ evolution and control effort."""
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # ── λ₁ ──
    ax = axes[0]
    t = log['time']
    l1 = log['lambda1']
    ax.plot(t, l1, 'b-', linewidth=1.5, label='With damper')

    if log_compare is not None:
        t_c = log_compare['time']
        l1_c = log_compare['lambda1']
        ax.plot(t_c, l1_c, 'r--', linewidth=1.5, label=compare_label)

    ax.axhline(y=EPSILON, color='orange', linestyle=':',
               linewidth=1, label=f'ε = {EPSILON}')
    ax.set_ylabel('Fiedler eigenvalue λ₁')
    ax.set_title('Spectral Gap Evolution — '
                 '顿开金绳，扯断玉锁')
    ax.legend()
    ax.set_ylim(bottom=-0.01)

    # Shade bang arcs
    for i in range(len(t) - 1):
        if log['arc_type'][i] == 1:
            ax.axvspan(t[i], t[i] + DT, alpha=0.15, color='red')

    # ── Control effort ──
    ax = axes[1]
    ax.plot(t, log['control_norm'], 'g-', linewidth=1)
    ax.axhline(y=U_MAX, color='red', linestyle=':',
               linewidth=0.8, label=f'ū = {U_MAX}')
    ax.set_ylabel('Control ‖u‖')
    ax.set_xlabel('Time')
    ax.legend()

    plt.tight_layout()
    _out = os.path.join(_OUTPUT_DIR, 'threebody_results.png')
    plt.savefig(_out, dpi=150)
    print(f"Saved {_out}")
    plt.show()


def plot_comparison(log_reactive, log_pmp):
    """Plot reactive vs PMP solver comparison."""
    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

    # ── λ₁ comparison ──
    ax = axes[0]
    ax.plot(log_reactive['time'], log_reactive['lambda1'],
            'b-', linewidth=1.5, label='Reactive', alpha=0.8)
    ax.plot(log_pmp['time'], log_pmp['lambda1'],
            'r-', linewidth=1.5, label='PMP', alpha=0.8)
    ax.axhline(y=EPSILON, color='orange', linestyle=':',
               linewidth=1, label=f'ε = {EPSILON}')
    ax.set_ylabel('λ₁')
    ax.set_title('Reactive vs PMP Solver — '
                 '顿开金绳，扯断玉锁')
    ax.legend()
    ax.set_ylim(bottom=-0.01)

    # ── Control effort comparison ──
    ax = axes[1]
    ax.plot(log_reactive['time'], log_reactive['control_norm'],
            'b-', linewidth=0.8, label='Reactive', alpha=0.6)
    ax.plot(log_pmp['time'], log_pmp['control_norm'],
            'r-', linewidth=0.8, label='PMP', alpha=0.6)
    ax.axhline(y=U_MAX, color='red', linestyle=':',
               linewidth=0.8, label=f'ū = {U_MAX}')
    ax.set_ylabel('‖u‖')
    ax.legend()

    # ── PMP convergence ──
    ax = axes[2]
    if log_pmp.get('pmp_cost_history'):
        ax.plot(log_pmp['pmp_cost_history'], 'o-', markersize=2,
                label='PMP cost')
    if log_pmp.get('mppi_cost_history'):
        ax.plot(log_pmp['mppi_cost_history'], 's-', markersize=2,
                label='MPPI cost', alpha=0.7)
    ax.set_ylabel('Solver cost')
    ax.set_xlabel('Solver iteration')
    ax.legend()

    plt.tight_layout()
    _out = os.path.join(_OUTPUT_DIR, 'threebody_comparison.png')
    plt.savefig(_out, dpi=150)
    print(f"Saved {_out}")
    plt.show()


def plot_trajectories(log, title='Three-Body Trajectories'):
    """Plot 2D trajectories of all bodies."""
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))

    n_bodies = len(log['positions'][0])
    colors = ['#e41a1c', '#377eb8', '#4daf4a', '#ff7f00']
    labels = ['m₁', 'm₂', 'm₃', 'm* (damper)']

    for b in range(n_bodies):
        xs = [log['positions'][step][b][0]
              for step in range(len(log['positions']))]
        ys = [log['positions'][step][b][1]
              for step in range(len(log['positions']))]
        ax.plot(xs, ys, color=colors[b], linewidth=0.8,
                label=labels[b], alpha=0.7)
        # Mark start
        ax.plot(xs[0], ys[0], 'o', color=colors[b], markersize=8)
        # Mark end
        ax.plot(xs[-1], ys[-1], 's', color=colors[b], markersize=6)

    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title(title)
    ax.legend()
    ax.set_aspect('equal')
    plt.tight_layout()
    _out = os.path.join(_OUTPUT_DIR, 'threebody_trajectories.png')
    plt.savefig(_out, dpi=150)
    print(f"Saved {_out}")
    plt.show()


# ══════════════════════════════════════════════════════════════
# Statistics
# ══════════════════════════════════════════════════════════════

def print_stats(log, label=''):
    """Print summary statistics for a simulation run."""
    l1 = np.array(log['lambda1'])
    cn = np.array(log['control_norm'])
    arc = np.array(log['arc_type'])
    total_steps = len(arc)
    bang_steps = np.sum(arc == 1)

    print(f"  {label}")
    print(f"    Final λ₁ = {l1[-1]:.4f} "
          f"({'STABLE' if l1[-1] >= EPSILON else 'UNSTABLE'})")
    print(f"    Min λ₁   = {np.min(l1):.4f}")
    print(f"    λ₁ ≥ ε maintained: "
          f"{'YES' if np.all(l1 >= EPSILON - 1e-6) else 'NO'}")
    print(f"    Total cost J = {log['total_cost']:.4f}")
    print(f"    Mean ‖u‖     = {np.mean(cn):.4f}")
    print(f"    Bang fraction = {100 * bang_steps / total_steps:.1f}%")


# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Three-Body Gravity Damper Simulation')
    parser.add_argument('--headless', action='store_true',
                        help='Run without display')
    parser.add_argument('--no-damper', action='store_true',
                        help='Run without damper (shows instability)')
    parser.add_argument('--solver', choices=['reactive', 'pmp'],
                        default='reactive',
                        help='Solver mode: reactive (default) or pmp')
    args = parser.parse_args()

    if args.headless:
        matplotlib.use('Agg')

    print("=" * 60)
    print("  Three-Body Gravity Damper")
    print("  顿开金绳，扯断玉锁")
    print("=" * 60)

    if args.solver == 'pmp' and not args.no_damper:
        # ── Full stack comparison ──
        print(f"\n[1/3] Running REACTIVE solver...")
        log_reactive = simulate(use_damper=True, headless=args.headless)
        print_stats(log_reactive, 'Reactive')

        print(f"\n[2/3] Running PMP solver (full stack)...")
        log_pmp = simulate_pmp(headless=args.headless)
        print_stats(log_pmp, 'PMP')

        print(f"\n[3/3] Running WITHOUT damper...")
        log_no_damper = simulate(use_damper=False, headless=args.headless)
        l1_nd = log_no_damper['lambda1'][-1]
        print(f"  Final λ₁ = {l1_nd:.4f} "
              f"({'STABLE' if l1_nd >= EPSILON else 'UNSTABLE'})")

        # ── Plots ──
        print("\nPlotting comparison...")
        plot_comparison(log_reactive, log_pmp)
        plot_results(log_pmp, log_no_damper,
                     compare_label='Without damper')
        plot_trajectories(log_pmp, 'PMP Solver Trajectories')
    else:
        # ── Standard reactive mode ──
        print("\n[1/2] Running WITH damper...")
        log_damper = simulate(use_damper=True, headless=args.headless)
        print_stats(log_damper, 'Reactive')

        print("\n[2/2] Running WITHOUT damper...")
        log_no_damper = simulate(use_damper=False, headless=args.headless)
        l1_nd = log_no_damper['lambda1'][-1]
        print(f"  Final λ₁ = {l1_nd:.4f} "
              f"({'STABLE' if l1_nd >= EPSILON else 'UNSTABLE'})")

        print("\nPlotting results...")
        plot_results(log_damper, log_no_damper)
        plot_trajectories(log_damper, 'With Damper')

    print("\nDone.")


if __name__ == '__main__':
    main()
