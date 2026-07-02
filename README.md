# Lane Understanding Challenge — Submission

## Overview

This project detects lane lines from a driving video and renders them as a
clean schematic drawing on a white background, showing the lane geometry and
each lane's horizontal position relative to the camera center.

The pipeline uses classical computer vision (no training data, no
per-video tuning), so the same code can be pointed at a different driving
video and reprocessed without modification.

## How to run

### 1. Prepare the video
Combine the provided `.ts` segments into a single video (already done for
this submission, kept here for reproducibility):

```bash
ffmpeg -f concat -safe 0 -i inputs.txt -c copy drive.ts
ffmpeg -fflags +genpts -i drive.ts -c copy drive.mp4
```

### 2. Set up the environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
pip install -r source_code/requirements.txt
```

### 3. Run lane extraction (Phase 1)
```bash
cd source_code
python extract_lanes.py --video ../drive.mp4 --out_dir ../output
```
Outputs:
- `output/lane_lines.json` — per-frame lane geometry and offsets
- `output/overlay_video.mp4` — original video with detected lanes drawn on top, for visual verification

### 4. Render the schematic (Phase 2)
```bash
python render_lanes.py --json ../output/lane_lines.json --frame 5880 --out ../output_lane_drawing.png
```
`--frame` selects which frame's lane geometry to render. Frame 5880
(~4:54 into the video) was chosen for this submission because it is a
clearly visible, well-tracked curved section of road.

## Method

1. **Edge detection** — each frame is converted to grayscale, blurred, and
   passed through a Canny edge detector.
2. **Region of interest (ROI)** — a trapezoid covering the road area masks
   out sky, dashboard, and roadside clutter. The trapezoid is defined as
   *fractions* of the frame's width/height (not fixed pixel coordinates),
   so it automatically scales to any input resolution.
3. **Hough transform** — straight line segments are extracted from the
   masked edges.
4. **Left/right classification** — segments are split into left-lane vs.
   right-lane candidates using slope sign and horizontal position relative
   to the frame's midpoint.
5. **Polynomial fit** — each side's points are fit to a 2nd-degree
   polynomial (x as a function of y), which handles gentle curves better
   than a single straight line.
6. **Temporal smoothing** — an exponential moving average (EMA) smooths
   the polynomial coefficients across frames, reducing frame-to-frame
   jitter without hard-coding to any specific frame.
7. **Rendering** — the fitted lane curves for a chosen frame are drawn on
   a blank white canvas, alongside a reference line marking the camera
   center.

## Camera center & lane position definition

- **Camera center** is defined as the horizontal midpoint of the frame:
  `camera_center_x = frame_width / 2`.
- **Lane offset** for each detected lane is measured in pixels, calculated
  as the horizontal distance between that lane's fitted curve (evaluated
  at the bottom of the frame, closest to the vehicle) and `camera_center_x`.
  A negative value means the lane sits to the left of center; positive
  means right.
- These values are written per-frame in `lane_lines.json` under
  `offset_from_center_px` for each lane.

## Detected lanes

The pipeline detects **up to 2 lane lines per frame** (left and right,
relative to the camera's driving position). It does not currently attempt
to detect additional lanes further out (e.g. adjacent lanes on a multi-lane
road), since the classical Hough-based approach is tuned to find the
nearest line on each side.

## Assumptions

- The camera is roughly forward-facing and mounted near the vehicle's
  centerline, so the frame's horizontal midpoint is a reasonable proxy for
  the car's actual centerline.
- The road occupies the lower-to-middle portion of the frame, consistent
  with a typical forward dashcam mount — this determines the ROI's
  vertical bounds.
- Lane markings are visibly higher-contrast than the road surface (works
  under most lighting, including night driving with headlights/streetlights
  as seen in this footage — see `overlay_video.mp4`).

## Limitations & what I'd improve with more time

- **Intersections and open areas** (e.g. parking lots, wide junctions) confuse
  the ROI/Hough approach, since there are multiple candidate edges and no
  single clear "lane." This was observed directly in the overlay video
  output.
- **Frames with faded, absent, or heavily obscured lane markings** can
  produce unreliable or missing lane detections, since the method relies on
  edge contrast rather than semantic understanding of "lane."
- **No real-world calibration** — offsets are reported in pixels, not
  meters, since no camera intrinsics/extrinsics or lane-width reference
  were provided.
- **Straight-line camera-center assumption** — if the camera isn't mounted
  exactly on the vehicle's centerline, offsets will be systematically
  biased; this isn't corrected for.
- With more time, I would:
  - Add a perspective ("bird's-eye view") transform before lane fitting, to
    better handle sharper curves and give more geometrically accurate
    offsets.
  - Replace the classical CV stage with a learned lane-segmentation model
    for more robust detection in low-light, rain, or degraded-marking
    conditions.
  - Use a proper tracker (e.g. Kalman filter) instead of a simple EMA for
    smoother and more failure-resistant temporal consistency.
  - Auto-select a representative "best" frame for the final schematic
    rather than manually choosing one, e.g. by scoring frames on fit
    confidence/line length.

## Files in this submission

```
asem_challenge/
├── README.md                  <- this file
├── source_code/
│   ├── extract_lanes.py       <- Phase 1: lane detection + tracking
│   ├── render_lanes.py        <- Phase 2: schematic rendering
│   ├── utils.py                <- shared CV utility functions
│   └── requirements.txt
├── output_lane_drawing.png    <- final rendered lane schematic
└── output/
    ├── lane_lines.json        <- per-frame lane geometry & offsets
    └── overlay_video.mp4      <- lanes overlaid on original video (visual QA)
