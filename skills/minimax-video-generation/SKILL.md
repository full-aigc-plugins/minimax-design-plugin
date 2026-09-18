---
name: minimax-video-generation
description: "Generate videos with MiniMax Hailuo through scripts/minimax_video.py: text2video, image2video with first_frame_image, and first/last-frame composition anchored by a Blender white-model previs. Deterministic client, resumable query, verified download."
---

# MiniMax Video Generation

Deterministic client: `scripts/minimax_video.py`. Every paid call needs the
step-0 preflight from `minimax-design-use` to pass first. The client is
async-native: create task → poll → retrieve file → verified download.

## Modes

1. **t2v** — text only:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/minimax_video.py" t2v \
  --prompt "<shot description>" --out generated/shot-01.mp4
```

2. **i2v** — first-frame image anchors composition:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/minimax_video.py" i2v \
  --first-frame renders/shot-01_first.png --prompt "<motion description>" \
  --out generated/shot-01.mp4
```

3. **first/last-frame** — the white-model previs anchor (preferred for
   storyboarded work): render each shot's first and last frame from the Blender
   white model, then let Hailuo interpolate:

```bash
python3 "${CLAUDE_PROJECT_DIR}/scripts/minimax_video.py" i2v \
  --first-frame renders/shot-01_first.png --last-frame renders/shot-01_last.png \
  --prompt "<what happens between the two frames>" --out generated/shot-01.mp4
```

Local files are base64-encoded automatically; URLs pass through unchanged.

## Parameters

- `--duration 6|10` (10s only at 768P), `--resolution 768P|1080P` (1080P is 6s only).
- `--wait <seconds>` caps polling; a timeout prints the `task_id` — resume later
  with `query --task-id <id>`, never resubmit a paid task.
- Model and gateway come from env: `MINIMAX_MODEL` (default `MiniMax-Hailuo-02`),
  `MINIMAX_BASE` (default 国内 `api.minimaxi.com`).

## Style-leak discipline (white-model frames)

The white-model frame is gray primitives; i2v may keep that style. Run one A/B
shot before a batch: (a) white-model frame directly + a strong restyle prompt
("photorealistic cinematic scene, ignore the placeholder style, keep the exact
composition"); (b) restyle the frame through an image model first. Fix the
winning path into the episode's convention before spending on all shots.

## Prompt contract

- Describe motion and content between the frames, not the composition (the
  frames already lock it): subject action, camera behavior, atmosphere, style.
- One shot per generation; per-shot regeneration is the cost-control unit.

## Never do

- Never submit paid generation without the preflight and the user's intent.
- Never resubmit a submitted task id; `query` is the only resume path.
- Never treat a polling timeout as failure — it is a resume state.
- Never delete or overwrite a downloaded shot; regeneration is per shot id.
