"""
Verification for Links 1-3: scripted pick-and-place with free-floating gripper.

Uses mocap body (direct Cartesian control, no IK) to execute:
  1. Approach: gripper descends to block       → ρ rises toward 1
  2. Grasp:   fingers close                    → λ₁ becomes positive
  3. Lift:    gripper rises with block          → ρ stays high, λ₁ stable
  4. Wind:    stochastic horizontal force       → λ₁_eff drops
  5. Place:   gripper descends, fingers open    → ρ drops, λ₁ → table contact

Verifications:
  V4.1:  ρ_contact tracks approach/retreat
  V4.3:  λ₁ ≥ ε during grasp
  V4.11: Wind reduces λ₁_eff
  NEW:   ρ crosses 1 at contact transition
"""

import numpy as np
import mujoco
import sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kinematics import rho_from_contacts, lambda1, lambda1_effective, Wind
from observer.wrist_observer import make_observer


def lerp(a, b, t):
    """Linear interpolation: a at t=0, b at t=1."""
    return a + (b - a) * np.clip(t, 0, 1)


def main():
    # ── Load scene ────────────────────────────────────────────
    m = mujoco.MjModel.from_xml_path(str(ROOT / 'scene' / 'floating_gripper.xml'))
    d = mujoco.MjData(m)

    # IDs
    hand_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "hand")
    cube_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "block_cube_0")
    cube_mass = m.body_mass[cube_id]
    print(f"Cube body ID: {cube_id}, mass: {cube_mass:.3f} kg")

    # Setup
    wind = Wind(F_max=0.0, seed=42)
    observer = make_observer(m, mode="gt")

    # ── Gripper poses ─────────────────────────────────────────
    # Orientation: gripper points down (-z world)
    grip_quat = np.array([0.707107, 0.707107, 0, 0])

    # Cube is at (0.3, 0, 0.02), half-height = 0.02
    # Finger pads reach ~0.103 below hand center (0.058 + 0.045)
    # So hand z for contact ≈ 0.02 + 0.103 = 0.123
    cube_xy = np.array([0.3, 0.0])
    z_home  = 0.25     # start height
    z_grasp = 0.115    # contact height (tuned)
    z_lift  = 0.20     # lift height

    OPEN  = 0.04       # finger fully open
    CLOSE = 0.015      # finger closed on 4cm cube (2cm half-width)

    # ── Phase schedule ────────────────────────────────────────
    # Each phase: (duration_s, description)
    phases = [
        (0.3, "settle"),          # 0.0 - 0.3
        (0.5, "approach"),        # 0.3 - 0.8
        (0.3, "close"),           # 0.8 - 1.1
        (0.5, "lift"),            # 1.1 - 1.6
        (0.5, "hold"),            # 1.6 - 2.1
        (0.5, "wind_light"),      # 2.1 - 2.6
        (0.5, "wind_strong"),     # 2.6 - 3.1
        (0.3, "descend"),         # 3.1 - 3.4
        (0.3, "open"),            # 3.4 - 3.7
        (0.3, "retreat"),         # 3.7 - 4.0
    ]
    phase_starts = []
    t_acc = 0
    for dur, name in phases:
        phase_starts.append((t_acc, t_acc + dur, name))
        t_acc += dur
    T_total = t_acc

    print(f"\nPhase schedule ({T_total:.1f}s total):")
    for t0, t1, name in phase_starts:
        print(f"  [{t0:.1f}-{t1:.1f}] {name}")

    # ── Simulation ────────────────────────────────────────────
    dt = m.opt.timestep
    N_steps = int(T_total / dt)
    sample_every = 10

    # Storage
    times, rho_vals, lam1_vals, lam1_eff_vals = [], [], [], []
    wind_mag, phase_ids = [], []
    grip_z_vals = []

    # Initialize: gripper at home, fingers open
    d.mocap_pos[0] = [cube_xy[0], cube_xy[1], z_home]
    d.mocap_quat[0] = grip_quat
    d.ctrl[0] = OPEN

    # Settle
    for _ in range(200):
        mujoco.mj_step(m, d)

    for step in range(N_steps):
        t = step * dt

        # Determine current phase
        phase_name = "settle"
        phase_frac = 0.0
        pid = 0
        for i, (t0, t1, name) in enumerate(phase_starts):
            if t0 <= t < t1:
                phase_name = name
                phase_frac = (t - t0) / (t1 - t0)
                pid = i
                break

        # ── Control ───────────────────────────────────────
        if phase_name == "settle":
            target_z = z_home
            finger = OPEN

        elif phase_name == "approach":
            target_z = lerp(z_home, z_grasp, phase_frac)
            finger = OPEN

        elif phase_name == "close":
            target_z = z_grasp
            finger = lerp(OPEN, CLOSE, phase_frac)

        elif phase_name == "lift":
            target_z = lerp(z_grasp, z_lift, phase_frac)
            finger = CLOSE

        elif phase_name == "hold":
            target_z = z_lift
            finger = CLOSE

        elif phase_name == "wind_light":
            target_z = z_lift
            finger = CLOSE
            wind.F_max = 0.2 * cube_mass * 9.81

        elif phase_name == "wind_strong":
            target_z = z_lift
            finger = CLOSE
            wind.F_max = 0.8 * cube_mass * 9.81

        elif phase_name == "descend":
            target_z = lerp(z_lift, z_grasp, phase_frac)
            finger = CLOSE
            wind.F_max = 0.0

        elif phase_name == "open":
            target_z = z_grasp
            finger = lerp(CLOSE, OPEN, phase_frac)

        elif phase_name == "retreat":
            target_z = lerp(z_grasp, z_home, phase_frac)
            finger = OPEN

        # Apply control
        d.mocap_pos[0] = [cube_xy[0], cube_xy[1], target_z]
        d.mocap_quat[0] = grip_quat
        d.ctrl[0] = finger

        # Wind (only on block when not being held — but for test, apply always)
        if wind.F_max > 0:
            wind.apply(d, [cube_id])
        else:
            wind.clear(d, [cube_id])

        # Step
        mujoco.mj_step(m, d)

        # ── Sample ────────────────────────────────────────
        if step % sample_every == 0:
            rho_c = rho_from_contacts(m, d, cube_id)
            lam1 = lambda1(m, d, cube_id)
            lam1_e = lambda1_effective(m, d, cube_id, wind.last_force)

            times.append(t)
            rho_vals.append(rho_c)
            lam1_vals.append(lam1)
            lam1_eff_vals.append(lam1_e)
            wind_mag.append(np.linalg.norm(wind.last_force))
            phase_ids.append(pid)
            grip_z_vals.append(d.xpos[hand_id, 2])

    # ── Convert to arrays ─────────────────────────────────────
    times = np.array(times)
    rho_vals = np.array(rho_vals)
    lam1_vals = np.array(lam1_vals)
    lam1_eff_vals = np.array(lam1_eff_vals)
    wind_mag = np.array(wind_mag)
    phase_ids = np.array(phase_ids)
    grip_z_vals = np.array(grip_z_vals)

    # ── Results ───────────────────────────────────────────────
    print(f"\n=== Verification Results ===")
    print(f"Steps simulated: {N_steps} ({T_total:.1f}s)")

    # V4.1: ρ tracks approach/retreat
    mask_approach = phase_ids == 1  # approach
    mask_grasp = (phase_ids >= 2) & (phase_ids <= 6)  # close through wind_strong
    mask_open = phase_ids == 8  # open

    rho_approach = rho_vals[mask_approach]
    rho_grasp = rho_vals[mask_grasp]
    rho_open = rho_vals[mask_open]

    print(f"\nV4.1 — ρ_contact during phases:")
    print(f"  Approach:  mean={rho_approach.mean():.4f}, "
          f"max={rho_approach.max():.4f}")
    print(f"  Grasp+Lift: mean={rho_grasp.mean():.4f}, "
          f"min={rho_grasp.min():.4f}")
    print(f"  Open:       mean={rho_open.mean():.4f}")

    # V4.3: λ₁ ≥ ε during grasp
    mask_hold = (phase_ids >= 3) & (phase_ids <= 4)  # lift + hold (no wind)
    lam1_hold = lam1_vals[mask_hold]
    eps = 0.05
    print(f"\nV4.3 — λ₁ during lift+hold (no wind):")
    print(f"  Mean: {lam1_hold.mean():.4f}")
    print(f"  Min:  {lam1_hold.min():.4f}")
    print(f"  λ₁ ≥ ε ({eps})? {(lam1_hold >= eps).all()}")

    # V4.11: Wind effect
    mask_wl = phase_ids == 5  # wind_light
    mask_ws = phase_ids == 6  # wind_strong
    lam1_wl = lam1_eff_vals[mask_wl]
    lam1_ws = lam1_eff_vals[mask_ws]

    print(f"\nV4.11 — Wind effect on λ₁_eff:")
    print(f"  No wind (hold):     λ₁ mean = {lam1_hold.mean():.4f}")
    if len(lam1_wl) > 0:
        print(f"  Light wind (0.2mg): λ₁_eff mean = {lam1_wl.mean():.4f}, "
              f"min = {lam1_wl.min():.4f}")
    if len(lam1_ws) > 0:
        print(f"  Strong wind (0.8mg): λ₁_eff mean = {lam1_ws.mean():.4f}, "
              f"min = {lam1_ws.min():.4f}")

    # Final block position
    obs = observer.observe(d)
    cube_obs = obs[cube_id]
    print(f"\nFinal cube position: {cube_obs.position}")
    print(f"Final cube height: {cube_obs.position[2]*100:.2f} cm")

    # ── Plot ──────────────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

        # Phase background colors
        phase_colors = {
            'settle': '#ffffff', 'approach': '#fff3cd',
            'close': '#d1ecf1', 'lift': '#d4edda',
            'hold': '#d4edda', 'wind_light': '#fff3cd',
            'wind_strong': '#f8d7da', 'descend': '#e2e3e5',
            'open': '#d1ecf1', 'retreat': '#ffffff',
        }
        for ax in axes:
            for t0, t1, name in phase_starts:
                ax.axvspan(t0, t1, alpha=0.3,
                           color=phase_colors.get(name, '#ffffff'))

        # Panel 0: gripper height
        axes[0].plot(times, grip_z_vals * 100, color='gray', label='gripper z')
        axes[0].axhline(z_grasp * 100, color='r', ls=':', alpha=0.5,
                        label=f'z_grasp={z_grasp*100:.1f}cm')
        axes[0].set_ylabel('Height (cm)')
        axes[0].legend(loc='upper right')
        axes[0].set_title('Gripper height')

        # Panel 1: ρ
        axes[1].plot(times, rho_vals, label='ρ (contact)', color='darkorange')
        axes[1].axhline(1.0, color='r', ls=':', alpha=0.5, label='ρ = 1')
        axes[1].set_ylabel('ρ')
        axes[1].legend(loc='upper right')
        axes[1].set_title('Contact order parameter ρ(t)')

        # Panel 2: λ₁ and λ₁_eff
        axes[2].plot(times, lam1_vals, label='λ₁', color='green')
        axes[2].plot(times, lam1_eff_vals, label='λ₁_eff', color='red',
                     ls='--', alpha=0.8)
        axes[2].axhline(eps, color='gray', ls=':', alpha=0.5,
                        label=f'ε = {eps}')
        axes[2].set_ylabel('λ₁')
        axes[2].legend(loc='upper right')
        axes[2].set_title('Spectral gap λ₁(t) and λ₁_eff(t)')

        # Panel 3: wind
        axes[3].plot(times, wind_mag, label='|F_wind|', color='purple')
        axes[3].set_ylabel('Force (N)')
        axes[3].set_xlabel('Time (s)')
        axes[3].legend(loc='upper right')
        axes[3].set_title('Wind force magnitude')

        # Phase labels at top
        for t0, t1, name in phase_starts:
            axes[0].text((t0 + t1) / 2, axes[0].get_ylim()[1] * 0.95,
                         name, ha='center', va='top', fontsize=7,
                         style='italic')

        plt.tight_layout()
        outpath = str(ROOT / 'assets' / 'visual_reads' / 'verify_link1_pick_place.png')
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        plt.savefig(outpath, dpi=150)
        print(f"\nPlot saved to {outpath}")
    except ImportError:
        print("\nmatplotlib not available, skipping plot")


if __name__ == "__main__":
    main()
