"""
Render the scripted pick-rotate-place as an MP4 video.

Scripted sequence:
  settle → approach → close → lift → reorient → wind → descend → open → retreat

The gripper picks up a cube, rotates it 90° about the vertical axis
while translating to the goal position, endures wind perturbation,
then places the cube at the goal pose and retreats.

Visualises contact points + forces.

Run from project root:
    python verification/render_pick_place.py
"""

import numpy as np
import mujoco
import imageio.v3 as iio
import sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kinematics import Wind


def lerp(a, b, t):
    return a + (b - a) * np.clip(t, 0, 1)


def quat_slerp(q0, q1, t):
    """Spherical linear interpolation between quaternions (w,x,y,z)."""
    t = np.clip(t, 0, 1)
    q0 = q0 / np.linalg.norm(q0)
    q1 = q1 / np.linalg.norm(q1)
    dot = np.dot(q0, q1)
    if dot < 0:
        q1 = -q1
        dot = -dot
    if dot > 0.9995:
        result = q0 + t * (q1 - q0)
        return result / np.linalg.norm(result)
    theta = np.arccos(np.clip(dot, -1, 1))
    return (np.sin((1 - t) * theta) * q0 + np.sin(t * theta) * q1) / np.sin(theta)


def quat_mul(q1, q2):
    """Multiply two quaternions (w,x,y,z format)."""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
    ])


def main():
    m = mujoco.MjModel.from_xml_path(str(ROOT / 'scene' / 'floating_gripper.xml'))
    d = mujoco.MjData(m)

    cube_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "block_cube_0")
    cube_mass = m.body_mass[cube_id]
    wind = Wind(F_max=0.0, seed=42)

    # ── Gripper config ──────────────────────────────────────────
    grip_quat = np.array([0.707107, 0.707107, 0, 0])

    # 90° rotation about world z = quat (cos45, 0, 0, sin45)
    q_z90 = np.array([0.707107, 0, 0, 0.707107])
    goal_grip_quat = quat_mul(q_z90, grip_quat)  # [0.5, 0.5, 0.5, 0.5]

    start_xy = np.array([0.3, 0.0])
    goal_xy = np.array([0.3, 0.08])   # matches goal body in XML

    z_home = 0.15       # home height
    z_grasp = 0.057     # pad centres align with block centre
    z_lift = 0.12       # lift height
    OPEN, CLOSE = 0.04, 0.015

    # ── Phase schedule ──────────────────────────────────────────
    phases = [
        (0.3, "settle"),
        (0.5, "approach"),
        (0.3, "close"),
        (0.5, "lift"),
        (0.8, "reorient"),      # rotate 90° + translate to goal xy
        (0.5, "wind_light"),
        (0.5, "wind_strong"),
        (0.3, "descend"),
        (0.3, "open"),
        (0.4, "retreat"),
    ]
    phase_starts = []
    t_acc = 0
    for dur, name in phases:
        phase_starts.append((t_acc, t_acc + dur, name))
        t_acc += dur
    T_total = t_acc

    # ── Renderer ────────────────────────────────────────────────
    W, H = 960, 720
    renderer = mujoco.Renderer(m, height=H, width=W)

    vopt = mujoco.MjvOption()
    vopt.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = True
    vopt.flags[mujoco.mjtVisFlag.mjVIS_CONTACTFORCE] = True

    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0.3, 0.04, 0.06]
    cam.distance = 0.40
    cam.azimuth = -50
    cam.elevation = -25

    dt = m.opt.timestep
    N_steps = int(T_total / dt)
    fps = 30
    frame_every = int(1.0 / (fps * dt))

    # Init: gripper at home, fingers open
    d.mocap_pos[0] = [start_xy[0], start_xy[1], z_home]
    d.mocap_quat[0] = grip_quat
    d.ctrl[0] = OPEN
    for _ in range(200):
        mujoco.mj_step(m, d)

    frames = []
    cur_xy = start_xy.copy()
    cur_quat = grip_quat.copy()

    for step in range(N_steps):
        t = step * dt

        phase_name, phase_frac = "settle", 0.0
        for t0, t1, name in phase_starts:
            if t0 <= t < t1:
                phase_name = name
                phase_frac = (t - t0) / (t1 - t0)
                break

        if phase_name == "settle":
            tz, finger = z_home, OPEN
            cur_xy = start_xy
            cur_quat = grip_quat
        elif phase_name == "approach":
            tz, finger = lerp(z_home, z_grasp, phase_frac), OPEN
            cur_xy = start_xy
            cur_quat = grip_quat
        elif phase_name == "close":
            tz, finger = z_grasp, lerp(OPEN, CLOSE, phase_frac)
            cur_xy = start_xy
            cur_quat = grip_quat
        elif phase_name == "lift":
            tz, finger = lerp(z_grasp, z_lift, phase_frac), CLOSE
            cur_xy = start_xy
            cur_quat = grip_quat
        elif phase_name == "reorient":
            tz, finger = z_lift, CLOSE
            cur_xy = lerp(start_xy, goal_xy, phase_frac)
            cur_quat = quat_slerp(grip_quat, goal_grip_quat, phase_frac)
        elif phase_name == "wind_light":
            tz, finger = z_lift, CLOSE
            cur_xy = goal_xy
            cur_quat = goal_grip_quat
            wind.F_max = 0.2 * cube_mass * 9.81
        elif phase_name == "wind_strong":
            tz, finger = z_lift, CLOSE
            cur_xy = goal_xy
            cur_quat = goal_grip_quat
            wind.F_max = 0.8 * cube_mass * 9.81
        elif phase_name == "descend":
            tz, finger = lerp(z_lift, z_grasp, phase_frac), CLOSE
            cur_xy = goal_xy
            cur_quat = goal_grip_quat
            wind.F_max = 0.0
        elif phase_name == "open":
            tz, finger = z_grasp, lerp(CLOSE, OPEN, phase_frac)
            cur_xy = goal_xy
            cur_quat = goal_grip_quat
        elif phase_name == "retreat":
            tz, finger = lerp(z_grasp, z_home, phase_frac), OPEN
            cur_xy = goal_xy
            cur_quat = goal_grip_quat

        d.mocap_pos[0] = [cur_xy[0], cur_xy[1], tz]
        d.mocap_quat[0] = cur_quat
        d.ctrl[0] = finger

        if wind.F_max > 0:
            wind.apply(d, [cube_id])
        else:
            wind.clear(d, [cube_id])

        mujoco.mj_step(m, d)

        if step % frame_every == 0:
            renderer.update_scene(d, camera=cam, scene_option=vopt)
            img = renderer.render().copy()
            frames.append(img)

    renderer.close()
    print(f"Captured {len(frames)} frames at {fps} fps")

    # Write MP4 via imageio
    outpath = str(ROOT / 'assets' / 'visual_reads' / 'pick_place_contacts.mp4')
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    iio.imwrite(outpath, np.stack(frames), fps=fps,
                codec='libx264', plugin='pyav')
    print(f"Video saved to {outpath}")

    # Also save keyframe snapshots
    _save_keyframes(m, cube_id, cam, vopt)


def _ramp_mocap(m, d, target_pos, target_quat, steps=400):
    """Gradually ramp the mocap target to avoid impulse on the weld."""
    start_pos = d.mocap_pos[0].copy()
    start_quat = d.mocap_quat[0].copy()
    for i in range(steps):
        t = i / steps
        d.mocap_pos[0] = lerp(start_pos, np.array(target_pos), t)
        d.mocap_quat[0] = quat_slerp(start_quat, np.array(target_quat), t)
        mujoco.mj_step(m, d)
    # Settle at target
    d.mocap_pos[0] = target_pos
    d.mocap_quat[0] = target_quat
    for _ in range(200):
        mujoco.mj_step(m, d)


def _save_keyframes(m, cube_id, cam, vopt):
    """Save 5 keyframe images showing the pick-rotate-place sequence."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    W, H = 640, 480
    renderer = mujoco.Renderer(m, height=H, width=W)

    grip_quat = np.array([0.707107, 0.707107, 0, 0])
    q_z90 = np.array([0.707107, 0, 0, 0.707107])
    goal_grip_quat = quat_mul(q_z90, grip_quat)

    z_grasp = 0.057
    z_lift = 0.12

    snapshots, labels = [], []

    # 1: Approach — stabilize at home
    d = mujoco.MjData(m)
    d.mocap_pos[0] = [0.3, 0, 0.15]
    d.mocap_quat[0] = grip_quat
    d.ctrl[0] = 0.04
    for _ in range(1000):
        mujoco.mj_step(m, d)
    renderer.update_scene(d, camera=cam, scene_option=vopt)
    snapshots.append(renderer.render().copy())
    labels.append('1. Approach')

    # 2: Grasp — ramp down, then close
    _ramp_mocap(m, d, [0.3, 0, z_grasp], grip_quat, steps=400)
    d.ctrl[0] = 0.010
    for _ in range(500):
        mujoco.mj_step(m, d)
    renderer.update_scene(d, camera=cam, scene_option=vopt)
    snapshots.append(renderer.render().copy())
    labels.append('2. Grasp')

    # 3: Lift — ramp up
    _ramp_mocap(m, d, [0.3, 0, z_lift], grip_quat, steps=500)
    renderer.update_scene(d, camera=cam, scene_option=vopt)
    snapshots.append(renderer.render().copy())
    labels.append('3. Lift')

    # 4: Reorient — ramp position + rotation gradually
    _ramp_mocap(m, d, [0.3, 0.08, z_lift], goal_grip_quat, steps=600)
    renderer.update_scene(d, camera=cam, scene_option=vopt)
    snapshots.append(renderer.render().copy())
    labels.append('4. Reorient\n(90\u00b0 + translate)')

    # 5: Place at goal — ramp down, then open
    _ramp_mocap(m, d, [0.3, 0.08, z_grasp], goal_grip_quat, steps=400)
    d.ctrl[0] = 0.04  # open
    for _ in range(300):
        mujoco.mj_step(m, d)
    renderer.update_scene(d, camera=cam, scene_option=vopt)
    snapshots.append(renderer.render().copy())
    labels.append('5. Place at goal')

    renderer.close()

    fig, axes = plt.subplots(1, 5, figsize=(20, 4))
    for ax, img, label in zip(axes, snapshots, labels):
        ax.imshow(img)
        ax.set_title(label, fontsize=11, fontweight='bold')
        ax.axis('off')

    plt.tight_layout()
    outpath = str(ROOT / 'assets' / 'visual_reads' / 'pick_place_contacts_keyframes.png')
    plt.savefig(outpath, dpi=150)
    print(f"Keyframes saved to {outpath}")


if __name__ == "__main__":
    main()
