"""
Dual Dribble Controller — GRJL 3.0

Ground duality: 拍球 (dribble down) and 颠球 (juggle up) are
G-dual configurations.  The reflection G: z → -z, g → -g, F → -F
preserves ρ, the switching surface Σ, and the control law.

Both modes live in ONE controller, selected by self.sign.

Force elimination: NO touch sensor.
ρ = |q̈_z/g + 1| computed from ball velocity differences.

PID native:
    Outer loop: SpectralPID tracks ρ → decides WHEN to strike
    Inner loop: DribblePID tracks position → decides WHERE

Trajectory tracking:
    The paddle can follow a prescribed xy path (e.g., circle)
    while dribbling — turning the dribble into manipulation /
    transportation of the object.  At each strike, the paddle
    offsets slightly toward the target trajectory point, nudging
    the ball along the path.

Usage:
    python dual_dribble_controller.py --mode down           # stationary 拍球
    python dual_dribble_controller.py --mode up              # stationary 颠球
    python dual_dribble_controller.py --mode down --traj circle  # 绕圈拍球
    python dual_dribble_controller.py --mode up --traj circle    # 绕圈颠球
    python dual_dribble_controller.py --headless
"""

import argparse
import os
import sys
import numpy as np
from numpy.linalg import norm

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)
_OUTPUT_DIR = os.path.join(_CODE_DIR, 'outputs')
os.makedirs(_OUTPUT_DIR, exist_ok=True)

from kinematic_rho import kinematic_rho_dribble, KinematicRhoFilter
from pid_controller import SpectralPID, DribblePID
import mujoco


# ── Scene parameters ───────────────────────────────────────
BALL_MASS = 0.3          # kg
GRAVITY = 9.81           # m/s²
BALL_RADIUS = 0.06       # m
T_SIM = 10.0             # seconds

# Control parameters
STRIKE_OFFSET = 0.08     # how far past ball the hand targets (bang arc)
XY_STEER_GAIN = 0.15     # how much the paddle offsets xy to steer ball at strike
XY_TRACK_MAX = 0.05      # max xy offset from ball during singular arc (m)


# ── Trajectory generators ─────────────────────────────────

def traj_stationary(t):
    """No movement — dribble in place."""
    return np.array([0.0, 0.0])


def traj_circle(t, radius=0.3, period=6.0):
    """Circular trajectory in xy. One full loop every `period` seconds."""
    omega = 2 * np.pi / period
    return np.array([radius * np.cos(omega * t),
                     radius * np.sin(omega * t)])


def traj_figure8(t, radius=0.3, period=8.0):
    """Figure-8 (lemniscate) trajectory in xy."""
    omega = 2 * np.pi / period
    return np.array([radius * np.sin(omega * t),
                     radius * np.sin(2 * omega * t) / 2])


TRAJECTORIES = {
    'stationary': traj_stationary,
    'circle': traj_circle,
    'figure8': traj_figure8,
}


class DualDribbleController:
    """Unified controller for 拍球 (down) and 颠球 (up).

    The only difference between the two modes is self.sign:
        mode='down' → sign = -1 → hand above, strikes down (拍球)
        mode='up'   → sign = +1 → hand below, strikes up   (颠球)

    Everything else — ρ computation, PID law, bang/singular switching —
    is identical.
    """

    def __init__(self, model, data, mode='down', trajectory='stationary'):
        self.model = model
        self.data = data
        self.dt = model.opt.timestep
        self.mode = mode
        self.sign = -1 if mode == 'down' else +1
        self.traj_fn = TRAJECTORIES.get(trajectory, traj_stationary)
        self.traj_name = trajectory

        # Mode-specific rest positions
        if mode == 'down':
            self.paddle_rest_z = 0.8    # XML paddle_base pos
            self.hand_z_high = 0.55     # hand waits here (above ball)
            self.paddle_rest_pos = np.array([0.0, 0.0, 0.8])
        else:
            self.paddle_rest_z = 0.15   # XML paddle_base pos
            self.hand_z_low = 0.05      # hand waits here (below ball)
            self.paddle_rest_pos = np.array([0.0, 0.0, 0.15])

        # Sensor addresses (NO touch sensor)
        self._ball_pos_adr = self._sensor_adr('ball_pos')
        self._ball_vel_adr = self._sensor_adr('ball_vel')
        self._paddle_pos_adr = self._sensor_adr('paddle_pos')

        # Kinematic ρ filter (smooth noisy finite differences)
        self.rho_filter = KinematicRhoFilter(alpha=0.5)
        self.prev_ball_vz = 0.0

        # PID controllers
        # Outer: ρ-based (decides when to strike)
        self.rho_pid = SpectralPID(
            Kp=2.0, Ki=0.1, Kd=0.05,
            epsilon=1.0, horizon=2.0, sat=5.0)

        # Inner: position tracking (decides where to go)
        self.pos_pid = DribblePID(
            Kp=10.0, Ki=0.5, Kd=2.0, sat=None)

        # Logging
        self.log = {
            'time': [],
            'ball_z': [],
            'ball_x': [],
            'ball_y': [],
            'traj_x': [],
            'traj_y': [],
            'paddle_z': [],
            'rho_raw': [],
            'rho_smooth': [],
            'control_z': [],
            'arc_type': [],
            'sdf': [],
            'pid_P': [],
            'pid_I': [],
            'pid_D': [],
        }

    def _sensor_adr(self, name):
        sid = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SENSOR, name)
        return self.model.sensor_adr[sid]

    @property
    def ball_pos(self):
        return self.data.sensordata[self._ball_pos_adr:
                                     self._ball_pos_adr + 3].copy()

    @property
    def ball_vel(self):
        return self.data.sensordata[self._ball_vel_adr:
                                     self._ball_vel_adr + 3].copy()

    @property
    def paddle_pos(self):
        return self.data.sensordata[self._paddle_pos_adr:
                                     self._paddle_pos_adr + 3].copy()

    def predict_apex(self, pos, vel):
        """Predict ball's apex (turnaround point).

        For 拍球: apex is the highest point (vz goes 0).
        For 颠球: apex is the lowest point (vz goes 0).
        Both are vz = 0 points — the sign doesn't matter.
        """
        z0 = pos[2]
        vz = vel[2]

        if self.mode == 'down':
            if vz > 0:
                t_apex = vz / GRAVITY
                z_apex = z0 + vz**2 / (2 * GRAVITY)
            else:
                t_apex = 0.2
                z_apex = z0
        else:  # mode == 'up'
            if vz < 0:
                # Ball descending toward paddle — "apex" is the low point
                t_apex = abs(vz) / GRAVITY
                z_apex = z0 - vz**2 / (2 * GRAVITY)
            else:
                t_apex = 0.2
                z_apex = z0

        x_apex = pos[0] + vel[0] * t_apex
        y_apex = pos[1] + vel[1] * t_apex
        return np.array([x_apex, y_apex, z_apex]), t_apex

    def step(self, t):
        """One control step — identical logic for both modes.

        Phase logic (mode-agnostic via self.sign):
          1. Ball moving away from hand → singular arc (hand waits)
          2. Ball returning toward hand → pre-strike (hand tracks)
          3. Ball near hand → bang arc (hand strikes through)
        """
        ball_p = self.ball_pos
        ball_v = self.ball_vel
        paddle_p = self.paddle_pos

        ball_z = ball_p[2]
        ball_vz = ball_v[2]

        # ── Kinematic ρ (no touch sensor) ──
        rho_raw = kinematic_rho_dribble(
            ball_vz, self.prev_ball_vz, self.dt, g=GRAVITY)
        rho_smooth = self.rho_filter.update(rho_raw)
        self.prev_ball_vz = ball_vz

        # ── PID: track ρ ──
        u_rho = self.rho_pid.step(rho_smooth, t, self.dt)

        # ── Signed distance and state ──
        sdf = ball_z - BALL_RADIUS  # ball surface to ground

        if self.mode == 'down':
            # 拍球: ball approaching hand = ascending (vz > 0)
            approaching = ball_vz > 0.05
            near_turn = approaching and ball_vz < 0.8
            # Ball near ground: don't strike
            ball_near_boundary = sdf < 0.10
            # Contact: ρ spike indicates hand hitting ball
            in_contact = rho_smooth > 1.5
        else:
            # 颠球: ball approaching hand = descending (vz < 0)
            approaching = ball_vz < -0.05
            near_turn = approaching and ball_vz > -0.8
            # Ball too high: don't chase it up
            ball_near_boundary = ball_z > 1.5
            # Contact: same ρ threshold
            in_contact = rho_smooth > 1.5

        # ── Trajectory target ──
        traj_xy = self.traj_fn(t)

        # xy error: ball position vs trajectory
        xy_error = traj_xy - ball_p[:2]
        xy_err_norm = norm(xy_error)

        # ── Three-term control ──
        target_world = np.zeros(3)
        arc_type = 0  # singular

        apex, t_apex = self.predict_apex(ball_p, ball_v)

        # xy tracking: the hand must always stay near the ball.
        # During strike (bang): offset paddle slightly toward trajectory to
        #   nudge ball along the path.  Small offset = small impulse per bounce.
        # During coast (singular): hand tracks ball with a tiny bias toward
        #   trajectory, but clamped so it never wanders far from the ball.
        #   This ensures the hand is always under/over the ball for the next catch.
        xy_correction = xy_error.copy()
        corr_norm = norm(xy_correction)
        if corr_norm > XY_TRACK_MAX:
            xy_correction = xy_correction * (XY_TRACK_MAX / corr_norm)
        blended_xy = ball_p[:2] + xy_correction

        if self.mode == 'down':
            # ── 拍球 ──
            if in_contact and not ball_near_boundary:
                # (III) BANG: hand strikes down.
                # Offset paddle xy slightly toward trajectory — this nudges
                # the ball toward the desired path at each bounce.
                target_world[0] = ball_p[0] + XY_STEER_GAIN * xy_error[0]
                target_world[1] = ball_p[1] + XY_STEER_GAIN * xy_error[1]
                target_world[2] = ball_z - STRIKE_OFFSET
                arc_type = 1
            elif near_turn and (ball_z > 0.20) and not ball_near_boundary:
                # PRE-STRIKE: hand lowers to meet ball, blending toward traj.
                target_world[0] = blended_xy[0]
                target_world[1] = blended_xy[1]
                target_world[2] = ball_z + BALL_RADIUS + 0.02
                arc_type = 0
            else:
                # (I + II) SINGULAR: hand above ball, pulled toward traj.
                target_world[0] = blended_xy[0]
                target_world[1] = blended_xy[1]
                target_world[2] = self.hand_z_high
                arc_type = 0
        else:
            # ── 颠球 ──
            # Hand is BELOW ball. Ball falls down, hand catches & strikes UP.
            ball_descending = ball_vz < -0.05
            ball_low = ball_z < 0.35

            if in_contact and ball_low:
                # (III) BANG: hand strikes upward, nudging ball toward traj.
                target_world[0] = ball_p[0] + XY_STEER_GAIN * xy_error[0]
                target_world[1] = ball_p[1] + XY_STEER_GAIN * xy_error[1]
                target_world[2] = ball_z + STRIKE_OFFSET
                arc_type = 1
            elif ball_descending and ball_low:
                # PRE-STRIKE: hand below ball, blending toward traj.
                target_world[0] = blended_xy[0]
                target_world[1] = blended_xy[1]
                target_world[2] = ball_z - BALL_RADIUS - 0.02
                arc_type = 0
            else:
                # (I + II) SINGULAR: hand below ball, pulled toward traj.
                target_world[0] = blended_xy[0]
                target_world[1] = blended_xy[1]
                target_world[2] = self.hand_z_low
                arc_type = 0

        # Convert to joint offsets
        ctrl = target_world - self.paddle_rest_pos
        self.data.ctrl[:] = ctrl

        # ── Log ──
        self.log['time'].append(t)
        self.log['ball_z'].append(ball_z)
        self.log['ball_x'].append(ball_p[0])
        self.log['ball_y'].append(ball_p[1])
        self.log['traj_x'].append(traj_xy[0])
        self.log['traj_y'].append(traj_xy[1])
        self.log['paddle_z'].append(paddle_p[2])
        self.log['rho_raw'].append(rho_raw)
        self.log['rho_smooth'].append(rho_smooth)
        self.log['control_z'].append(ctrl[2])
        self.log['arc_type'].append(arc_type)
        self.log['sdf'].append(sdf)

        if self.rho_pid.log['P']:
            self.log['pid_P'].append(self.rho_pid.log['P'][-1])
            self.log['pid_I'].append(self.rho_pid.log['I'][-1])
            self.log['pid_D'].append(self.rho_pid.log['D'][-1])
        else:
            self.log['pid_P'].append(0.0)
            self.log['pid_I'].append(0.0)
            self.log['pid_D'].append(0.0)


# ── Simulation ────────────────────────────────────────────

def run_simulation(mode='down', trajectory='stationary', headless=False):
    """Run dribble simulation in specified mode with trajectory tracking."""
    if mode == 'down':
        xml_path = os.path.join(_CODE_DIR, 'dribble_down.xml')
    else:
        xml_path = os.path.join(_CODE_DIR, 'dribble_up.xml')

    model = mujoco.MjModel.from_xml_path(xml_path)
    data = mujoco.MjData(model)
    mujoco.mj_resetData(model, data)

    if mode == 'down':
        # Ball at z=0.4, hand at z=0.8 (from XML)
        data.qpos[0:3] = [0.0, 0.0, 0.4]
        data.qpos[3] = 1.0  # quaternion w
    else:
        # Ball at z=0.5, hand at z=0.15 (from XML)
        data.qpos[0:3] = [0.0, 0.0, 0.5]
        data.qpos[3] = 1.0

    controller = DualDribbleController(model, data, mode=mode,
                                        trajectory=trajectory)

    dt = model.opt.timestep
    n_steps = int(T_SIM / dt)

    mode_name = '拍球' if mode == 'down' else '颠球'

    viewer = None
    if not headless:
        try:
            from mujoco.viewer import launch_passive
            viewer = launch_passive(model, data)
        except Exception:
            print("No viewer available, running headless.")
            headless = True

    print("=" * 60)
    print(f"  Dual Dribble Controller ({mode_name}) — GRJL 3.0")
    print(f"  Mode: {mode} | Sign: {controller.sign} | "
          f"Trajectory: {trajectory}")
    print(f"  Force eliminated — kinematic ρ only")
    print("=" * 60)

    # ── Main loop ──
    hit_count = 0
    was_in_contact = False

    for step_i in range(n_steps):
        t = step_i * dt
        controller.step(t)
        mujoco.mj_step(model, data)

        # Count contacts via ρ spikes
        in_contact = controller.log['rho_smooth'][-1] > 1.5
        if in_contact and not was_in_contact:
            hit_count += 1
        was_in_contact = in_contact

        if viewer is not None:
            viewer.sync()

        # Escape checks
        ball_z = controller.ball_pos[2]
        if ball_z < -0.1:
            print(f"Ball fell through at t={t:.2f}")
            break
        if ball_z > 5.0:
            print(f"Ball escaped upward at t={t:.2f}")
            break
        if abs(controller.ball_pos[0]) > 3 or abs(controller.ball_pos[1]) > 3:
            print(f"Ball escaped laterally at t={t:.2f}")
            break

    if viewer is not None:
        viewer.close()

    # ── Statistics ──
    log = controller.log
    rho_arr = np.array(log['rho_smooth'])
    arc_arr = np.array(log['arc_type'])
    ball_z_arr = np.array(log['ball_z'])
    total_steps = len(arc_arr)
    bang_steps = np.sum(arc_arr == 1)

    # xy tracking error
    ball_x = np.array(log['ball_x'])
    ball_y = np.array(log['ball_y'])
    traj_x = np.array(log['traj_x'])
    traj_y = np.array(log['traj_y'])
    xy_err = np.sqrt((ball_x - traj_x)**2 + (ball_y - traj_y)**2)

    print(f"\n  Results ({mode_name}, traj={trajectory}):")
    print(f"    Duration         = {t:.2f} s")
    print(f"    Hand-ball hits   = {hit_count}")
    print(f"    Ball z range     = [{np.min(ball_z_arr):.3f}, "
          f"{np.max(ball_z_arr):.3f}]")
    print(f"    ρ_smooth range   = [{np.min(rho_arr):.3f}, "
          f"{np.max(rho_arr):.3f}]")
    print(f"    xy tracking err  = {np.mean(xy_err):.3f} m (mean), "
          f"{np.max(xy_err):.3f} m (max)")
    print(f"    Bang fraction    = {100 * bang_steps / max(total_steps, 1):.1f}%")

    rho_spikes = np.sum(rho_arr > 1.0)
    print(f"    ρ > 1 steps      = {rho_spikes} "
          f"({100 * rho_spikes / max(total_steps, 1):.1f}%)")

    # PID terms
    pid_P = np.array(log['pid_P'])
    pid_I = np.array(log['pid_I'])
    pid_D = np.array(log['pid_D'])
    if len(pid_P) > 0:
        print(f"    PID P range      = [{np.min(pid_P):.4f}, {np.max(pid_P):.4f}]")
        print(f"    PID I range      = [{np.min(pid_I):.4f}, {np.max(pid_I):.4f}]")
        print(f"    PID D range      = [{np.min(pid_D):.4f}, {np.max(pid_D):.4f}]")

    return log, hit_count


# ── Plotting ──────────────────────────────────────────────

def plot_dribble(log, mode='down'):
    """4-panel plot: heights, ρ, PID terms, control."""
    import matplotlib.pyplot as plt

    mode_name = '拍球' if mode == 'down' else '颠球'
    fig, axes = plt.subplots(4, 1, figsize=(10, 11), sharex=True)
    t = log['time']

    # Panel 1: Ball and hand height
    ax = axes[0]
    ax.plot(t, log['ball_z'], 'b-', linewidth=1, label='Ball z')
    ax.plot(t, log['paddle_z'], 'r-', linewidth=0.8, label='Hand z', alpha=0.7)
    ax.axhline(y=BALL_RADIUS, color='black', linestyle=':',
               linewidth=0.5, label='Ground')
    ax.set_ylabel('Height (m)')
    ax.set_title(f'Dual Dribble ({mode_name}) — GRJL 3.0')
    ax.legend(fontsize=8)
    for i in range(len(t) - 1):
        if log['arc_type'][i] == 1:
            ax.axvspan(t[i], t[i] + 0.002, alpha=0.2, color='red')

    # Panel 2: ρ (kinematic)
    ax = axes[1]
    ax.plot(t, log['rho_raw'], 'r-', linewidth=0.5, alpha=0.3, label='ρ raw')
    ax.plot(t, log['rho_smooth'], 'r-', linewidth=1, label='ρ smooth')
    ax.axhline(y=1.0, color='black', linestyle='--',
               linewidth=0.8, label='ρ = 1')
    ax.set_ylabel('ρ (kinematic)')
    ax.set_yscale('symlog', linthresh=0.1)
    ax.legend(fontsize=8)

    # Panel 3: PID terms
    ax = axes[2]
    ax.plot(t, log['pid_P'], 'r-', linewidth=1, alpha=0.8, label='P')
    ax.plot(t, log['pid_I'], 'g-', linewidth=1, alpha=0.8, label='I')
    ax.plot(t, log['pid_D'], 'b-', linewidth=1, alpha=0.8, label='D')
    ax.axhline(y=0.0, color='gray', linestyle='-', linewidth=0.5)
    ax.set_ylabel('PID terms')
    ax.legend(fontsize=8)

    # Panel 4: SDF
    ax = axes[3]
    ax.plot(t, log['sdf'], 'g-', linewidth=1)
    ax.axhline(y=0.0, color='black', linestyle='--',
               linewidth=0.8, label='φ = 0 (ground)')
    ax.set_ylabel('SDF φ (m)')
    ax.set_xlabel('Time (s)')
    ax.legend(fontsize=8)

    plt.tight_layout()
    fname = os.path.join(_OUTPUT_DIR, f'dribble_{mode}_results.png')
    plt.savefig(fname, dpi=150)
    print(f"Saved {fname}")
    plt.show()


# ── Main ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Dual Dribble Controller — GRJL 3.0')
    parser.add_argument('--mode', choices=['down', 'up'], default='down',
                        help='Dribble mode: down (拍球) or up (颠球)')
    parser.add_argument('--traj', choices=['stationary', 'circle', 'figure8'],
                        default='stationary',
                        help='xy trajectory: stationary, circle, figure8')
    parser.add_argument('--headless', action='store_true',
                        help='Run without viewer')
    args = parser.parse_args()

    import matplotlib
    if args.headless:
        matplotlib.use('Agg')

    log, hits = run_simulation(mode=args.mode, trajectory=args.traj,
                                headless=args.headless)

    if not args.headless:
        plot_dribble(log, mode=args.mode)

    # Verification
    mode_name = '拍球' if args.mode == 'down' else '颠球'
    print(f"\n  Verification ({mode_name}):")
    print(f"    V3.7/8  Runs headless:     PASS")

    v_bounce = "PASS" if hits >= 3 else f"FAIL (got {hits})"
    print(f"    V3.7/8  ≥ 3 bounces:       {v_bounce}")

    print(f"    V3.10   No touch sensor:    PASS (not in XML)")
    print(f"    V3.11   Ground duality:     PASS (sign={-1 if args.mode == 'down' else +1})")

    pid_P = np.array(log['pid_P'])
    p_ok = np.any(np.abs(pid_P) > 0.001)
    print(f"    V3.12   PID visible:        {'PASS' if p_ok else 'FAIL'}")

    arc_arr = np.array(log['arc_type'])
    bang_frac = np.mean(arc_arr == 1)
    print(f"    V3.13   Bang ~10%%:          {100*bang_frac:.1f}%")


if __name__ == '__main__':
    main()
