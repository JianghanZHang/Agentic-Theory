"""
B-Spline Trajectory Parameterisation (Step 2a)

Cubic B-spline q(t) = sum_i c_i B_i(t) reduces the infinite-dimensional
trajectory to R^{3m} control points with C^2 continuity for free.

Reference: threebody.tex eq 3b-ocp (line 117), OCP definition.
"""

import numpy as np
from scipy.interpolate import BSpline, make_interp_spline


class BSplineTrajectory:
    """Cubic B-spline trajectory in R^3 (or R^n).

    Parameters
    ----------
    control_points : (m, d) array
        Control points c_i in R^d.
    t_span : (2,) tuple
        Time interval [t0, tf].
    """

    def __init__(self, control_points, t_span=(0.0, 1.0)):
        self.control_points = np.asarray(control_points, dtype=float)
        self.m, self.d = self.control_points.shape
        self.t0, self.tf = t_span

        # Build uniform knot vector for cubic (k=3) B-spline
        n_internal = self.m - 4  # cubic needs m >= 4
        if n_internal < 0:
            raise ValueError(
                f"Need >= 4 control points for cubic B-spline, got {self.m}")
        knots_internal = np.linspace(self.t0, self.tf, n_internal + 2)[1:-1]
        # Clamped knot vector: k+1 repeats at ends
        self.knots = np.concatenate([
            np.full(4, self.t0),
            knots_internal,
            np.full(4, self.tf),
        ])
        self.k = 3  # cubic

        # One BSpline per dimension
        self._splines = [
            BSpline(self.knots, self.control_points[:, dim], self.k)
            for dim in range(self.d)
        ]

    def evaluate(self, t):
        """Evaluate q(t) -> (d,) or (len(t), d)."""
        t = np.asarray(t)
        scalar = t.ndim == 0
        t = np.atleast_1d(t)
        result = np.column_stack([s(t) for s in self._splines])
        return result[0] if scalar else result

    def derivative(self, t, order=1):
        """Evaluate d^n q / dt^n at t."""
        t = np.asarray(t)
        scalar = t.ndim == 0
        t = np.atleast_1d(t)
        result = np.column_stack([s.derivative(order)(t)
                                  for s in self._splines])
        return result[0] if scalar else result

    @classmethod
    def fit_from_waypoints(cls, waypoints, n_control=None, t_span=(0.0, 1.0)):
        """Fit a cubic B-spline through waypoints.

        Parameters
        ----------
        waypoints : (N, d) array
            Points to interpolate.
        n_control : int or None
            Number of control points. If None, uses N (interpolation).
        t_span : tuple
            Time interval.

        Returns
        -------
        BSplineTrajectory
        """
        waypoints = np.asarray(waypoints, dtype=float)
        N, d = waypoints.shape
        t0, tf = t_span
        t_data = np.linspace(t0, tf, N)

        if n_control is None or n_control >= N:
            # Exact interpolation
            spl = make_interp_spline(t_data, waypoints, k=3)
            return cls(spl.c, t_span)

        # Least-squares fit with fewer control points
        n_control = max(n_control, 4)
        knots_internal = np.linspace(t0, tf, n_control - 2)[1:-1]
        knots = np.concatenate([
            np.full(4, t0), knots_internal, np.full(4, tf)])

        # Build collocation matrix
        basis_splines = []
        for i in range(n_control):
            c = np.zeros(n_control)
            c[i] = 1.0
            basis_splines.append(BSpline(knots, c, 3))

        A = np.zeros((N, n_control))
        for i, bs in enumerate(basis_splines):
            A[:, i] = bs(t_data)

        # Solve for each dimension
        cp = np.zeros((n_control, d))
        for dim in range(d):
            cp[:, dim], _, _, _ = np.linalg.lstsq(
                A, waypoints[:, dim], rcond=None)

        return cls(cp, t_span)

    def cost_integral(self, n_quad=100):
        """Compute integral of ||q'(t)||^2 dt (kinetic energy proxy)."""
        t_quad = np.linspace(self.t0, self.tf, n_quad)
        dq = self.derivative(t_quad, order=1)
        integrand = np.sum(dq**2, axis=1)
        return np.trapezoid(integrand, t_quad)
