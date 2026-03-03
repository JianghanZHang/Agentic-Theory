"""
Three-Body Gravity Damper — ρ formulation (GRJL 2.0)

Everything is a smooth function of ρ = F_repulsion / F_attraction.
No discrete contact modes.  The order parameter governs edge weights,
the control law, and the Laplacian — continuously.

Solver modes:
    --solver reactive   Three-term controller using ρ threshold
    --solver pmp        Full stack: PMP + MPPI + ρ-weighted Laplacian

Usage:
    python threebody_rho.py                              # reactive (default)
    python threebody_rho.py --solver pmp --headless       # full stack
    python threebody_rho.py --no-damper                   # instability baseline

Requirements: numpy, scipy, matplotlib
"""

import argparse
import os
import sys
import numpy as np
from numpy.linalg import eigvalsh, eigh, norm
import matplotlib
import matplotlib.pyplot as plt

# Ensure sibling modules are importable
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)
_OUTPUT_DIR = os.path.join(_CODE_DIR, 'outputs')
os.makedirs(_OUTPUT_DIR, exist_ok=True)

from order_parameter import (compute_rho, smooth_edge_weight,
                              d_smooth_edge_weight_d_rho,
                              build_laplacian_from_rho, tidal_rho)


# ── Physical constants ──────────────────────────────────────
G = 0.5            # gravitational constant (normalised)
M_BODY = 1.0       # mass of each celestial body
M_DAMPER = 0.5     # mass of damper
EPSILON = 0.02     # spectral gap threshold
U_MAX = 5.0        # box constraint on damper thrust
ALPHA = 0.05       # control cost weight
DT = 0.002         # time step
T_FINAL = 8.0      # simulation duration
N_STEPS = int(T_FINAL / DT)

# Weight parameters
K_N = 1.0
K_T = 1.0
MU_FRICTION = 0.5
BETA_SIGMOID = 20.0


# ── Physics ────────────────────────────────────────────────

def gravitational_force(qi, qj, mi, mj, softening=0.05):
    """Gravitational force on body i due to body j."""
    r = qj - qi
    d = max(norm(r), softening)
    return G * mi * mj / d**2 * r / d


def graph_laplacian_tidal(positions, masses):
    """Tidal-weight graph Laplacian (1.0 style, for baseline)."""
    n = len(masses)
    L = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = max(norm(positions[i] - positions[j]), 0.05)
            w = G * masses[i] * masses[j] / d**3
            L[i, i] += w
            L[j, j] += w
            L[i, j] -= w
            L[j, i] -= w
    evals = eigvalsh(L)
    return L, evals[1]


def compute_rho_pairs(positions, masses, damper_idx=3):
    """Compute pairwise ρ between damper and each body."""
    rho_pairs = {}
    for j in range(len(masses)):
        if j == damper_idx:
            continue
        i_pair = min(damper_idx, j)
        j_pair = max(damper_idx, j)
        rho_pairs[(i_pair, j_pair)] = tidal_rho(
            positions, masses, damper_idx, j, G, softening=0.05)
    return rho_pairs


def rho_weighted_lambda1(positions, masses, damper_idx=3):
    """Compute λ₁ from ρ-weighted Laplacian."""
    rho_pairs = compute_rho_pairs(positions, masses, damper_idx)
    _, lambda1, weights = build_laplacian_from_rho(
        rho_pairs, len(masses), K_N, K_T, MU_FRICTION, BETA_SIGMOID)
    return lambda1, rho_pairs, weights


def spectral_gradient_rho(positions, masses, damper_idx=3, delta=1e-4):
    """Finite-diff gradient of ρ-weighted λ₁ w.r.t. damper position."""
    grad = np.zeros(3)
    for k in range(3):
        pos_plus = [p.copy() for p in positions]
        pos_minus = [p.copy() for p in positions]
        pos_plus[damper_idx][k] += delta
        pos_minus[damper_idx][k] -= delta

        l1_plus, _, _ = rho_weighted_lambda1(pos_plus, masses, damper_idx)
        l1_minus, _, _ = rho_weighted_lambda1(pos_minus, masses, damper_idx)
        grad[k] = (l1_plus - l1_minus) / (2 * delta)
    return grad


def saturate(v, u_max):
    """Componentwise saturation."""
    return np.clip(v, -u_max, u_max)


# ── Initial conditions ─────────────────────────────────────

def make_initial_conditions():
    """Create initial positions and velocities (same as 1.0 for comparison)."""
    r0 = 1.5
    positions = [
        np.array([r0 * np.cos(2 * np.pi * k / 3),
                   r0 * np.sin(2 * np.pi * k / 3), 0.0])
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
    return positions, velocities


# ══════════════════════════════════════════════════════════════
# Reactive simulator — ρ-based control
# ══════════════════════════════════════════════════════════════

def simulate_reactive(use_damper=True, headless=False):
    """Three-body simulation with ρ-based reactive control.

    Control law: when ρ_min < 1 for any damper-body pair, the damper
    is losing tidal authority → spectral kick.  Otherwise coast.
    """
    positions, velocities = make_initial_conditions()
    masses = [M_BODY, M_BODY, M_BODY, M_DAMPER]
    n_bodies = 4 if use_damper else 3

    log = {
        'time': [],
        'lambda1': [],
        'control_norm': [],
        'positions': [],
        'arc_type': [],
        'total_cost': 0.0,
        'rho_min': [],
        'rho_max': [],
        'edge_weights': [],
    }

    for step in range(N_STEPS):
        t = step * DT

        # ── Compute ρ and λ₁ ──
        if use_damper:
            lambda1, rho_pairs, weights = rho_weighted_lambda1(
                positions, masses)
            rho_values = list(rho_pairs.values())
            rho_min = min(rho_values) if rho_values else 0.0
            rho_max = max(rho_values) if rho_values else 0.0
        else:
            _, lambda1 = graph_laplacian_tidal(
                positions[:n_bodies], masses[:n_bodies])
            rho_min = rho_max = 0.0
            weights = {}

        # ── ρ-based control law ──
        u = np.zeros(3)
        arc_type = 0  # singular

        if use_damper:
            # Phase transition: ρ_min crossing 1.0 is the control trigger
            if rho_min < 0.5:
                # Deep in separating regime: full bang
                grad = spectral_gradient_rho(positions, masses)
                g_norm = norm(grad)
                if g_norm > 1e-8:
                    u = U_MAX * grad / g_norm
                arc_type = 1  # bang
            elif rho_min < 1.0:
                # Approaching phase transition: proportional kick
                grad = spectral_gradient_rho(positions, masses)
                gain = (1.0 - rho_min) / 0.5  # linear ramp
                u_raw = gain * grad / ALPHA
                u = saturate(u_raw, U_MAX)
                arc_type = 0
            # else: ρ_min ≥ 1 → sticking regime, coast

        # ── Gravitational forces ──
        forces = [np.zeros(3) for _ in range(n_bodies)]
        for i in range(n_bodies):
            for j in range(n_bodies):
                if i != j:
                    forces[i] += gravitational_force(
                        positions[i], positions[j],
                        masses[i], masses[j])

        if use_damper:
            forces[3] += u

        # ── Symplectic Euler ──
        for i in range(n_bodies):
            velocities[i] += (forces[i] / masses[i]) * DT
            positions[i] += velocities[i] * DT

        # ── Log ──
        log['total_cost'] += (0.5 * ALPHA * np.dot(u, u)) * DT
        log['time'].append(t)
        log['lambda1'].append(lambda1)
        log['control_norm'].append(norm(u))
        log['positions'].append([p.copy() for p in positions])
        log['arc_type'].append(arc_type)
        log['rho_min'].append(rho_min)
        log['rho_max'].append(rho_max)
        log['edge_weights'].append(dict(weights))

        # Early exit if escaped
        max_dist = max(norm(positions[i] - positions[j])
                       for i in range(3) for j in range(i + 1, 3))
        if max_dist > 20.0:
            print(f"System escaped at t={t:.2f}, max_dist={max_dist:.1f}")
            break

    return log


# ══════════════════════════════════════════════════════════════
# PMP simulator — ρ-weighted Laplacian
# ══════════════════════════════════════════════════════════════

def simulate_pmp(headless=False):
    """Three-body simulation using PMP + MPPI with ρ-weighted Laplacian."""
    from pmp_rho_solver import PmpRhoSolver
    from rho_sampler import RhoMPPISampler, make_gravity_rho_fn, make_gravity_cost_fn

    positions, velocities = make_initial_conditions()
    masses = [M_BODY, M_BODY, M_BODY, M_DAMPER]

    # ── Solvers ──
    pmp = PmpRhoSolver(
        masses, G=G, alpha=ALPHA, epsilon=EPSILON,
        u_max=U_MAX, dt=DT,
        k_n=K_N, k_t=K_T, mu_friction=MU_FRICTION,
        beta_sigmoid=BETA_SIGMOID)

    # MPPI dynamics wrapper
    def mppi_dynamics(state, control, dt):
        pos = [state[3*i:3*i+3].copy() for i in range(4)]
        vel = [state[12 + 3*i:12 + 3*i+3].copy() for i in range(4)]
        for i in range(4):
            force = np.zeros(3)
            for j in range(4):
                if i != j:
                    force += gravitational_force(
                        pos[i], pos[j], masses[i], masses[j])
            if i == 3:
                force += control
            vel[i] += (force / masses[i]) * dt
            pos[i] += vel[i] * dt
        return pmp.state_from_pos_vel(pos, vel)

    rho_fn = make_gravity_rho_fn(masses, damper_idx=3, G=G)
    cost_fn = make_gravity_cost_fn(masses, alpha=ALPHA, epsilon=EPSILON, G=G)

    mppi = RhoMPPISampler(
        mppi_dynamics, cost_fn, rho_fn,
        state_dim=24, control_dim=3,
        alpha=ALPHA, u_max=U_MAX, gamma=5.0, delta_rho=0.1)

    # ── Planning parameters ──
    PLAN_HORIZON = 50
    REPLAN_EVERY = 25
    MPPI_K = 32
    PMP_ITERS = 5

    log = {
        'time': [],
        'lambda1': [],
        'control_norm': [],
        'positions': [],
        'arc_type': [],
        'total_cost': 0.0,
        'rho_min': [],
        'rho_max': [],
        'edge_weights': [],
        'pmp_cost_history': [],
        'mppi_cost_history': [],
    }

    planned_controls = np.zeros((PLAN_HORIZON, 3))
    plan_step = 0

    for step in range(N_STEPS):
        t = step * DT

        # ── Compute ρ and λ₁ ──
        lambda1, rho_pairs, weights = rho_weighted_lambda1(
            positions, masses)
        rho_values = list(rho_pairs.values())
        rho_min = min(rho_values) if rho_values else 0.0
        rho_max = max(rho_values) if rho_values else 0.0

        # ── Re-plan ──
        if step % REPLAN_EVERY == 0:
            x0 = pmp.state_from_pos_vel(positions, velocities)

            # MPPI warm start
            u_mppi, mppi_costs, _ = mppi.solve(
                x0, PLAN_HORIZON, DT, K=MPPI_K,
                noise_std=2.0, n_iters=3, u_init=planned_controls)
            log['mppi_cost_history'].extend(mppi_costs)

            # PMP refinement
            pmp_horizon = min(PLAN_HORIZON, N_STEPS - step)
            pmp_result = pmp.solve(
                x0, pmp_horizon, max_iter=PMP_ITERS, verbose=False)
            log['pmp_cost_history'].extend(pmp_result['cost_history'])

            # Blend: PMP where ρ > 1 (sticking), MPPI near transition
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

        # ── Safety override: ρ-based reactive fallback ──
        if rho_min < 0.5:
            grad = spectral_gradient_rho(positions, masses)
            g_norm = norm(grad)
            if g_norm > 1e-8:
                u = U_MAX * grad / g_norm
            arc_type = 1
        elif rho_min < 1.0:
            grad = spectral_gradient_rho(positions, masses)
            gain = (1.0 - rho_min) / 0.5
            u_reactive = saturate(gain * grad / ALPHA, U_MAX)
            u = 0.5 * u + 0.5 * u_reactive
            u = saturate(u, U_MAX)
            arc_type = 0
        else:
            arc_type = 0

        # ── Gravitational forces ──
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

        # ── Log ──
        log['total_cost'] += (0.5 * ALPHA * np.dot(u, u)) * DT
        log['time'].append(t)
        log['lambda1'].append(lambda1)
        log['control_norm'].append(norm(u))
        log['positions'].append([p.copy() for p in positions])
        log['arc_type'].append(arc_type)
        log['rho_min'].append(rho_min)
        log['rho_max'].append(rho_max)
        log['edge_weights'].append(dict(weights))

        max_dist = max(norm(positions[i] - positions[j])
                       for i in range(3) for j in range(i + 1, 3))
        if max_dist > 20.0:
            print(f"System escaped at t={t:.2f}, max_dist={max_dist:.1f}")
            break

    return log


# ══════════════════════════════════════════════════════════════
# Plotting
# ══════════════════════════════════════════════════════════════

def plot_rho_results(log, title_suffix=''):
    """3-panel plot: λ₁, ρ, and control effort."""
    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    t = log['time']

    # ── λ₁ ──
    ax = axes[0]
    ax.plot(t, log['lambda1'], 'b-', linewidth=1.5)
    ax.axhline(y=EPSILON, color='orange', linestyle=':',
               linewidth=1, label=f'ε = {EPSILON}')
    ax.set_ylabel('Fiedler eigenvalue λ₁')
    ax.set_title(f'ρ-Formulation Results{title_suffix}')
    ax.legend()
    ax.set_ylim(bottom=-0.01)
    for i in range(len(t) - 1):
        if log['arc_type'][i] == 1:
            ax.axvspan(t[i], t[i] + DT, alpha=0.15, color='red')

    # ── ρ ──
    ax = axes[1]
    ax.plot(t, log['rho_min'], 'r-', linewidth=1, label='ρ_min')
    ax.plot(t, log['rho_max'], 'b-', linewidth=1, alpha=0.5, label='ρ_max')
    ax.axhline(y=1.0, color='black', linestyle='--',
               linewidth=1, label='ρ = 1 (phase transition)')
    ax.set_ylabel('Order parameter ρ')
    ax.legend()
    ax.set_ylim(bottom=-0.1)

    # ── Control ──
    ax = axes[2]
    ax.plot(t, log['control_norm'], 'g-', linewidth=1)
    ax.axhline(y=U_MAX, color='red', linestyle=':',
               linewidth=0.8, label=f'ū = {U_MAX}')
    ax.set_ylabel('Control ‖u‖')
    ax.set_xlabel('Time')
    ax.legend()

    plt.tight_layout()
    _out = os.path.join(_OUTPUT_DIR, 'threebody_rho_results.png')
    plt.savefig(_out, dpi=150)
    print(f"Saved {_out}")
    plt.show()


def plot_phase_portrait(log, title_suffix=''):
    """Phase portrait: ρ_min vs λ₁."""
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    ax.scatter(log['rho_min'], log['lambda1'],
               c=log['time'], cmap='viridis', s=1, alpha=0.5)
    ax.axvline(x=1.0, color='black', linestyle='--',
               linewidth=1, label='ρ = 1')
    ax.axhline(y=EPSILON, color='orange', linestyle=':',
               linewidth=1, label=f'ε = {EPSILON}')
    ax.set_xlabel('ρ_min')
    ax.set_ylabel('λ₁')
    ax.set_title(f'Phase Portrait{title_suffix}')
    ax.legend()
    cbar = plt.colorbar(ax.collections[0], ax=ax)
    cbar.set_label('Time')
    plt.tight_layout()
    _out = os.path.join(_OUTPUT_DIR, 'threebody_rho_phase.png')
    plt.savefig(_out, dpi=150)
    print(f"Saved {_out}")
    plt.show()


# ══════════════════════════════════════════════════════════════
# Statistics
# ══════════════════════════════════════════════════════════════

def print_stats(log, label=''):
    """Print summary statistics."""
    l1 = np.array(log['lambda1'])
    cn = np.array(log['control_norm'])
    arc = np.array(log['arc_type'])
    total_steps = len(arc)
    bang_steps = np.sum(arc == 1)

    rho_min_arr = np.array(log.get('rho_min', [0.0]))
    rho_max_arr = np.array(log.get('rho_max', [0.0]))

    print(f"  {label}")
    print(f"    Final λ₁ = {l1[-1]:.4f} "
          f"({'STABLE' if l1[-1] >= EPSILON else 'UNSTABLE'})")
    print(f"    Min λ₁   = {np.min(l1):.4f}")
    print(f"    λ₁ ≥ ε maintained: "
          f"{'YES' if np.all(l1 >= EPSILON - 1e-6) else 'NO'}")
    print(f"    Total cost J = {log['total_cost']:.4f}")
    print(f"    Mean ‖u‖     = {np.mean(cn):.4f}")
    print(f"    Bang fraction = {100 * bang_steps / total_steps:.1f}%")
    if len(rho_min_arr) > 0:
        crossings = np.sum(np.diff(np.sign(rho_min_arr - 1.0)) != 0)
        print(f"    ρ phase crossings = {crossings}")
        print(f"    ρ_min range = [{np.min(rho_min_arr):.3f}, "
              f"{np.max(rho_min_arr):.3f}]")


# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Three-Body Gravity Damper (ρ formulation)')
    parser.add_argument('--headless', action='store_true',
                        help='Run without display')
    parser.add_argument('--no-damper', action='store_true',
                        help='Run without damper')
    parser.add_argument('--solver', choices=['reactive', 'pmp'],
                        default='reactive',
                        help='Solver mode')
    args = parser.parse_args()

    if args.headless:
        matplotlib.use('Agg')

    print("=" * 60)
    print("  Three-Body Gravity Damper — ρ formulation (2.0)")
    print("  顿开金绳，扯断玉锁")
    print("=" * 60)

    if args.solver == 'pmp' and not args.no_damper:
        print(f"\n[1/3] Running REACTIVE (ρ-based)...")
        log_reactive = simulate_reactive(
            use_damper=True, headless=args.headless)
        print_stats(log_reactive, 'Reactive (ρ)')

        print(f"\n[2/3] Running PMP (ρ-weighted Laplacian)...")
        log_pmp = simulate_pmp(headless=args.headless)
        print_stats(log_pmp, 'PMP (ρ)')

        print(f"\n[3/3] Running WITHOUT damper...")
        log_no_damper = simulate_reactive(
            use_damper=False, headless=args.headless)
        l1_nd = log_no_damper['lambda1'][-1]
        print(f"  Final λ₁ = {l1_nd:.4f} "
              f"({'STABLE' if l1_nd >= EPSILON else 'UNSTABLE'})")

        if not args.headless:
            plot_rho_results(log_pmp, ' — PMP')
            plot_phase_portrait(log_pmp, ' — PMP')
    else:
        print("\n[1/2] Running WITH damper (ρ-based)...")
        log_damper = simulate_reactive(
            use_damper=True, headless=args.headless)
        print_stats(log_damper, 'Reactive (ρ)')

        print("\n[2/2] Running WITHOUT damper...")
        log_no_damper = simulate_reactive(
            use_damper=False, headless=args.headless)
        l1_nd = log_no_damper['lambda1'][-1]
        print(f"  Final λ₁ = {l1_nd:.4f} "
              f"({'STABLE' if l1_nd >= EPSILON else 'UNSTABLE'})")

        if not args.headless:
            plot_rho_results(log_damper, ' — Reactive')
            plot_phase_portrait(log_damper, ' — Reactive')

    print("\nDone.")


if __name__ == '__main__':
    main()
