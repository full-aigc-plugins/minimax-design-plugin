# MiniMax 设计（partme-minimax-design）

在编码智能体（Codex / ZCode / Kimi）里生成 **MiniMax **H3** 视频：环境变量鉴权、
**白模首尾帧锚定**、断点续查、经验证的下载，并逐字内置 **mmx 工具箱**技能
（文本/图像/语音/音乐）。

状态：**v0.1.0 —— 纯技能分发**（暂无 MCP server；确定性客户端是
`scripts/minimax_video.py`）。

## 快速开始

1. 申请密钥：[platform.minimaxi.com](https://platform.minimaxi.com)（国内）或
   [platform.minimax.io](https://platform.minimax.io)（国际）→ 用户中心 → 接口密钥。
2. 配置：`export MINIMAX_API_KEY=...`（写入 shell 配置或项目 `.env`）。网关默认
   `api.minimaxi.com`，国际账号用 `MINIMAX_BASE` 覆盖。
3. 在智能体里直接提需求，路由技能会**先跑能力预检**：

```text
用 MiniMax 生成一段视频：<你的画面描述>
```

密钥缺失时 `minimax-design-use` 给出的是「去哪申请、怎么配置」的可操作指引，
而不是一条裸 API 报错。

## 能力

| 模式 | 锚定 | 命令 |
|---|---|---|
| 文生视频 | 仅提示词（必填 ratio） | `minimax_video.py generate --prompt ... --ratio 16:9 --out ...` |
| 图生视频 | `first_frame` 首帧 | `minimax_video.py generate --first-frame ... --out ...` |
| 首尾帧 FL2VA | 白模预演首尾帧 | `minimax_video.py generate --first-frame ... --last-frame ... --out ...` |
| 主体参考 | `reference_image` | `minimax_video.py generate --reference-image ... --out ...` |

- 模型：`MiniMax-H3`（480P/768P/2K，4~15s）与 `MiniMax-H3-Max`（极速，480P/768P，5~15s）；
  `MINIMAX_MODEL` 覆盖。
- v2 接口：`POST {网关}/v2/video_generation`，content 多模态数组（`first_frame` /
  `last_frame` / `reference_image` 角色）；OpenAI 风格错误；异步任务用
  `query --task-id` 续查（含 `list` / `cancel`）。
- 提示词经内置 **`h3-prompt-writing`** 技能起草（T2VA / I2VA / FL2VA / L2VA /
  Ref2VA 结构，来自 MiniMax-AI/MiniMax-H3）。
- 异步任务 + 断点续查：轮询超时会打印 `task_id`，用 `query --task-id` 续查——
  **付费任务永不重复提交**。
- 内置技能（逐字 vendor 自
  [full-aigc-skills/minimax-skills](https://github.com/full-aigc-skills/minimax-skills)，
  内容按 SHA-256 固定）：`minimax-multimodal-toolkit`、`minimax-music-gen`、
  `minimax-music-playlist`。

## 固定模式起号流水线

本插件是固定模式起号流水线的「生成腿」：

```text
公有领域经典名场面 → 镜头表 → Blender 白模逐镜预演 → MiniMax 首尾帧逐镜生成
→ detect_shots 实测切点 → video-agent-kit 解说后期 → 发布
```

白模半段（镜头表 schema、白模规范、版权指引）见 `partme-blender-plugin` 的
`blender-previs` 技能。

## 三平台安装

| 平台 | 清单 | 说明 |
|---|---|---|
| Codex | `.codex-plugin/plugin.json` | `partme-ai` market 条目 / `codex plugin add` |
| ZCode | `.zcode-plugin/plugin.json` | market 条目，钩子已接 |
| Kimi | `kimi.plugin.json` | 扁平技能 + 钩子 |

## 文档

- 架构与约定见 `docs/`
- [上游技能](https://github.com/full-aigc-skills/minimax-skills)——逐字 vendor，
  内容由 `skills.lock.json` 的 SHA-256 固定

## License

Apache-2.0。上游技能保留其自有许可（见 THIRD_PARTY_NOTICES.md）。
