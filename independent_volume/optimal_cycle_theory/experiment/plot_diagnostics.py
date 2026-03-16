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

    # ── Figure 3: Solved centroidal trajectory vs reference ──
    all_trajs = npz['all_trajectories']
    has_ref = 'x_ref' in npz
    if all_trajs.ndim == 3 and all_trajs.shape[2] == 13:
        # Best centroidal trajectory (last iteration)
        x_solved = all_trajs[-1]  # (H+1, 13)
        H1 = x_solved.shape[0]
        dt_cent = 0.01  # OCP dt
        t_cent = np.arange(H1) * dt_cent

        x_ref = npz['x_ref'] if has_ref else None

        fig3 = plt.figure(figsize=(16, 12))
        fig3.suptitle('Solved Centroidal Trajectory vs Reference', fontsize=12)
        gs3 = gridspec.GridSpec(4, 2, figure=fig3, hspace=0.45, wspace=0.3)

        # (0,0) Position px, py
        ax = fig3.add_subplot(gs3[0, 0])
        ax.plot(t_cent, x_solved[:, 0], 'r-', linewidth=1.5, label='px (solved)')
        ax.plot(t_cent, x_solved[:, 1], 'g-', linewidth=1.5, label='py (solved)')
        if x_ref is not None:
            ax.plot(t_cent, x_ref[:H1, 0], 'r--', linewidth=1, alpha=0.6, label='px (ref)')
            ax.plot(t_cent, x_ref[:H1, 1], 'g--', linewidth=1, alpha=0.6, label='py (ref)')
        ax.set_ylabel('Position (m)')
        ax.set_title('Horizontal position: px, py', fontsize=9)
        ax.legend(fontsize=7, ncol=2)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Time (s)')

        # (0,1) Position pz
        ax = fig3.add_subplot(gs3[0, 1])
        ax.plot(t_cent, x_solved[:, 2], 'b-', linewidth=1.5, label='pz (solved)')
        if x_ref is not None:
            ax.plot(t_cent, x_ref[:H1, 2], 'b--', linewidth=1, alpha=0.6, label='pz (ref)')
        ax.axhline(0.27, color='b', linestyle=':', alpha=0.3, linewidth=0.8, label='z_target')
        ax.axhline(0.13, color='k', linestyle=':', alpha=0.3, linewidth=0.8, label='z_min')
        ax.axhline(0.41, color='k', linestyle=':', alpha=0.3, linewidth=0.8, label='z_max')
        ax.set_ylabel('Height (m)')
        ax.set_title('Vertical position: pz', fontsize=9)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Time (s)')

        # (1,0) Velocity vx, vy
        ax = fig3.add_subplot(gs3[1, 0])
        ax.plot(t_cent, x_solved[:, 3], 'r-', linewidth=1.5, label='vx (solved)')
        ax.plot(t_cent, x_solved[:, 4], 'g-', linewidth=1.5, label='vy (solved)')
        if x_ref is not None:
            ax.plot(t_cent, x_ref[:H1, 3], 'r--', linewidth=1, alpha=0.6, label='vx (ref)')
            ax.plot(t_cent, x_ref[:H1, 4], 'g--', linewidth=1, alpha=0.6, label='vy (ref)')
        ax.set_ylabel('Velocity (m/s)')
        ax.set_title('Horizontal velocity: vx, vy', fontsize=9)
        ax.legend(fontsize=7, ncol=2)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Time (s)')

        # (1,1) Velocity vz
        ax = fig3.add_subplot(gs3[1, 1])
        ax.plot(t_cent, x_solved[:, 5], 'b-', linewidth=1.5, label='vz (solved)')
        if x_ref is not None:
            ax.plot(t_cent, x_ref[:H1, 5], 'b--', linewidth=1, alpha=0.6, label='vz (ref)')
        ax.set_ylabel('Velocity (m/s)')
        ax.set_title('Vertical velocity: vz', fontsize=9)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Time (s)')

        # (2,0) Orientation: roll, pitch, yaw
        ax = fig3.add_subplot(gs3[2, 0])
        ori_labels = ['roll', 'pitch', 'yaw']
        ori_colors = ['r', 'g', 'b']
        for i in range(3):
            ax.plot(t_cent, np.degrees(x_solved[:, 6+i]), color=ori_colors[i],
                    linewidth=1.5, label=f'{ori_labels[i]} (solved)')
        ax.axhline(30, color='k', linestyle=':', alpha=0.3, linewidth=0.8)
        ax.axhline(-30, color='k', linestyle=':', alpha=0.3, linewidth=0.8)
        ax.set_ylabel('Angle (deg)')
        ax.set_title('Orientation: roll, pitch, yaw', fontsize=9)
        ax.legend(fontsize=7, ncol=3)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Time (s)')

        # (2,1) Angular velocity: wx, wy, wz
        ax = fig3.add_subplot(gs3[2, 1])
        for i in range(3):
            ax.plot(t_cent, x_solved[:, 9+i], color=ori_colors[i],
                    linewidth=1.5, label=f'ω_{ori_labels[i][0]} (solved)')
        ax.set_ylabel('Angular vel (rad/s)')
        ax.set_title('Angular velocity: ωx, ωy, ωz', fontsize=9)
        ax.legend(fontsize=7, ncol=3)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Time (s)')

        # (3,0) Contact modes: barrier scales σ_k (Gantt-style)
        has_scales = 'best_scales' in npz
        has_heights = 'best_heights' in npz
        if has_scales:
            ax = fig3.add_subplot(gs3[3, 0])
            scales = npz['best_scales']
            T_sc = min(scales.shape[0], H1)
            t_sc = np.arange(T_sc) * dt_cent
            for k in range(4):
                y_base = 3 - k
                # Gantt bars: stance (σ > 0.5)
                for i in range(T_sc):
                    if scales[i, k] > 0.5:
                        ax.barh(y_base, dt_cent, left=t_sc[i], height=0.6,
                                color=LEG_COLORS[k], alpha=0.7, edgecolor='none')
                # σ line overlay
                ax.plot(t_sc, scales[:T_sc, k] * 0.5 + y_base - 0.25,
                        color=LEG_COLORS[k], linewidth=0.8, alpha=0.6)
            ax.set_yticks([0, 1, 2, 3])
            ax.set_yticklabels(list(reversed(LEG_NAMES)))
            ax.set_ylabel('Foot')
            ax.set_title('Solved contact mode σ_k (bars: stance, lines: σ)', fontsize=9)
            ax.set_ylim(-0.5, 3.8)
            ax.grid(True, alpha=0.3, axis='x')
            ax.set_xlabel('Time (s)')
        elif x_ref is not None:
            # Fallback: tracking error
            ax = fig3.add_subplot(gs3[3, 0])
            err_pos = np.linalg.norm(x_solved[:, 0:3] - x_ref[:H1, 0:3], axis=1)
            err_vel = np.linalg.norm(x_solved[:, 3:6] - x_ref[:H1, 3:6], axis=1)
            err_ori = np.linalg.norm(x_solved[:, 6:9] - x_ref[:H1, 6:9], axis=1)
            ax.plot(t_cent, err_pos, 'r-', linewidth=1.5, label='‖Δp‖ (m)')
            ax.plot(t_cent, err_vel, 'b-', linewidth=1.5, label='‖Δv‖ (m/s)')
            ax.plot(t_cent, err_ori, 'g-', linewidth=1.5, label='‖Δφ‖ (rad)')
            ax.set_ylabel('Tracking error')
            ax.set_title('Tracking error vs reference', fontsize=9)
            ax.legend(fontsize=7, ncol=3)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('Time (s)')

        # (3,1) Foot heights + tracking error
        ax = fig3.add_subplot(gs3[3, 1])
        if has_heights:
            heights_data = npz['best_heights']
            T_h = min(heights_data.shape[0], H1)
            t_h = np.arange(T_h) * dt_cent
            for k in range(4):
                ax.plot(t_h, heights_data[:T_h, k], color=LEG_COLORS[k],
                        linewidth=1.2, label=LEG_NAMES[k])
            ax.set_ylabel('Foot height (m)')
            ax.set_title('Solved foot height schedule h_k(t)', fontsize=9)
            ax.legend(fontsize=7, ncol=4)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('Time (s)')
        else:
            # Fallback: phase clock
            ax.plot(t_cent, x_solved[:, 12], 'k-', linewidth=1.5, label='phase (solved)')
            if x_ref is not None:
                ax.plot(t_cent, x_ref[:H1, 12], 'k--', linewidth=1, alpha=0.6, label='phase (ref)')
            ax.set_ylabel('Phase')
            ax.set_title('Stride phase clock', fontsize=9)
            ax.legend(fontsize=7)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('Time (s)')

        fig3.tight_layout(rect=[0, 0, 1, 0.96])
        if save:
            out_path3 = str(Path(out_dir) / 'solved_trajectory.png')
            fig3.savefig(out_path3, dpi=150, bbox_inches='tight')
            print(f"Saved {out_path3}")
        else:
            plt.show()


if __name__ == '__main__':
    main()
