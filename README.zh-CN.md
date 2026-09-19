# MiniMax 设计（partme-minimax-design）

在编码智能体（Codex / ZCode / Kimi）里生成 **MiniMax H3** 视频：环境变量鉴权、
**白模首尾帧锚定**、断点续查、经验证的下载，并逐字内置 **mmx 工具箱**技能
（文本/图像/语音/音乐）。

状态：**v0.4.2 —— 跨宿主技能与确定性客户端分发**（暂无 MCP server；可执行客户端是
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
- 内置技能（逐字 vendor，SHA-256 内容固定）：
  [full-aigc-skills/minimax-skills](https://github.com/full-aigc-skills/minimax-skills)
  v1.1.0 的 mmx 工具箱与音乐技能，**以及 8 个自 MiniMax-AI/MiniMax-H3 改编为
  mmx-cli 执行的风格生成器**（品牌宣传、3D 动画短片、MV 字幕、定格剪纸、
  纸拼贴、极简产品广告、手绘实拍、双人游戏开场）。

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

<!-- FULL_STACK_DOC_START -->
## 项目定位与运行边界

`minimax-design-plugin` 是面向 Codex、ZCode 与 Kimi 的跨宿主插件。当前基础版本为 `0.4.2`，三个宿主清单分别是 `.codex-plugin/plugin.json`、`.zcode-plugin/plugin.json` 和 `kimi.plugin.json`。README 中的版本、技能数量和安装来源以这些清单、`skills.lock.json` 与正式 Release 为准。

```text
宿主请求
  │
  ▼
三端 manifest / command / skill discovery
  │
  ▼
插件本地 Harness 或供应商客户端
  │
  ├── 成功：本地产物 + 回执 + 哈希
  └── 失败：稳定错误 + 可恢复状态，不静默重试付费动作
```

### 能力边界

- 插件负责宿主适配、配置注入、可执行脚本和插件专属技能；
- 外部技能只能从不可变 Release 按 lock 同步，受管副本禁止直接修改；
- “安装成功”“manifest 被发现”“MCP/Hook 已加载”“供应商调用成功”是四个不同证据等级；
- 网络、付费生成、上传、覆盖、删除和发布不会因安装插件而自动获得授权。

## 三端清单与技能供应链

| 宿主 | 清单 | 声明版本 |
|---|---|---|
| Codex | `.codex-plugin/plugin.json` | `0.4.2+codex.20260920` |
| ZCode | `.zcode-plugin/plugin.json` | `0.4.2` |
| Kimi | `kimi.plugin.json` | `0.4.2` |

| 外部技能包 | Release ref | Peeled SHA | 技能数 |
|---|---|---|---:|
| `minimax-skills` | `v1.1.1` | `6c27146be428` | 12 |

插件专属技能：`minimax-design-use`, `minimax-video-generation`。外部技能共 12 个；插件专属技能不进入 `skills.lock.json`。

## 验证与发布门禁

```bash
python3 scripts/lint_skills.py
python3 scripts/validate_distribution.py
python3 scripts/vendor/skill_vendor.py check --offline
python3 scripts/vendor/skill_vendor.py check
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

发布前必须验证：三端基础版本一致、Codex build metadata 合法、受管技能在线/离线摘要一致、插件专属技能已声明、测试通过、市场安装源固定到 Release tag，并在干净环境检查加载结果。

## 安全与凭据

- 凭据只通过宿主的 sensitive 配置、环境变量或外部秘密系统注入；
- README、日志、错误和测试夹具不得包含真实 token；
- 网络请求必须有超时、状态分类和有限重试；付费异步任务先持久化 task ID，再允许查询恢复；
- 路径写入限制在批准目录，已有文件默认不得覆盖。

## 故障排查

| 现象 | 证据入口 | 处理 |
|---|---|---|
| 插件未发现 | 对应宿主 manifest、市场 pin、安装缓存 | 核对插件 ID、版本和 Release ref |
| 技能数量不一致 | `skills.lock.json`、`plugin-local-skills.json` | 运行 vendor check，禁止手工修受管副本 |
| MCP/Hook 未加载 | 宿主诊断、配置 Schema、可执行文件 | 区分配置缺失、工具缺失和运行时错误 |
| 请求超时 | task ID、错误响应、超时配置 | 查询已有任务，不自动再次提交付费请求 |
| 发布后市场仍是旧内容 | tag、Release、市场生成器输出 | 校验 tag SHA 后重新生成和验证市场 |
<!-- FULL_STACK_DOC_END -->

## License

Apache-2.0。上游技能保留其自有许可（见 THIRD_PARTY_NOTICES.md）。
