"""
Shared utility functions for the lane detection pipeline.
Kept resolution-agnostic on purpose: every geometric value is derived
from the frame's own width/height, never hard-coded pixel constants.
"""

import numpy as np
import cv2


def region_of_interest(img, vertices):
    """Mask out everything except the polygon defined by `vertices`."""
    mask = np.zeros_like(img)
    cv2.fillPoly(mask, [vertices], 255)
    return cv2.bitwise_and(img, mask)


def default_roi_vertices(width, height):
    """
    A trapezoid covering the road area, expressed as fractions of the
    frame size so it scales automatically to any resolution.
    Tweak the fractions if your camera mount / FOV differs a lot.
    """
    bottom_left = (int(0.05 * width), height)
    bottom_right = (int(0.98 * width), height)
    top_left = (int(0.42 * width), int(0.62 * height))
    top_right = (int(0.58 * width), int(0.62 * height))
    return np.array([[bottom_left, top_left, top_right, bottom_right]], dtype=np.int32)[0]


def make_canny(frame):
    """Standard grayscale -> blur -> Canny edge pipeline."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    return edges


def hough_lines(edges):
    return cv2.HoughLinesP(
        edges,
        rho=2,
        theta=np.pi / 180,
        threshold=50,
        minLineLength=40,
        maxLineGap=100,
    )


def split_left_right(lines, width):
    """
    Separate raw Hough segments into left-lane / right-lane candidates
    using slope sign and position relative to frame center.
    """
    left_pts, right_pts = [], []
    if lines is None:
        return left_pts, right_pts

    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 == x1:
            continue  # skip vertical segments (undefined slope)
        slope = (y2 - y1) / (x2 - x1)
        if abs(slope) < 0.3:
            continue  # skip near-horizontal noise (not lane-like)

        mid_x = (x1 + x2) / 2
        if slope < 0 and mid_x < width * 0.6:
            left_pts.append((x1, y1))
            left_pts.append((x2, y2))
        elif slope > 0 and mid_x > width * 0.4:
            right_pts.append((x1, y1))
            right_pts.append((x2, y2))

    return left_pts, right_pts


def fit_poly(points, degree=2):
    """Fit x = f(y) so near-vertical lane lines don't blow up the fit."""
    if len(points) < 4:
        return None
    pts = np.array(points)
    xs, ys = pts[:, 0], pts[:, 1]
    try:
        coeffs = np.polyfit(ys, xs, degree)
        return coeffs
    except np.linalg.LinAlgError:
        return None


def poly_to_points(coeffs, y_start, y_end, num=30):
    """Sample a fitted polynomial into a list of (x, y) points."""
    if coeffs is None:
        return []
    ys = np.linspace(y_start, y_end, num)
    xs = np.polyval(coeffs, ys)
    return [(float(x), float(y)) for x, y in zip(xs, ys)]


class EMASmoother:
    """
    Simple exponential moving average smoother for polynomial
    coefficients, so lane lines don't jitter frame to frame.
    """

    def __init__(self, alpha=0.25):
        self.alpha = alpha
        self.state = None

    def update(self, coeffs):
        if coeffs is None:
            return self.state
        if self.state is None:
            self.state = coeffs
        else:
            self.state = self.alpha * coeffs + (1 - self.alpha) * self.state
        return self.state