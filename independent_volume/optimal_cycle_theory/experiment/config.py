"""Hyperparameters and robot model configuration for the quadruped experiment."""

import jax.numpy as jnp

# ── Robot model (Unitree Go1-like centroidal) ──
ROBOT = {
    "mass": 15.206,  # kg (from go2.xml: base 6.921 + 4×hip 0.678 + 4×thigh 1.152 + 4×calf 0.241)
    "inertia": jnp.array([0.107, 0.098, 0.024]),  # Ixx, Iyy, Izz (from go2.xml base diaginertia)
    "foot_positions": jnp.array([
        [ 0.1934,  0.142, -0.265],   # FL (FK: hip + lateral offset from go2.xml)
        [ 0.1934, -0.142, -0.265],   # FR
        [-0.1934,  0.142, -0.265],   # RL
        [-0.1934, -0.142, -0.265],   # RR
    ]),
    "standing_height": 0.27,  # m (from go2.xml keyframe home qpos z)
    "stride_period": 0.5,    # s (2 Hz stride frequency)
    "stride_frequency": 2.0, # Hz
    "duty_factor": 0.5,      # fraction in stance
    "swing_height": 0.08,    # m
    "eta": 5.0,              # viscous ground friction [N·s/m per stance foot]
    "k_raibert": 0.3,        # Raibert foot placement gain (dimensionless)
    "target_velocity_x": 1.0,  # desired forward velocity for Raibert correction [m/s]
    "ground_normal": jnp.array([0.0, 0.0, 1.0]),  # default surface normal (flat ground)
}

# ── State/control dimensions ──
NX = 13  # px,py,pz, vx,vy,vz, phi_x,phi_y,phi_z, wx,wy,wz, phase
NU = 12  # f0_x,f0_y,f0_z, f1_x,..., f3_z (4 feet × 3 force components)

# ── OCP (inner solver) ──
OCP = {
    "horizon": 50,
    "dt": 0.01,                     # 100 Hz discretization
    "target_velocity": jnp.array([1.0, 0.0, 0.0]),  # 1 m/s forward
    "Q_diag": jnp.concatenate([
        1.0 * jnp.ones(3),    # position tracking
        0.1 * jnp.ones(3),    # velocity tracking
        0.5 * jnp.ones(3),    # orientation tracking
        0.01 * jnp.ones(3),   # angular velocity
        jnp.zeros(1),         # phase (free)
    ]),
    "R_diag": 1e-4 * jnp.ones(NU),  # control regularization
    "Q_f_diag": jnp.concatenate([
        10.0 * jnp.ones(3),
        1.0 * jnp.ones(3),
        5.0 * jnp.ones(3),
        0.1 * jnp.ones(3),
        jnp.zeros(1),
    ]),
    "force_limit": 100.0,  # N per foot
    "w_slip": 0.1,         # contact no-slip weight (integral constraint)
}

# ── MPPI (outer loop) ──
MPPI = {
    "N_samples": 128,
    "nu_init": 2.0,             # student-t df (broad exploration)
    "epsilon_init": 1.0,        # initial temperature
    "alpha_up": 1.1,            # multiplicative ε increase (underexploring)
    "alpha_down": 0.95,         # multiplicative ε decrease (overexploring)
    "compression_rate": 0.97,   # entropy bound compression per iteration
    "epsilon_min": 1e-4,
    "epsilon_max": 100.0,
    "h_min": 1e-4,              # barrier floor (prevent division by zero)
    "barrier_delta": 0.01,      # sigmoid sharpness for force_scale
    "n_knots": 6,               # B-spline control points per foot per stride
    "delta_kl": 0.5,            # KL trust region radius on T^3
}

# ── Height and orientation constraints ──
CONSTRAINTS = {
    "z_target": 0.27,      # standing height (m, from go2.xml keyframe)
    "z_min": 0.13,         # min CoM height (m)
    "z_max": 0.41,         # max CoM height (m)
    "w_height": 2.0,       # quadratic height tracking weight
    "w_height_barrier": 1.0,  # log-barrier weight (× ε)
    "phi_max": 0.524,      # max pitch/roll ~30° (rad)
    "w_ori_barrier": 1.0,  # orientation log-barrier weight (× ε)
    "w_joint_barrier": 0.1, # joint-limit log-barrier weight (× ε)
}

# ── MuJoCo simulation ──
MUJOCO = {
    "timestep": 0.002,         # 500 Hz simulation (5× finer than OCP)
    "integrator": "implicit",  # implicit Euler
    "solver": "Newton",        # Newton contact solver
    "niter": 50,               # high iteration threshold for contact solver
    "tolerance": 1e-10,        # tight convergence for contact forces
}
