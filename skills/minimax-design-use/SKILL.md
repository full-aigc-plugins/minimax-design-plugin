---
name: minimax-design-use
description: "Route MiniMax design requests: capability preflight first, then video generation (text2video, image2video, first/last-frame), or the vendored mmx toolkit skills for text, image, speech, and music generation."
---

# MiniMax Design Router

Use this as the entry point. Before any generation, run the capability preflight
(step 0) — MiniMax authenticates with an API key from the environment, and a
missing key must surface as actionable guidance, never as a raw API error.

## Step 0 — capability preflight (always first)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/minimax_video.py" check
```

Read the output and act on it:

- `MINIMAX_API_KEY: 未设置` → tell the user exactly how to fix it: get a key at
  https://platform.minimaxi.com (国内) or https://platform.minimax.io (国际),
  then `export MINIMAX_API_KEY=...` (shell config or project `.env`). Do not
  proceed to paid generation without the key; do not ask the user to paste the
  key into chat.
- `MINIMAX_API_KEY: 已设置` → continue. The gateway line shows which base
  (国内 api.minimaxi.com / 国际 api.minimax.io) the calls will use.
- `mmx CLI` lines are informational: the vendored `minimax-multimodal-toolkit`
  skill needs `mmx` (`npm install -g mmx-cli` + `mmx auth login --api-key`);
  video generation through `scripts/minimax_video.py` does not.

## Routing

- **Video generation** (text2video, image2video, first/last-frame composition
  from a white-model previs) → `minimax-video-generation`.
- **Text / images / speech / music / web search via the mmx CLI** →
  `minimax-multimodal-toolkit`.
- **Music / song generation** → `minimax-music-gen`; personalized playlists →
  `minimax-music-playlist`.

## Never do

- Never run paid generation without the step-0 preflight passing.
- Never echo the API key value back into the conversation; show only the masked
  tail (the check command already does this).
- Never guess the gateway: 国内 and 国际 accounts are separate — the base URL
  must match where the key was issued (`MINIMAX_BASE` overrides).
