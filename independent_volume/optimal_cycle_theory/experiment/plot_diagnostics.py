"""Generate MPC-style locomotion diagnostic plots from rollout data.

Usage:
    python plot_diagnostics.py [rollout_data.npz] [--save]

Produces a multi-panel figure with:
  1. CoM position (x, y, z) and velocity
  2. Joint positions (12 joints, grouped by leg)
  3. Joint torques (12 joints, grouped by leg)
  4. Contact pattern (Gantt chart: stance/swing per foot)
  5. Barrier scales σ_k and foot height schedule
  6. MPPI convergence (cost, ε, entropy, ESS)
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

LEG_NAMES = ["FL", "FR", "RL", "RR"]  # matches MuJoCo + corrected gait_sampler order
JOINT_NAMES = ["hip", "thigh", "calf"]
LEG_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]


def load_data(npz_path: str):
    npz = np.load(npz_path)
    json_path = Path(npz_path).with_suffix('.json')
    with open(json_path) as f:
        meta = json.load(f)
    return npz, meta


def plot_com(ax_pos, ax_vel, com, dt):
    """CoM position and velocity vs time."""
    T = com.shape[0]
    t = np.arange(T) * dt

    for i, (label, color) in enumerate(zip(['x', 'y', 'z'], ['r', 'g', 'b'])):
        ax_pos.plot(t, com[:, i], color=color, label=label, linewidth=1)
    ax_pos.set_ylabel('CoM position (m)')
    ax_pos.legend(loc='upper right', fontsize=7, ncol=3)
    ax_pos.axhline(0.3, color='b', linestyle='--', alpha=0.3, linewidth=0.8)
    ax_pos.axhline(0.15, color='b', linestyle=':', alpha=0.3, linewidth=0.8)
    ax_pos.axhline(0.45, color='b', linestyle=':', alpha=0.3, linewidth=0.8)

    for i, (label, color) in enumerate(zip(['vx', 'vy', 'vz'], ['r', 'g', 'b'])):
        ax_vel.plot(t, com[:, 3+i], color=color, label=label, linewidth=1)
    ax_vel.axhline(1.0, color='r', linestyle='--', alpha=0.3, linewidth=0.8)
    ax_vel.set_ylabel('CoM velocity (m/s)')
    ax_vel.legend(loc='upper right', fontsize=7, ncol=3)


def plot_joints(ax, qpos, dt, title='Joint positions'):
    """Joint angles grouped by leg."""
    T = qpos.shape[0]
    t = np.arange(T) * dt
    joints = qpos[:, 7:19]  # 12 joint angles

    for k in range(4):
        for j in range(3):
            idx = 3*k + j
            ls = ['-', '--', ':'][j]
            label = f"{LEG_NAMES[k]}_{JOINT_NAMES[j]}" if k == 0 else None
            ax.plot(t, joints[:, idx], color=LEG_COLORS[k],
                    linestyle=ls, linewidth=0.8,
                    label=f"{JOINT_NAMES[j]}" if k == 0 else None)
    ax.set_ylabel('Joint angle (rad)')
    ax.set_title(title, fontsize=9)
    # Custom legend: one entry per joint type + one per leg
    from matplotlib.lines import Line2D
    handles = []
    for j in range(3):
        handles.append(Line2D([0], [0], color='gray', linestyle=['-', '--', ':'][j],
                              label=JOINT_NAMES[j]))
    for k in range(4):
        handles.append(Line2D([0], [0], color=LEG_COLORS[k], linestyle='-',
                              label=LEG_NAMES[k]))
    ax.legend(handles=handles, loc='upper right', fontsize=6, ncol=4)


def plot_torques(ax, torques, dt):
    """Joint torques grouped by leg."""
    T = torques.shape[0]
    t = np.arange(T) * dt

    for k in range(4):
        for j in range(3):
            idx = 3*k + j
            ls = ['-', '--', ':'][j]
            ax.plot(t, torques[:, idx], color=LEG_COLORS[k],
                    linestyle=ls, linewidth=0.8)
    ax.set_ylabel('Torque (N·m)')
    ax.set_title('Joint torques', fontsize=9)


def plot_contacts(ax, contacts, scales, dt):
    """Gantt-chart contact pattern + barrier scales overlay."""
    T = contacts.shape[0]
    t = np.arange(T) * dt

    for k in range(4):
        # Contact Gantt bars
        in_contact = contacts[:, k] > 0.5
        y_base = 3 - k  # FL on top
        for i in range(T):
            if in_contact[i]:
                ax.barh(y_base, dt, left=t[i], height=0.6,
                        color=LEG_COLORS[k], alpha=0.7, edgecolor='none')
        # Barrier scale as line overlay (truncate to match contacts length)
        s = scales[:T, k]
        ax.plot(t, s * 0.5 + y_base - 0.25,
                color=LEG_COLORS[k], linewidth=0.8, alpha=0.5)

    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(list(reversed(LEG_NAMES)))
    ax.set_ylabel('Foot')
    ax.set_title('Contact pattern (bars) + barrier scale σ (lines)', fontsize=9)
    ax.set_ylim(-0.5, 3.8)


def plot_foot_heights(ax, heights, height_fracs, dt):
    """Foot height schedule and normalized fractions."""
    T = heights.shape[0]
    t = np.arange(T) * dt

    for k in range(4):
        ax.plot(t, heights[:, k], color=LEG_COLORS[k], linewidth=1,
                label=LEG_NAMES[k])
    ax.set_ylabel('Foot height (m)')
    ax.set_title('Foot height schedule h_k(t; φ)', fontsize=9)
    ax.legend(loc='upper right', fontsize=7, ncol=4)


def plot_mppi_convergence(axes, diagnostics):
    """MPPI convergence: cost, ε, entropy, ESS."""
    iters = np.arange(len(diagnostics['cost_best']))

    ax_cost, ax_eps, ax_ent = axes

    ax_cost.plot(iters, diagnostics['cost_mean'], 'b-', linewidth=1, label='mean')
    ax_cost.fill_between(iters,
                         np.array(diagnostics['cost_mean']) - np.array(diagnostics['cost_std']),
                         np.array(diagnostics['cost_mean']) + np.array(diagnostics['cost_std']),
                         alpha=0.2, color='b')
    ax_cost.plot(iters, diagnostics['cost_best'], 'r-', linewidth=1, label='best')
    ax_cost.set_ylabel('Cost')
    ax_cost.legend(fontsize=7)
    ax_cost.set_title('MPPI convergence', fontsize=9)

    ax_eps.plot(iters, diagnostics['epsilon'], 'k-', linewidth=1)
    ax_eps.set_ylabel('ε')
    ax_eps.set_xlabel('Iteration')

    ax_ent.plot(iters, diagnostics['entropy'], 'g-', linewidth=1, label='S')
    ax_ent2 = ax_ent.twinx()
    ax_ent2.plot(iters, diagnostics['ess'], 'orange', linewidth=1, label='ESS')
    ax_ent.set_ylabel('Entropy S', color='g')
    ax_ent2.set_ylabel('ESS', color='orange')
    ax_ent.set_xlabel('Iteration')


def main():
    npz_path = sys.argv[1] if len(sys.argv) > 1 else 'rollout_data.npz'
    save = '--save' in sys.argv
    out_dir = str(Path(npz_path).parent)
    npz, meta = load_data(npz_path)

    has_playback = 'pb_torques' in npz
    diagnostics = meta['diagnostics']
    dt = meta.get('playback_duration', 2.0) / (npz['pb_com'].shape[0] - 1) if has_playback else 0.01

    # ── Figure 1: Playback trajectory diagnostics ──
    if has_playback:
        fig = plt.figure(figsize=(16, 14))
        fig.suptitle(f"Quadruped Locomotion Diagnostics — φ*={meta['best_phi']}", fontsize=12)
        gs = gridspec.GridSpec(6, 2, figure=fig, hspace=0.4, wspace=0.3)

        # Row 1: CoM position + velocity
        ax_pos = fig.add_subplot(gs[0, 0])
        ax_vel = fig.add_subplot(gs[0, 1])
        plot_com(ax_pos, ax_vel, npz['pb_com'], dt)

        # Row 2: Joint positions (qpos)
        ax_joints = fig.add_subplot(gs[1, :])
        traj = npz['playback_trajectory']
        nq = meta['nq']
        qpos_traj = traj[:, :nq]
        # Build fake full qpos array for plot_joints
        plot_joints(ax_joints, qpos_traj, dt, title='Joint positions (rad)')

        # Row 3: Joint torques
        ax_torques = fig.add_subplot(gs[2, :])
        plot_torques(ax_torques, npz['pb_torques'], dt)

        # Row 4: Contact pattern
        ax_contacts = fig.add_subplot(gs[3, :])
        plot_contacts(ax_contacts, npz['pb_contacts'], npz['pb_barrier_scales'], dt)

        # Row 5: Foot heights
        ax_heights = fig.add_subplot(gs[4, :])
        plot_foot_heights(ax_heights, npz['pb_foot_heights'], npz['pb_height_fracs'], dt)

        # Row 6: MPPI convergence
        ax_c = fig.add_subplot(gs[5, 0])
        ax_e = fig.add_subplot(gs[5, 1])
        # Squeeze in a third axis for entropy/ESS
        ax_s = ax_e.twinx()

        iters = np.arange(len(diagnostics['cost_best']))
        ax_c.plot(iters, diagnostics['cost_mean'], 'b-', linewidth=1, label='mean')
        ax_c.fill_between(iters,
                          np.array(diagnostics['cost_mean']) - np.array(diagnostics['cost_std']),
                          np.array(diagnostics['cost_mean']) + np.array(diagnostics['cost_std']),
                          alpha=0.2, color='b')
        ax_c.plot(iters, diagnostics['cost_best'], 'r-', linewidth=1, label='best')
        ax_c.set_ylabel('Cost')
        ax_c.set_xlabel('Iteration')
        ax_c.legend(fontsize=7)
        ax_c.set_title('MPPI convergence', fontsize=9)

        ax_e.plot(iters, diagnostics['epsilon'], 'k-', linewidth=1, label='ε')
        ax_e.set_ylabel('ε', color='k')
        ax_e.set_xlabel('Iteration')
        ax_s.plot(iters, diagnostics['ess'], color='orange', linewidth=1, label='ESS')
        ax_s.set_ylabel('ESS', color='orange')
        ax_e.set_title('Temperature ε and ESS', fontsize=9)

        # Set common x-label for playback rows
        for ax in [ax_pos, ax_vel, ax_joints, ax_torques, ax_contacts, ax_heights]:
            ax.set_xlabel('Time (s)')
            ax.grid(True, alpha=0.3)

        if save:
            out_path = str(Path(out_dir) / 'locomotion_diagnostics.png')
            fig.savefig(out_path, dpi=150, bbox_inches='tight')
            print(f"Saved {out_path}")
        else:
            plt.show()
    else:
        print("No playback data found. Run with --playback to generate.")

    # ── Figure 2: Cost decomposition (if available) ──
    if 'best_vel' in diagnostics:
        fig2, axes2 = plt.subplots(2, 2, figsize=(14, 8))
        fig2.suptitle('MPPI Convergence Decomposition', fontsize=12)
        iters = np.arange(len(diagnostics['cost_best']))

        # (0,0) Stacked area: best sample cost components
        ax = axes2[0, 0]
        vel = np.array(diagnostics['best_vel'])
        ht = np.array(diagnostics['best_height'])
        hb = np.array(diagnostics['best_height_bar'])
        ob = np.array(diagnostics['best_ori_bar'])
        jb = np.array(diagnostics['best_joint_bar'])
        ctrl = np.array(diagnostics.get('best_control', np.zeros_like(vel)))
        cb = np.array(diagnostics.get('best_contact_bar', np.zeros_like(vel)))
        ax.stackplot(iters, vel, ht, ctrl, hb, ob, jb, cb,
                     labels=['velocity', 'height track', 'control ‖u‖²R',
                             'height barrier', 'orient barrier',
                             'joint barrier', 'contact barrier'],
                     alpha=0.7)
        ax.plot(iters, diagnostics['cost_best'], 'k--', linewidth=1.5, label='total')
        ax.set_ylabel('Cost (best sample)')
        ax.set_title('Best sample: cost decomposition', fontsize=9)
        ax.legend(fontsize=6, loc='upper right')
        ax.grid(True, alpha=0.3)

        # (0,1) Stacked area: mean cost components
        ax = axes2[0, 1]
        vel_m = np.array(diagnostics['mean_vel'])
        ht_m = np.array(diagnostics['mean_height'])
        hb_m = np.array(diagnostics['mean_height_bar'])
        ob_m = np.array(diagnostics['mean_ori_bar'])
        jb_m = np.array(diagnostics['mean_joint_bar'])
        ctrl_m = np.array(diagnostics.get('mean_control', np.zeros_like(vel_m)))
        cb_m = np.array(diagnostics.get('mean_contact_bar', np.zeros_like(vel_m)))
        ax.stackplot(iters, vel_m, ht_m, ctrl_m, hb_m, ob_m, jb_m, cb_m,
                     labels=['velocity', 'height track', 'control ‖u‖²R',
                             'height barrier', 'orient barrier',
                             'joint barrier', 'contact barrier'],
                     alpha=0.7)
        ax.plot(iters, diagnostics['cost_mean'], 'k--', linewidth=1.5, label='total')
        ax.set_ylabel('Cost (mean)')
        ax.set_title('Mean: cost decomposition', fontsize=9)
        ax.legend(fontsize=6, loc='upper right')
        ax.grid(True, alpha=0.3)

        # (1,0) Barrier costs vs epsilon
        ax = axes2[1, 0]
        eps = np.array(diagnostics['epsilon'])
        ax.plot(iters, hb, 'b-', linewidth=1, label='height bar (best)')
        ax.plot(iters, ob, 'g-', linewidth=1, label='orient bar (best)')
        ax.plot(iters, jb, 'r-', linewidth=1, label='joint bar (best)')
        ax2 = ax.twinx()
        ax2.plot(iters, eps, 'k--', linewidth=1, alpha=0.5, label='ε')
        ax.set_ylabel('Barrier cost')
        ax2.set_ylabel('ε', color='gray')
        ax.set_xlabel('Iteration')
        ax.set_title('Barrier costs vs ε', fontsize=9)
        ax.legend(fontsize=6, loc='upper left')
        ax.grid(True, alpha=0.3)

        # (1,1) KL and trust region alpha (if available)
        ax = axes2[1, 1]
        if 'kl' in diagnostics:
            ax.plot(iters, diagnostics['kl'], 'b-', linewidth=1, label='KL')
            if 'tr_alpha' in diagnostics:
                ax3 = ax.twinx()
                ax3.plot(iters, diagnostics['tr_alpha'], 'r-', linewidth=1,
                         alpha=0.7, label='α (step)')
                ax3.set_ylabel('Trust region α', color='r')
                ax3.set_ylim(-0.05, 1.1)
            ax.axhline(0.5, color='b', linestyle=':', alpha=0.3, linewidth=0.8)
            ax.set_ylabel('KL divergence')
            ax.set_title('KL trust region', fontsize=9)
            ax.legend(fontsize=7, loc='upper left')
        else:
            # Fallback: ESS and entropy
            ax.plot(iters, diagnostics['ess'], 'orange', linewidth=1, label='ESS')
            ax.set_ylabel('ESS')
            ax.set_title('Effective sample size', fontsize=9)
            ax.legend(fontsize=7)
        ax.set_xlabel('Iteration')
        ax.grid(True, alpha=0.3)

        fig2.tight_layout()
        if save:
            out_path2 = str(Path(out_dir) / 'convergence_decomposition.png')
            fig2.savefig(out_path2, dpi=150, bbox_inches='tight')
            print(f"Saved {out_path2}")
        else:
            plt.show()


if __name__ == '__main__':
    main()
