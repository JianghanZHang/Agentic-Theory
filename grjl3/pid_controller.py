"""
Spectral PID Controller — GRJL 3.0

The three-term control law (Theorem J.4):

    m* q̈* = (I) gravity + (II) least action + (III) spectral kick

maps to PID with error e(t) = λ₁(t) − ε:

    (I)   Gravity / drift           →  D term (Kd · ė)
    (II)  Least action / costate    →  I term (Ki · ∫e dt)
    (III) Spectral kick             →  P term (Kp · e)

The MPC rolling horizon is "the rolling of the rolling window":
the integral accumulates over a finite window H, and H itself
advances forward in time.
"""

import numpy as np


class SpectralPID:
    """PID controller where error = λ₁ − ε (spectral gap error).

    Maps the three-term decomposition to explicit PID gains.

    Parameters
    ----------
    Kp : float — proportional gain (spectral kick strength)
    Ki : float — integral gain (costate accumulation rate)
    Kd : float — derivative gain (drift damping)
    epsilon : float — target spectral gap λ₁ ≥ ε
    horizon : float or None — MPC rolling window length (seconds).
        None = infinite horizon (standard PID).
    sat : float — saturation limit for output (box constraint ū)
    """

    def __init__(self, Kp=5.0, Ki=0.5, Kd=1.0, epsilon=0.02,
                 horizon=None, sat=None):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.epsilon = epsilon
        self.horizon = horizon
        self.sat = sat

        # State
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_t = None

        # Logging
        self.log = {
            'P': [], 'I': [], 'D': [],
            'error': [], 'output': [],
        }

    def reset(self):
        """Reset controller state."""
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_t = None
        self.log = {k: [] for k in self.log}

    def step(self, lambda1, t, dt=None):
        """One PID step.

        Parameters
        ----------
        lambda1 : float — current Fiedler eigenvalue
        t : float — current time
        dt : float or None — timestep (auto-computed from t if None)

        Returns
        -------
        u_mag : float — control magnitude (scalar)
            Positive = increase spectral gap (apply spectral kick).
            Negative = spectral gap is large, relax control.
        """
        # Error: how far below the target
        e = lambda1 - self.epsilon

        # Timestep
        if dt is None:
            dt = (t - self.prev_t) if self.prev_t is not None else 0.002
        self.prev_t = t

        # ── I term: costate integral with rolling horizon ──
        self.integral += e * dt
        if self.horizon is not None and self.horizon > 0:
            # Exponential decay: old contributions fade
            decay = np.exp(-dt / self.horizon)
            self.integral *= decay

        # ── D term: rate of change of error ──
        if dt > 1e-12:
            de = (e - self.prev_error) / dt
        else:
            de = 0.0
        self.prev_error = e

        # ── PID output ──
        P = self.Kp * e
        I = self.Ki * self.integral
        D = self.Kd * de
        u_mag = P + I + D

        # Saturation (box constraint)
        if self.sat is not None:
            u_mag = np.clip(u_mag, -self.sat, self.sat)

        # Log
        self.log['P'].append(P)
        self.log['I'].append(I)
        self.log['D'].append(D)
        self.log['error'].append(e)
        self.log['output'].append(u_mag)

        return u_mag

    def arc_type(self):
        """Return current arc type based on last output.

        0 = singular (coasting, |u| < sat)
        1 = bang (saturated, |u| = sat)
        """
        if not self.log['output']:
            return 0
        u = self.log['output'][-1]
        if self.sat is not None and abs(abs(u) - self.sat) < 1e-6:
            return 1
        return 0


class DribblePID:
    """PID controller for the dribble, operating in position space.

    Error = desired_z − actual_z for the paddle.
    The three-term law maps to:
        P: position tracking (where should the hand be?)
        I: accumulated drift correction
        D: velocity damping

    This is the inner-loop PID. The outer loop (SpectralPID)
    decides WHEN to strike based on ρ. This one decides WHERE.
    """

    def __init__(self, Kp=10.0, Ki=0.5, Kd=2.0, sat=None):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.sat = sat

        self.integral = np.zeros(3)
        self.prev_error = np.zeros(3)

    def reset(self):
        self.integral = np.zeros(3)
        self.prev_error = np.zeros(3)

    def step(self, target, actual, dt):
        """Compute PID control for 3D position tracking.

        Parameters
        ----------
        target : (3,) — desired position
        actual : (3,) — current position
        dt : float — timestep

        Returns
        -------
        ctrl : (3,) — control output (position offset for actuator)
        """
        e = target - actual

        self.integral += e * dt
        if dt > 1e-12:
            de = (e - self.prev_error) / dt
        else:
            de = np.zeros(3)
        self.prev_error = e.copy()

        ctrl = self.Kp * e + self.Ki * self.integral + self.Kd * de

        if self.sat is not None:
            ctrl = np.clip(ctrl, -self.sat, self.sat)

        return ctrl


# ── Verification ─────────────────────────────────────────

def verify_pid():
    """Basic PID verification."""
    pid = SpectralPID(Kp=5.0, Ki=0.5, Kd=1.0, epsilon=0.02,
                      horizon=1.0, sat=10.0)

    # Simulate: λ₁ starts at 0.05, drops to 0.01, recovers
    dt = 0.01
    lambda1_series = np.concatenate([
        np.linspace(0.05, 0.01, 50),   # dropping
        np.linspace(0.01, 0.05, 50),   # recovering
    ])

    for i, lam in enumerate(lambda1_series):
        u = pid.step(lam, i * dt, dt)

    P_arr = np.array(pid.log['P'])
    I_arr = np.array(pid.log['I'])
    D_arr = np.array(pid.log['D'])

    # When λ₁ drops below ε, P should be negative (kick needed)
    assert np.any(P_arr < 0), "P term should go negative when λ₁ < ε"

    # I term should accumulate
    assert abs(I_arr[-1]) > abs(I_arr[0]), "I term should accumulate"

    # D term should respond to rate of change
    assert np.any(np.abs(D_arr) > 0.01), "D term should respond to changes"

    print("  SpectralPID verification: PASS")
    print(f"    P range: [{P_arr.min():.4f}, {P_arr.max():.4f}]")
    print(f"    I range: [{I_arr.min():.4f}, {I_arr.max():.4f}]")
    print(f"    D range: [{D_arr.min():.4f}, {D_arr.max():.4f}]")


if __name__ == '__main__':
    verify_pid()
