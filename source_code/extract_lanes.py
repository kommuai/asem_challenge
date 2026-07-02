"""
extract_lanes.py

Phase 1: read a driving video, detect the left/right lane lines in each
frame, smooth them over time, and write out:
  - lane_lines.json   (per-frame lane geometry + offset from camera center)
  - overlay_video.mp4 (original video with detected lanes drawn on top,
                        for visual sanity-checking)

Usage:
    python extract_lanes.py --video drive.mp4 --out_dir ../output
"""

import argparse
import json
import os

import cv2
import numpy as np

from utils import (
    region_of_interest,
    default_roi_vertices,
    make_canny,
    hough_lines,
    split_left_right,
    fit_poly,
    poly_to_points,
    EMASmoother,
)


def process_video(video_path, out_dir, sample_every=1, make_overlay=True):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    camera_center_x = width / 2.0

    roi_vertices = default_roi_vertices(width, height)
    y_bottom = height
    y_top = int(0.62 * height)

    left_smoother = EMASmoother(alpha=0.25)
    right_smoother = EMASmoother(alpha=0.25)

    os.makedirs(out_dir, exist_ok=True)
    writer = None
    if make_overlay:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(
            os.path.join(out_dir, "overlay_video.mp4"), fourcc, fps, (width, height)
        )

    frames_out = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_every == 0:
            edges = make_canny(frame)
            masked = region_of_interest(edges, roi_vertices)
            lines = hough_lines(masked)
            left_pts, right_pts = split_left_right(lines, width)

            left_coeffs = left_smoother.update(fit_poly(left_pts))
            right_coeffs = right_smoother.update(fit_poly(right_pts))

            left_points = poly_to_points(left_coeffs, y_top, y_bottom)
            right_points = poly_to_points(right_coeffs, y_top, y_bottom)

            # offset from camera center measured at the bottom of the frame
            left_offset = (
                left_points[-1][0] - camera_center_x if left_points else None
            )
            right_offset = (
                right_points[-1][0] - camera_center_x if right_points else None
            )

            frames_out.append(
                {
                    "frame": frame_idx,
                    "camera_center_x": camera_center_x,
                    "lanes": [
                        {
                            "id": "left",
                            "points": left_points,
                            "offset_from_center_px": left_offset,
                        },
                        {
                            "id": "right",
                            "points": right_points,
                            "offset_from_center_px": right_offset,
                        },
                    ],
                }
            )

            if writer is not None:
                overlay = frame.copy()
                for pts, color in ((left_points, (0, 255, 0)), (right_points, (0, 0, 255))):
                    for i in range(len(pts) - 1):
                        p1 = tuple(map(int, pts[i]))
                        p2 = tuple(map(int, pts[i + 1]))
                        cv2.line(overlay, p1, p2, color, 4)
                writer.write(overlay)

        frame_idx += 1

    cap.release()
    if writer is not None:
        writer.release()

    with open(os.path.join(out_dir, "lane_lines.json"), "w") as f:
        json.dump(
            {
                "video": os.path.basename(video_path),
                "width": width,
                "height": height,
                "fps": fps,
                "frames": frames_out,
            },
            f,
            indent=2,
        )

    print(f"Processed {frame_idx} frames.")
    print(f"Wrote {os.path.join(out_dir, 'lane_lines.json')}")
    if make_overlay:
        print(f"Wrote {os.path.join(out_dir, 'overlay_video.mp4')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Path to input video (e.g. drive.mp4)")
    parser.add_argument("--out_dir", default="../output", help="Where to write outputs")
    parser.add_argument("--sample_every", type=int, default=1, help="Process every Nth frame")
    parser.add_argument("--no_overlay", action="store_true", help="Skip overlay video generation")
    args = parser.parse_args()

    process_video(
        args.video,
        args.out_dir,
        sample_every=args.sample_every,
        make_overlay=not args.no_overlay,
    )