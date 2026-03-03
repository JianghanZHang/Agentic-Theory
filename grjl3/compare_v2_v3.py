"""
Compare GRJL 2.0 vs 3.0 — Head-to-head.

Backend 1 (three-body):
    2.0: tidal_rho + ad-hoc thresholding
    3.0: kinematic_rho + SpectralPID

Key new panels: PID term decomposition, kinematic ρ vs tidal ρ.

Usage:
    python compare_v2_v3.py              # with plots
    python compare_v2_v3.py --headless   # stats only
"""

import argparse
import os
import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_CODE_DIR)
for p in [_CODE_DIR, _PARENT, os.path.join(_PARENT, 'grjl2'),
          os.path.join(_PARENT, 'grjl3')]:
    if p not in sys.path:
        sys.path.insert(0, p)
_OUTPUT_DIR = os.path.join(_CODE_DIR, 'outputs')
os.makedirs(_OUTPUT_DIR, exist_ok=True)


def run_comparison(headless=False):
    """Run both 2.0 and 3.0, collect logs, compare."""

    # ── Import both versions ──
    from grjl2.threebody_rho import simulate_reactive as sim_v2
    from grjl3.threebody_kinematic import simulate_reactive as sim_v3

    print("=" * 60)
    print("  GRJL 2.0 vs 3.0 — Head-to-Head Comparison")
    print("  顿开金绳，扯断玉锁")
    print("=" * 60)

    # ── Run 2.0 ──
    print("\n[1/3] Running GRJL 2.0 (tidal ρ + threshold)...")
    log_v2 = sim_v2(use_damper=True, headless=True)

    # ── Run 3.0 ──
    print("[2/3] Running GRJL 3.0 (kinematic ρ + PID)...")
    log_v3 = sim_v3(use_damper=True, headless=True)

    # ── Run no-damper baseline ──
    print("[3/3] Running baseline (no damper)...")
    log_nd = sim_v2(use_damper=False, headless=True)

    # ── Statistics ──
    def stats(log, label):
        l1 = np.array(log['lambda1'])
        cn = np.array(log['control_norm'])
        arc = np.array(log['arc_type'])
        rho_min = np.array(log.get('rho_min', [0]))
        bang = np.sum(arc == 1) / len(arc)
        crossings = np.sum(np.diff(np.sign(rho_min - 1.0)) != 0)
        print(f"\n  {label}:")
        print(f"    Final λ₁     = {l1[-1]:.4f}")
        print(f"    Min λ₁       = {np.min(l1):.4f}")
        print(f"    Cost J       = {log['total_cost']:.4f}")
        print(f"    Mean ‖u‖     = {np.mean(cn):.4f}")
        print(f"    Bang %       = {100*bang:.1f}%")
        print(f"    ρ crossings  = {crossings}")
        return l1[-1], log['total_cost'], bang, crossings

    final_v2, cost_v2, bang_v2, cross_v2 = stats(log_v2, "GRJL 2.0")
    final_v3, cost_v3, bang_v3, cross_v3 = stats(log_v3, "GRJL 3.0")

    l1_nd = np.array(log_nd['lambda1'])
    print(f"\n  No damper: final λ₁ = {l1_nd[-1]:.4f}")

    # ── Comparison table ──
    print("\n" + "=" * 60)
    print("  Comparison")
    print("=" * 60)
    print(f"  {'Metric':<20} {'2.0':>10} {'3.0':>10} {'Δ':>10}")
    print(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*10}")
    print(f"  {'Final λ₁':<20} {final_v2:>10.4f} {final_v3:>10.4f} "
          f"{final_v3-final_v2:>+10.4f}")
    print(f"  {'Cost J':<20} {cost_v2:>10.4f} {cost_v3:>10.4f} "
          f"{cost_v3-cost_v2:>+10.4f}")
    print(f"  {'Bang %':<20} {100*bang_v2:>9.1f}% {100*bang_v3:>9.1f}% "
          f"{100*(bang_v3-bang_v2):>+9.1f}%")
    print(f"  {'ρ crossings':<20} {cross_v2:>10d} {cross_v3:>10d} "
          f"{cross_v3-cross_v2:>+10d}")

    # ── V3.6 check ──
    cost_ratio = cost_v3 / max(cost_v2, 1e-12)
    v36 = "PASS" if cost_ratio < 2.0 else "FAIL"
    print(f"\n  V3.6 (cost within 2×): {v36} "
          f"(ratio = {cost_ratio:.2f})")

    return log_v2, log_v3, log_nd


def plot_comparison(log_v2, log_v3, log_nd):
    """5-panel comparison plot."""
    fig, axes = plt.subplots(5, 1, figsize=(12, 16), sharex=True)

    t2 = log_v2['time']
    t3 = log_v3['time']
    tnd = log_nd['time']

    # Panel 1: λ₁
    ax = axes[0]
    ax.plot(tnd, log_nd['lambda1'], 'gray', linewidth=0.8,
            alpha=0.5, label='No damper')
    ax.plot(t2, log_v2['lambda1'], 'b-', linewidth=1, label='2.0 (tidal ρ)')
    ax.plot(t3, log_v3['lambda1'], 'r-', linewidth=1,
            alpha=0.7, label='3.0 (kinematic ρ + PID)')
    ax.axhline(y=0.02, color='orange', linestyle=':', linewidth=0.8,
               label='ε = 0.02')
    ax.set_ylabel('λ₁')
    ax.set_title('GRJL 2.0 vs 3.0 — Three-Body Comparison')
    ax.legend(fontsize=8)

    # Panel 2: Control norm
    ax = axes[1]
    ax.plot(t2, log_v2['control_norm'], 'b-', linewidth=0.8,
            alpha=0.7, label='2.0')
    ax.plot(t3, log_v3['control_norm'], 'r-', linewidth=0.8,
            alpha=0.7, label='3.0')
    ax.set_ylabel('‖u‖')
    ax.legend(fontsize=8)

    # Panel 3: ρ_min
    ax = axes[2]
    ax.plot(t2, log_v2['rho_min'], 'b-', linewidth=0.8, label='2.0 ρ_min')
    ax.plot(t3, log_v3['rho_min'], 'r-', linewidth=0.8,
            alpha=0.7, label='3.0 ρ_min')
    ax.axhline(y=1.0, color='black', linestyle='--', linewidth=0.8)
    ax.set_ylabel('ρ_min')
    ax.legend(fontsize=8)

    # Panel 4: PID terms (3.0 only)
    ax = axes[3]
    pid_P = log_v3.get('pid_P', [])
    pid_I = log_v3.get('pid_I', [])
    pid_D = log_v3.get('pid_D', [])
    if pid_P:
        ax.plot(t3, pid_P, 'r-', linewidth=0.8, alpha=0.8,
                label='P (spectral kick)')
        ax.plot(t3, pid_I, 'g-', linewidth=0.8, alpha=0.8,
                label='I (costate)')
        ax.plot(t3, pid_D, 'b-', linewidth=0.8, alpha=0.8,
                label='D (drift)')
    ax.axhline(y=0.0, color='gray', linestyle='-', linewidth=0.5)
    ax.set_ylabel('3.0 PID terms')
    ax.legend(fontsize=8)

    # Panel 5: Arc type comparison
    ax = axes[4]
    ax.fill_between(t2, log_v2['arc_type'], step='post',
                     alpha=0.3, color='blue', label='2.0 bang')
    ax.fill_between(t3, log_v3['arc_type'], step='post',
                     alpha=0.3, color='red', label='3.0 bang')
    ax.set_ylabel('Arc type')
    ax.set_xlabel('Time (s)')
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['Singular', 'Bang'])
    ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(_OUTPUT_DIR, 'compare_v2_v3.png'), dpi=150)
    print("Saved compare_v2_v3.png")
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='Compare GRJL 2.0 vs 3.0')
    parser.add_argument('--headless', action='store_true',
                        help='No plots')
    args = parser.parse_args()

    if args.headless:
        matplotlib.use('Agg')

    log_v2, log_v3, log_nd = run_comparison(headless=args.headless)

    if not args.headless:
        plot_comparison(log_v2, log_v3, log_nd)

    print("\nDone.")


if __name__ == '__main__':
    main()
