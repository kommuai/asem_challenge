# Kommu Lane Understanding Challenge

Congrats on being part of ASEM, one of the strongest robotics / semiconductor training grounds around.

In a world where AI tools are everywhere, we want to see what you are personally capable of: how you think, learn, test, improve, and build something scalable.

## Objective

Given a driving video, build a scalable lane understanding pipeline in **two phases**:

### Phase 1 — Extract lane structure

From the video, detect the lane lines and recover their shapes (curves, positions, and how lanes connect). Your output should support estimating:

- Lane line positions relative to the camera center
- Number of visible lane lines

### Phase 2 — Draw the lane layout

Take the lane structure from Phase 1 and render it onto a clean **white background**, producing a schematic lane drawing similar to the example below. This becomes your `output_lane_drawing.png`.

There is no fixed right answer. We care about your reasoning, method, and execution.

**Please submit even if your solution does not quite hit the goal.** A partial result with a clear approach, documented assumptions, and honest limitations is much more useful to us than no submission.

## Goal Example

Phase 2 should produce a drawing like this — lane lines on a white background, without the original road scene:

![Goal example: lane layout on a white background](goal-example.png)

## Download Video

The driving video is split into **10 H.264 `.ts` segments**, indexed `N = 0` through `9`.

Files are available in this repository under:

`870ce22d4093b701---2026-03-19--11-46-54/`

Clone the repository and combine the segments into one video:

```bash
git clone git@github.com:kommuai/asem_challenge.git
cd asem_challenge/870ce22d4093b701---2026-03-19--11-46-54
PREFIX="870ce22d4093b701---2026-03-19--11-46-54--"
for N in {0..9}; do echo "file '${PREFIX}${N}---qcamera.ts'"; done > inputs.txt
ffmpeg -f concat -safe 0 -i inputs.txt -c copy drive.ts
ffmpeg -fflags +genpts -i drive.ts -c copy drive.mp4
```

## Task

Use any method or tools to complete both phases: extract lane structure from the video, then render it as a white-background drawing.

You may use:

- OpenCV, machine learning, segmentation, geometry, tracking, optical flow, existing models, or any other approach.

But your solution must **not** be hard-coded to this exact video.

**Avoid:**

- manually drawing fixed lines
- fixed pixel coordinates only
- one-off tuning that only works on this clip
- solutions that cannot scale to other road videos

We prefer a simple scalable method over a highly accurate hard-coded result.

## Required Submission

Submit what you have — even if Phase 1 or Phase 2 is only partially working:

- `README.md`
- `source_code/`
- `output_lane_drawing.png`
- `lane_lines.csv` or `lane_lines.json`

**Optional:**

- `overlay_video.mp4`

Your README should explain:

- how to run your code
- your method
- your assumptions
- how you define camera center
- detected lane count
- lane positions relative to camera center
- limitations and what you would improve

## Evaluation

We will evaluate based on:

| Criteria | What we look for |
|----------|------------------|
| Scalability | Can your method work beyond this video? |
| Independence | Can you learn and solve without hand-holding? |
| Accuracy | Are the lane detections reasonable? |
| Engineering | Is the code clean and reproducible? |
| Reasoning | Are assumptions and limitations clearly explained? |

This is not about getting a perfect answer. It is about showing how you approach a real-world perception problem.
