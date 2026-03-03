"""
Render MuJoCo videos for both 拍球 and 颠球 — GRJL 3.0

Produces:
    outputs/dribble_down.mp4          (拍球, stationary)
    outputs/dribble_up.mp4            (颠球, stationary)
    outputs/dribble_down_circle.mp4   (绕圈拍球)
    outputs/dribble_up_circle.mp4     (绕圈颠球)
"""

import os
import sys
import numpy as np
import mujoco
import imageio

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from dual_dribble_controller import DualDribbleController

OUTPUT_DIR = os.path.join(_CODE_DIR, 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

T_SIM = 10.0       # 10 seconds of video
FPS = 30
RENDER_W = 640
RENDER_H = 480


def render_mode(mode='down', trajectory='stationary'):
    """Render a single mode+trajectory to video."""
    mode_name = '拍球' if mode == 'down' else '颠球'
    suffix = f'_{trajectory}' if trajectory != 'stationary' else ''
    xml_name = f'dribble_{mode}.xml'
    xml_path = os.path.join(_CODE_DIR, xml_name)
    out_path = os.path.join(OUTPUT_DIR, f'dribble_{mode}{suffix}.mp4')

    print(f"\n  Rendering {mode_name} ({mode}, traj={trajectory})...")

    model = mujoco.MjModel.from_xml_path(xml_path)
    data = mujoco.MjData(model)
    mujoco.mj_resetData(model, data)

    # Initial conditions
    if mode == 'down':
        data.qpos[0:3] = [0.0, 0.0, 0.4]
        data.qpos[3] = 1.0
    else:
        data.qpos[0:3] = [0.0, 0.0, 0.5]
        data.qpos[3] = 1.0

    # Controller (same one used in headless testing)
    controller = DualDribbleController(model, data, mode=mode,
                                        trajectory=trajectory)

    # Renderer
    renderer = mujoco.Renderer(model, RENDER_H, RENDER_W)

    # Camera — for circle trajectories, pull back and look from above
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    if trajectory != 'stationary':
        camera.lookat[:] = [0.0, 0.0, 0.2]
        camera.distance = 2.0
        camera.elevation = -35
        camera.azimuth = 135
    else:
        camera.lookat[:] = [0.0, 0.0, 0.3]
        camera.distance = 1.5
        camera.elevation = -20
        camera.azimuth = 135

    dt = model.opt.timestep
    n_steps = int(T_SIM / dt)
    render_every = max(1, int(1.0 / (FPS * dt)))

    frames = []
    hit_count = 0
    was_contact = False

    for step_i in range(n_steps):
        t = step_i * dt
        controller.step(t)
        mujoco.mj_step(model, data)

        # Count contacts via ρ spikes
        rho = controller.log['rho_smooth'][-1]
        in_contact = rho > 1.5
        if in_contact and not was_contact:
            hit_count += 1
        was_contact = in_contact

        # Render frame
        if step_i % render_every == 0:
            renderer.update_scene(data, camera)
            frame = renderer.render()
            frames.append(frame)

        # Escape check
        ball_z = controller.ball_pos[2]
        ball_p = controller.ball_pos
        if ball_z < -0.5 or ball_z > 5.0:
            print(f"    Ball escaped at t={t:.2f}")
            break
        if abs(ball_p[0]) > 3 or abs(ball_p[1]) > 3:
            print(f"    Ball escaped laterally at t={t:.2f}")
            break

    renderer.close()

    # Write video
    imageio.mimwrite(out_path, frames, fps=FPS, quality=8)
    print(f"  Saved {out_path}")
    print(f"    Duration: {len(frames)/FPS:.1f}s, {len(frames)} frames")
    print(f"    Hits: {hit_count}")

    return out_path


def main():
    print("=" * 60)
    print("  GRJL 3.0 — Video Rendering")
    print("  顿开金绳，扯断玉锁")
    print("=" * 60)

    paths = []

    # Stationary dribbles
    paths.append(render_mode('down', 'stationary'))
    paths.append(render_mode('up', 'stationary'))

    # Circle trajectory dribbles
    paths.append(render_mode('down', 'circle'))
    paths.append(render_mode('up', 'circle'))

    print(f"\n  Videos saved to:")
    for p in paths:
        print(f"    {p}")


if __name__ == '__main__':
    main()
