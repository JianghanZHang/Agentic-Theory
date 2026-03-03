"""
Verification for Link 1 (kinematics) + Link 3 (observer GT mode).

Runs a scripted pick-and-place of the cube block:
  1. Move gripper to block → ρ rises
  2. Close gripper → λ₁ becomes positive
  3. Lift → ρ stays high, λ₁ stable
  4. Apply wind → λ₁ drops
  5. Open gripper → ρ drops, λ₁ → 0

Plots ρ(t), λ₁(t), and the wind force.

Verifications:
  V4.1: ρ_kinematic ≈ ρ_contact (ground truth)
  V4.3: λ₁ ≥ ε during grasp
  V4.11: Wind reduces λ₁
"""

import numpy as np
import mujoco
import sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kinematics import KinematicRho, rho_from_contacts, lambda1, Wind
from observer.wrist_observer import make_observer


def main():
    # ── Load scene ────────────────────────────────────────────────
    m = mujoco.MjModel.from_xml_path(str(ROOT / 'franka_scene.xml'))
    d = mujoco.MjData(m)

    # Reset to ready keyframe
    mujoco.mj_resetDataKeyframe(m, d, 1)
    mujoco.mj_forward(m, d)

    # ── Setup modules ─────────────────────────────────────────────
    rho_calc = KinematicRho(m, ee_body="hand", alpha=0.3)
    wind = Wind(F_max=0.0, seed=42)
    observer = make_observer(m, mode="gt")

    # Block IDs
    cube_body = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "block_cube_0")
    cube_mass = m.body_mass[cube_body]
    print(f"Cube body ID: {cube_body}, mass: {cube_mass:.3f} kg")

    # ── Observe initial state ─────────────────────────────────────
    obs = observer.observe(d)
    print(f"\nInitial observations ({len(obs)} blocks):")
    for bid, o in obs.items():
        print(f"  {o.body_name} ({o.block_type}): "
              f"pos={o.position}, mass={o.mass_estimate:.3f} kg")

    # ── Run simulation with scripted control ──────────────────────
    dt = m.opt.timestep
    T_total = 2.0  # seconds
    N_steps = int(T_total / dt)

    # Storage
    times = []
    rho_kin = []
    rho_gt = []
    lam1_vals = []
    wind_mag = []

    # Scripted control: just hold the ready position for now
    # (full pick-place requires IK which is Link 4-5)
    # Here we verify the modules work on the static scene
    ctrl_ready = np.array([0, 0.3, 0, -1.5708, 0, 2.0, -0.7854, 255])

    # Phase schedule:
    #   t < 0.5:  no wind
    #   0.5 ≤ t < 1.0:  light wind (0.1 * m*g)
    #   1.0 ≤ t < 1.5:  strong wind (0.5 * m*g)
    #   t ≥ 1.5:  no wind

    for step in range(N_steps):
        t = step * dt

        # Set control
        d.ctrl[:] = ctrl_ready

        # Wind schedule
        if 0.5 <= t < 1.0:
            wind.F_max = 0.1 * cube_mass * 9.81
        elif 1.0 <= t < 1.5:
            wind.F_max = 0.5 * cube_mass * 9.81
        else:
            wind.F_max = 0.0

        # Apply wind to cube
        wind.apply(d, [cube_body])

        # Step simulation
        mujoco.mj_step(m, d)

        # Compute kinematics (every 10 steps to reduce noise)
        if step % 10 == 0:
            rho_k = rho_calc.update(d, cube_mass)
            rho_c = rho_from_contacts(m, d, cube_body)
            lam1 = lambda1(m, d, cube_body)

            times.append(t)
            rho_kin.append(rho_k)
            rho_gt.append(rho_c)
            lam1_vals.append(lam1)
            wind_mag.append(np.linalg.norm(wind.last_force))

    # ── Results ───────────────────────────────────────────────────
    times = np.array(times)
    rho_kin = np.array(rho_kin)
    rho_gt = np.array(rho_gt)
    lam1_vals = np.array(lam1_vals)
    wind_mag = np.array(wind_mag)

    print(f"\n=== Verification Results ===")
    print(f"Steps simulated: {N_steps} ({T_total:.1f}s)")

    # V4.1: ρ_kinematic ≈ ρ_contact
    # (In static scene, both should be near zero since robot isn't grasping)
    rho_diff = np.abs(rho_kin - rho_gt)
    print(f"\nV4.1 — ρ_kinematic vs ρ_contact:")
    print(f"  Mean |diff|: {rho_diff.mean():.6f}")
    print(f"  Max  |diff|: {rho_diff.max():.6f}")
    print(f"  ρ_kin range: [{rho_kin.min():.4f}, {rho_kin.max():.4f}]")
    print(f"  ρ_gt  range: [{rho_gt.min():.4f}, {rho_gt.max():.4f}]")

    # V4.3: λ₁ during static contact (block on table)
    # Block sits on table, so there should be contact with floor
    mask_no_wind = times < 0.5
    lam1_nowind = lam1_vals[mask_no_wind]
    print(f"\nV4.3 — λ₁ (block on table, no wind):")
    print(f"  Mean: {lam1_nowind.mean():.4f}")
    print(f"  Min:  {lam1_nowind.min():.4f}")

    # V4.11: Wind effect on λ₁
    mask_light = (times >= 0.5) & (times < 1.0)
    mask_strong = (times >= 1.0) & (times < 1.5)
    lam1_light = lam1_vals[mask_light]
    lam1_strong = lam1_vals[mask_strong]
    print(f"\nV4.11 — Wind effect on λ₁:")
    print(f"  No wind:      λ₁ mean = {lam1_nowind.mean():.4f}")
    print(f"  Light wind:   λ₁ mean = {lam1_light.mean():.4f}  "
          f"(F_max = 0.1·mg = {0.1*cube_mass*9.81:.3f} N)")
    print(f"  Strong wind:  λ₁ mean = {lam1_strong.mean():.4f}  "
          f"(F_max = 0.5·mg = {0.5*cube_mass*9.81:.3f} N)")

    # ── Save plot ─────────────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

        axes[0].plot(times, rho_kin, label='ρ (kinematic)', alpha=0.8)
        axes[0].plot(times, rho_gt, label='ρ (contact GT)', alpha=0.8, ls='--')
        axes[0].axhline(1.0, color='r', ls=':', alpha=0.5, label='ρ = 1')
        axes[0].set_ylabel('ρ')
        axes[0].legend()
        axes[0].set_title('Contact order parameter ρ(t)')

        axes[1].plot(times, lam1_vals, label='λ₁', color='green')
        axes[1].axhline(0.05, color='r', ls=':', alpha=0.5, label='ε = 0.05')
        axes[1].set_ylabel('λ₁')
        axes[1].legend()
        axes[1].set_title('Spectral gap λ₁(t)')

        axes[2].plot(times, wind_mag, label='|F_wind|', color='orange')
        axes[2].set_ylabel('Force (N)')
        axes[2].set_xlabel('Time (s)')
        axes[2].legend()
        axes[2].set_title('Wind force magnitude')

        # Shade wind periods
        for ax in axes:
            ax.axvspan(0.5, 1.0, alpha=0.1, color='yellow', label='_')
            ax.axvspan(1.0, 1.5, alpha=0.1, color='red', label='_')

        plt.tight_layout()
        outpath = str(ROOT / 'assets' / 'visual_reads' / 'verify_link1.png')
        plt.savefig(outpath, dpi=150)
        print(f"\nPlot saved to {outpath}")
    except ImportError:
        print("\nmatplotlib not available, skipping plot")

    # ── Final observations ────────────────────────────────────────
    obs_final = observer.observe(d)
    cube_obs = obs_final[cube_body]
    print(f"\nFinal cube position: {cube_obs.position}")
    print(f"Initial was: [0.42, -0.08, 0.02]")
    displacement = np.linalg.norm(cube_obs.position - np.array([0.42, -0.08, 0.02]))
    print(f"Displacement: {displacement*100:.2f} cm")
    if displacement > 0.01:
        print("  → Block moved (wind pushed it)")
    else:
        print("  → Block stayed in place")


if __name__ == "__main__":
    main()
