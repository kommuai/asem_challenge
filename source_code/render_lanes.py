"""
render_lanes.py

Phase 2: take the lane_lines.json produced by extract_lanes.py and draw
a clean schematic (white background, no road scene) matching the style
of the challenge's goal-example.png.

Usage:
    python render_lanes.py --json ../output/lane_lines.json \
                            --frame 300 \
                            --out ../output_lane_drawing.png
"""

import argparse
import json

import numpy as np
import cv2


def render_frame(data, frame_number, out_path):
    width, height = data["width"], data["height"]
    frame_entry = next((f for f in data["frames"] if f["frame"] == frame_number), None)
    if frame_entry is None:
        # fall back to nearest available frame
        frame_entry = min(data["frames"], key=lambda f: abs(f["frame"] - frame_number))
        print(f"Frame {frame_number} not found, using frame {frame_entry['frame']} instead.")

    canvas = np.ones((height, width, 3), dtype=np.uint8) * 255
    camera_center_x = int(frame_entry["camera_center_x"])

    # camera center reference line
    cv2.line(canvas, (camera_center_x, 0), (camera_center_x, height), (200, 200, 200), 2)

    colors = {"left": (40, 160, 40), "right": (40, 40, 200)}
    for lane in frame_entry["lanes"]:
        pts = lane["points"]
        if len(pts) < 2:
            continue
        color = colors.get(lane["id"], (0, 0, 0))
        for i in range(len(pts) - 1):
            p1 = tuple(map(int, pts[i]))
            p2 = tuple(map(int, pts[i + 1]))
            cv2.line(canvas, p1, p2, color, 4)

        offset = lane.get("offset_from_center_px")
        if offset is not None:
            label = f"{lane['id']}: {offset:+.0f}px"
            label_pos = tuple(map(int, pts[-1]))
            cv2.putText(
                canvas, label, (label_pos[0] - 40, label_pos[1] + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
            )

    cv2.imwrite(out_path, canvas)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Path to lane_lines.json")
    parser.add_argument("--frame", type=int, default=0, help="Which frame index to render")
    parser.add_argument("--out", default="../output_lane_drawing.png")
    args = parser.parse_args()

    with open(args.json) as f:
        data = json.load(f)

    render_frame(data, args.frame, args.out)