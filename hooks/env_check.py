#!/usr/bin/env python3
"""SessionStart hook: report MiniMax Design readiness for this plugin.

Advisory only — always exits 0. Credentials come from the environment
(MINIMAX_API_KEY) or the optional mmx CLI login; nothing here blocks a session.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    lines: list[str] = []

    client = ROOT / "scripts" / "minimax_video.py"
    lines.append("生成客户端: 就绪" if client.is_file() else "生成客户端: 脚本缺失")

    key = os.environ.get("MINIMAX_API_KEY")
    if key:
        lines.append(f"MINIMAX_API_KEY: 已设置（尾号 {key[-4:]}）")
    else:
        lines.append("MINIMAX_API_KEY: 未设置——首次使用时按 minimax-design-use 的"
                     " Step 0 指引配置（platform.minimax.cn / platform.minimax.io 申请）")

    base = os.environ.get("MINIMAX_BASE")
    lines.append(f"网关: {base or 'api.minimaxi.com（国内默认，MINIMAX_BASE 可覆盖）'}")

    if shutil.which("mmx"):
        lines.append("mmx CLI: 在 PATH")
    else:
        lines.append("mmx CLI: 未安装——通用生成/语音/视觉/搜索需要它（npm install -g mmx-cli && mmx auth login）")

    try:
        sys.stdin.read()
    except Exception:
        pass

    print("MiniMax 设计插件环境：" + "；".join(lines))
    return 0


if __name__ == "__main__":
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    sys.exit(main())
