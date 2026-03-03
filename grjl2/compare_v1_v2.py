"""
Compare GRJL 1.0 (discrete modes) vs 2.0 (continuous ρ)

Runs both simulators with identical initial conditions and produces
a 4-panel comparison: λ₁, control norm, ρ, edge weights.

Usage:
    python compare_v1_v2.py [--headless]
"""

import argparse
import os
import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

# Ensure both packages are importable
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_CODE_DIR)
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, 'grjl'))
sys.path.insert(0, os.path.join(_ROOT, 'grjl2'))
_OUTPUT_DIR = os.path.join(_CODE_DIR, 'outputs')
os.makedirs(_OUTPUT_DIR, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description='Compare GRJL 1.0 vs 2.0')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()

    if args.headless:
        matplotlib.use('Agg')

    # ── Run 1.0 ──
    print("[1/2] Running GRJL 1.0 (discrete modes)...")
    from grjl.threebody_damper import simulate as simulate_v1
    log_v1 = simulate_v1(use_damper=True, headless=True)

    # ── Run 2.0 ──
    print("[2/2] Running GRJL 2.0 (continuous ρ)...")
    from grjl2.threebody_rho import simulate_reactive as simulate_v2
    log_v2 = simulate_v2(use_damper=True, headless=True)

    # ── 4-panel plot ──
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    t1, t2 = log_v1['time'], log_v2['time']

    # Panel 1: λ₁
    ax = axes[0, 0]
    ax.plot(t1, log_v1['lambda1'], 'b-', linewidth=1, label='1.0 (discrete)')
    ax.plot(t2, log_v2['lambda1'], 'r-', linewidth=1, label='2.0 (ρ)', alpha=0.8)
    ax.axhline(y=0.02, color='orange', linestyle=':', linewidth=0.8)
    ax.set_ylabel('λ₁')
    ax.set_title('Fiedler Eigenvalue')
    ax.legend(fontsize=8)
    ax.set_ylim(bottom=-0.01)

    # Panel 2: Control norm
    ax = axes[0, 1]
    ax.plot(t1, log_v1['control_norm'], 'b-', linewidth=0.8,
            label='1.0', alpha=0.6)
    ax.plot(t2, log_v2['control_norm'], 'r-', linewidth=0.8,
            label='2.0', alpha=0.6)
    ax.set_ylabel('‖u‖')
    ax.set_title('Control Effort')
    ax.legend(fontsize=8)

    # Panel 3: ρ (2.0 only)
    ax = axes[1, 0]
    if 'rho_min' in log_v2:
        ax.plot(t2, log_v2['rho_min'], 'r-', linewidth=1, label='ρ_min')
        ax.plot(t2, log_v2['rho_max'], 'b-', linewidth=0.8,
                alpha=0.5, label='ρ_max')
    ax.axhline(y=1.0, color='black', linestyle='--',
               linewidth=0.8, label='ρ = 1')
    ax.set_ylabel('ρ')
    ax.set_xlabel('Time')
    ax.set_title('Order Parameter (2.0)')
    ax.legend(fontsize=8)

    # Panel 4: Edge weights
    ax = axes[1, 1]
    if 'edge_weights' in log_v2 and log_v2['edge_weights']:
        # Extract one representative edge weight over time
        first_key = None
        w_series = []
        for wd in log_v2['edge_weights']:
            if first_key is None and wd:
                first_key = list(wd.keys())[0]
            w_series.append(wd.get(first_key, 0.0) if first_key else 0.0)
        ax.plot(t2, w_series, 'r-', linewidth=1,
                label=f'w({first_key}) (2.0)')
    ax.set_ylabel('Edge weight')
    ax.set_xlabel('Time')
    ax.set_title('Smooth Edge Weights')
    ax.legend(fontsize=8)

    fig.suptitle('GRJL 1.0 vs 2.0 — 顿开金绳，扯断玉锁', fontsize=13)
    plt.tight_layout()
    _out = os.path.join(_OUTPUT_DIR, 'grjl_v1_v2_comparison.png')
    plt.savefig(_out, dpi=150)
    print(f"Saved {_out}")

    # ── Stats ──
    print("\n  1.0: J={:.4f}  bang={:.1f}%  λ₁_min={:.4f}".format(
        log_v1['total_cost'],
        100 * np.mean(np.array(log_v1['arc_type']) == 1),
        np.min(log_v1['lambda1'])))
    print("  2.0: J={:.4f}  bang={:.1f}%  λ₁_min={:.4f}  "
          "ρ_crossings={}".format(
        log_v2['total_cost'],
        100 * np.mean(np.array(log_v2['arc_type']) == 1),
        np.min(log_v2['lambda1']),
        int(np.sum(np.diff(np.sign(
            np.array(log_v2['rho_min']) - 1.0)) != 0))))

    if not args.headless:
        plt.show()


if __name__ == '__main__':
    main()
