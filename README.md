# MiniMax Design (partme-minimax-design)

Generate **MiniMax H3** videos from your coding agent (Codex / ZCode / Kimi) with environment-variable authentication, **first/last-frame composition anchored by Blender white-model previs frames**, resumable async queries with verified downloads, and verbatim vendored **mmx toolkit** skills (text / image / speech / music).

Status: **v0.4.2 — cross-host skill and deterministic-client distribution** (no MCP server yet; the executable client is `scripts/minimax_video.py`).

## Quick start

1. Get an API key: [platform.minimaxi.com](https://platform.minimaxi.com) (CN) or [platform.minimax.io](https://platform.minimax.io) (global) → 用户中心 → 接口密钥.
2. Export it: `export MINIMAX_API_KEY=...` (shell config or project `.env`). Gateway defaults to `api.minimaxi.com`; override with `MINIMAX_BASE` for global accounts.
3. In your agent, ask the router skill — it always runs the capability preflight first:

```text
用 MiniMax 生成一段视频：<你的画面描述>
```

The `minimax-design-use` skill routes the request and surfaces actionable guidance when the key is missing (where to apply, how to export) instead of a raw API error.

## Capabilities

| Mode | Anchoring | Command |
|---|---|---|
| text2video | prompt only (ratio required) | `minimax_video.py generate --prompt ... --ratio 16:9 --out ...` |
| image2video | `first_frame` role | `minimax_video.py generate --first-frame ... --out ...` |
| first/last-frame (FL2VA) | white-model previs frames | `minimax_video.py generate --first-frame ... --last-frame ... --out ...` |
| reference-image | subject consistency | `minimax_video.py generate --reference-image ... --out ...` |

- Model: `MiniMax-H3` (480P/768P/2K, 4–15s) or `MiniMax-H3-Max` (fast, 480P/768P, 5–15s); `MINIMAX_MODEL` overrides.
- v2 API: `POST {host}/v2/video_generation` with a multimodal `content` array
  (`first_frame` / `last_frame` / `reference_image` roles); OpenAI-style errors;
  async tasks pollable via `query --task-id` (`list` / `cancel` included).
- Prompts are drafted through the vendored **`h3-prompt-writing`** skill
  (T2VA / I2VA / FL2VA / L2VA / Ref2VA structures from MiniMax-AI/MiniMax-H3).
- Async with resumable queries: a polling timeout prints the `task_id`; resume with `query --task-id` — never resubmit a paid task.
- Vendored skills (verbatim, content-pinned by SHA-256): the mmx toolkit + music skills from [full-aigc-skills/minimax-skills](https://github.com/full-aigc-skills/minimax-skills) v1.1.0, **plus the 8 style-generator skills adapted from MiniMax-AI/MiniMax-H3 to mmx-cli execution** (brand promo, 3D animation short, MV subtitles, papercraft stop motion, paper collage, minimalist product ad, handdrawn live, co-op game intro).

## Fixed-format account pipeline

This plugin is the generation leg of a fixed-format account pipeline:

```text
公有领域经典名场面 → 镜头表 → Blender 白模逐镜预演 → MiniMax 首尾帧逐镜生成
→ detect_shots 实测切点 → video-agent-kit 解说后期 → 发布
```

See the companion kit for the full episode workflow (shot-table schema, previs conventions, copyright guidance): white-model previs lives in `partme-blender-plugin` (`blender-previs`).

## Three-platform install

| Platform | Manifest | Install |
|---|---|---|
| Codex | `.codex-plugin/plugin.json` | add the `partme-ai` marketplace entry / `codex plugin add minimax-design@<market>` |
| ZCode | `.zcode-plugin/plugin.json` | marketplace entry; standard `hooks/hooks.json` is auto-discovered once |
| Kimi | `kimi.plugin.json` | flat skills + hooks |

`.agents/plugins/marketplace.json` carries the Codex marketplace entry (`AVAILABLE` installation, `ON_USE` authentication).

## Docs

- [中文说明](README.zh-CN.md)
- Architecture & conventions: `docs/`
- [Upstream skills](https://github.com/full-aigc-skills/minimax-skills) — vendored verbatim; content pinned by SHA-256 in `skills.lock.json`

<!-- FULL_STACK_DOC_START -->
## Project position and runtime boundary

`minimax-design-plugin` is a cross-host plugin for Codex, ZCode, and Kimi. Its current base version is `0.4.2`. Versions, skill counts, and installation sources are derived from the three host manifests, `skills.lock.json`, and immutable GitHub Releases.

```text
host request -> manifest/command/skill discovery -> local harness or provider client
             -> artifact + receipt + hash
             -> or stable failure + recoverable state
```

### Boundaries

- The plugin owns host adaptation, configuration injection, executable clients, and declared plugin-local skills.
- External skills are synchronized only from immutable releases; managed copies are not edited directly.
- Installation, manifest discovery, hook/MCP loading, and successful provider execution are distinct proof levels.
- Installation does not authorize network use, paid generation, upload, overwrite, deletion, or publishing.

## Host manifests and skill supply chain

| Host | Manifest | Declared version |
|---|---|---|
| Codex | `.codex-plugin/plugin.json` | `0.4.2+codex.20260920` |
| ZCode | `.zcode-plugin/plugin.json` | `0.4.2` |
| Kimi | `kimi.plugin.json` | `0.4.2` |

| External package | Release ref | Peeled SHA | Skills |
|---|---|---|---:|
| `minimax-skills` | `v1.1.1` | `6c27146be428` | 12 |

Plugin-local skills: `minimax-design-use`, `minimax-video-generation`. The external lock contains 12 skills; plugin-local skills do not belong in `skills.lock.json`.

## Verification and release gates

```bash
python3 scripts/lint_skills.py
python3 scripts/validate_distribution.py
python3 scripts/vendor/skill_vendor.py check --offline
python3 scripts/vendor/skill_vendor.py check
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Before release, verify aligned base versions, legal Codex build metadata, online/offline skill digests, the plugin-local manifest, tests, immutable marketplace refs, and clean-environment host loading.

## Security and credentials

- Inject credentials only through sensitive host configuration, environment variables, or an external secret store.
- Never place real tokens in README files, logs, errors, or fixtures.
- Network calls require timeouts, stable failure classification, and bounded retries. Persist paid async task IDs before polling or recovery.
- Restrict writes to approved output roots; existing files are not overwritten by default.

## Troubleshooting

| Symptom | Evidence | Resolution |
|---|---|---|
| Plugin not discovered | Host manifest, marketplace pin, install cache | Check plugin ID, version, and release ref |
| Skill count drift | `skills.lock.json`, `plugin-local-skills.json` | Run vendor checks; do not patch managed copies |
| Hook or MCP not loaded | Host diagnostics, schema, executable availability | Separate missing config, missing tool, and runtime failure |
| Request timeout | Task ID, provider error, timeout config | Query the existing task; do not resubmit a paid operation automatically |
| Marketplace serves old content | Tag, Release, generator output | Verify tag SHA, then regenerate and validate the marketplace |
<!-- FULL_STACK_DOC_END -->

## License

Apache-2.0. Upstream skills keep their own licenses (see THIRD_PARTY_NOTICES.md).
