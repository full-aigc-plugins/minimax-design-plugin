#!/usr/bin/env python3
"""MiniMax 视频生成客户端 v2（MiniMax-H3 / H3-Max，video_generation v2 异步任务）。

用法:
  export MINIMAX_API_KEY=...                # platform.minimax.cn / .minimaxi.com / .minimax.io 申请
  python3 minimax_video.py check            # 能力预检（鉴权/依赖，exit 0）
  python3 minimax_video.py generate --prompt "..." --out shot-01.mp4
  python3 minimax_video.py generate --first-frame first.png --last-frame last.png \
      --prompt "两帧之间的连续运动描述" --out shot-01.mp4
  python3 minimax_video.py query --task-id <id>
  python3 minimax_video.py list
  python3 minimax_video.py cancel --task-id <id>

v2 契约（platform.minimax.cn/docs/api-reference/video-generation-v2-create）:
  - POST {host}/v2/video_generation，model=MiniMax-H3（480P/768P/2K，4~15s）
    或 MiniMax-H3-Max（极速版，480P/768P，5~15s）。
  - content 多模态数组：text（必填非空，≤7000 字符）+ image_url 元素带
    role=first_frame/last_frame/reference_image；url 支持公网 URL /
    mm_file://{file_id} / data:base64（本地文件自动转 data URL）。
  - 文生视频必填 ratio（不能 adaptive）；图生视频 ratio 可 adaptive。
  - 轮询: GET {host}/v2/video_generation/{task_id}，status ∈
    queued/running/succeeded/failed/cancelled，成功后 content.url 为视频地址。
  - 鉴权: Authorization: Bearer <MINIMAX_API_KEY>；网关默认
    https://api.minimax.cn，国际账号 MINIMAX_API_HOST=https://api.minimax.io。

mmx-cli（Token Plan 订阅制官方 CLI，https://github.com/MiniMax-AI/cli）是另一条
执行路径：mmx video generate / image generate / speech synthesize / text chat /
vision describe / search query；登录 mmx auth login --api-key sk-xxx。两者共享
同一账号体系；首尾帧精确锚定走本客户端（v2 content roles），通用生成可直接用 mmx。
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HOST = os.environ.get("MINIMAX_API_HOST", "https://api.minimax.cn").rstrip("/")
MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-H3")


def check() -> int:
    """能力预检：鉴权与依赖是否就绪。永远 exit 0，只输出可操作的状态行。"""
    lines: list[str] = []
    key = os.environ.get("MINIMAX_API_KEY")
    if key:
        lines.append(f"MINIMAX_API_KEY: 已设置（尾号 {key[-4:]}）")
    else:
        lines.append("MINIMAX_API_KEY: 未设置")
        lines.append("  获取: https://platform.minimax.cn （国内）/ https://platform.minimax.io （国际）"
                     " → 用户中心 → 接口密钥")
        lines.append("  配置: export MINIMAX_API_KEY=你的密钥   # 建议写入 shell 配置或项目 .env")
    lines.append(f"网关: {HOST}（MINIMAX_API_HOST 可覆盖；国内 .cn / .minimaxi.com，国际 .io）")
    lines.append(f"模型: {MODEL}")

    mmx = shutil.which("mmx")
    if mmx:
        lines.append(f"mmx CLI: {mmx}")
        auth = subprocess.run(["mmx", "auth", "status"], capture_output=True, text=True, timeout=20)
        status = (auth.stdout or "").strip().splitlines()
        lines.append("mmx 登录: " + (status[-1] if status else "未知（mmx auth status 无输出）"))
    else:
        lines.append("mmx CLI: 未安装——通用生成/语音/视觉/搜索需要它（Token Plan 订阅）")
        lines.append("  安装: npm install -g mmx-cli && mmx auth login --api-key sk-xxx")
        lines.append("  若已设 MINIMAX_API_KEY，可免登录直接用本客户端的 v2 接口路径")

    try:
        sys.stdin.read()
    except Exception:
        pass
    print("MiniMax 设计插件环境：" + "；".join(lines))
    return 0


def headers() -> dict:
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        sys.exit("缺 MINIMAX_API_KEY 环境变量——获取: https://platform.minimax.cn → 用户中心 → 接口密钥；"
                 "配置: export MINIMAX_API_KEY=你的密钥")
    return {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}


def call(method: str, path: str, payload: dict | None = None) -> dict:
    req = urllib.request.Request(
        HOST + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers(),
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        sys.exit(f"HTTP {exc.code}: {detail}")


def encode_image(path: str) -> str:
    if path.startswith(("http://", "https://", "mm_file://", "data:")):
        return path
    with open(path, "rb") as f:
        suffix = Path(path).suffix.lstrip(".").lower() or "png"
        return f"data:image/{suffix};base64," + base64.b64encode(f.read()).decode()


def build_content(prompt: str, first: str | None, last: str | None, refs: list[str]) -> list[dict]:
    if refs and (first or last):
        sys.exit("图生视频（first/last_frame）与多模态参考（reference_*）互斥，不可混用")
    content: list[dict] = [{"type": "text", "text": prompt}]
    if first:
        content.append({"type": "image_url", "image_url": {"url": encode_image(first)},
                        "role": "first_frame"})
    if last:
        if not first:
            sys.exit("last_frame 必须与 first_frame 成对使用（FL2VA）")
        content.append({"type": "image_url", "image_url": {"url": encode_image(last)},
                        "role": "last_frame"})
    for r in refs:
        content.append({"type": "image_url", "image_url": {"url": encode_image(r)},
                        "role": "reference_image"})
    return content


def wait_task(task_id: str, wait: int) -> dict:
    deadline = time.time() + wait
    while time.time() < deadline:
        time.sleep(10)
        body = call("GET", f"/v2/video_generation/{task_id}")
        task = body.get("task") or body
        status = task.get("status")
        print("status:", status, flush=True)
        if status in ("succeeded", "failed", "cancelled"):
            return body
    sys.exit(f"轮询超时——task_id={task_id} 处于进行中，稍后用 query --task-id 续查（勿重复提交）")


def download(url: str, out: str) -> None:
    urllib.request.urlretrieve(url, out)
    print("downloaded:", out)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="能力预检（鉴权/依赖，exit 0）")

    g = sub.add_parser("generate", help="提交 H3 v2 生成任务并轮询")
    g.add_argument("--prompt", required=True, help="非空提示词（≤7000 字符；首尾帧模式描述两帧间运动）")
    g.add_argument("--first-frame", help="首帧图（本地文件/URL/mm_file）")
    g.add_argument("--last-frame", help="尾帧图（须与首帧成对）")
    g.add_argument("--reference-image", action="append", default=[],
                   help="主体参考图（可重复；与首尾帧互斥）")
    g.add_argument("--model", default=MODEL, choices=["MiniMax-H3", "MiniMax-H3-Max"])
    g.add_argument("--duration", type=int, default=6, help="4~15 秒（H3-Max 5~15）")
    g.add_argument("--resolution", default="768P", choices=["480P", "768P", "2K"])
    g.add_argument("--ratio", help="文生视频必填且不能 adaptive；图生视频可 adaptive")
    g.add_argument("--out", required=True)
    g.add_argument("--wait", type=int, default=900, help="最长轮询秒数")
    g.add_argument("--async-only", action="store_true", help="只提交不轮询，打印 task_id")

    q = sub.add_parser("query", help="查询单个任务")
    q.add_argument("--task-id", required=True)
    q.add_argument("--out", help="视频下载路径（任务 succeeded 时）")
    l = sub.add_parser("list", help="任务列表")
    c = sub.add_parser("cancel", help="取消或删除任务")
    c.add_argument("--task-id", required=True)

    args = ap.parse_args()

    if args.cmd == "check":
        sys.exit(check())

    if args.cmd == "generate":
        if not (4 <= args.duration <= 15):
            sys.exit("duration 取值 4~15（H3-Max 5~15）")
        payload: dict = {
            "model": args.model,
            "content": build_content(args.prompt, args.first_frame, args.last_frame,
                                     args.reference_image),
            "resolution": args.resolution,
            "duration": args.duration,
        }
        if args.ratio:
            payload["ratio"] = args.ratio
        elif not (args.first_frame or args.last_frame or args.reference_image):
            sys.exit("文生视频必填 --ratio（且不能为 adaptive）；图生/参考生视频可省略")
        res = call("POST", "/v2/video_generation", payload)
        task_id = res.get("task_id")
        print("task_id:", task_id, flush=True)
        if args.async_only:
            sys.exit(0)
        body = wait_task(task_id, args.wait)
        task = body.get("task") or body
        if task.get("status") != "succeeded":
            sys.exit(f"任务终态 {task.get('status')}: {json.dumps(body, ensure_ascii=False)[:500]}")
        url = (task.get("content") or {}).get("url")
        if not url:
            sys.exit(f"成功但无视频地址: {json.dumps(body, ensure_ascii=False)[:500]}")
        download(url, args.out)
        return

    if args.cmd == "query":
        body = call("GET", f"/v2/video_generation/{args.task_id}")
        print(json.dumps(body, ensure_ascii=False, indent=2)[:1200])
        task = body.get("task") or body
        url = (task.get("content") or {}).get("url")
        if args.out and url:
            download(url, args.out)
        return

    if args.cmd == "list":
        print(json.dumps(call("GET", "/v2/video_generation"), ensure_ascii=False, indent=2)[:2000])
        return

    if args.cmd == "cancel":
        print(json.dumps(call("DELETE", f"/v2/video_generation/{args.task_id}"),
                         ensure_ascii=False, indent=2)[:800])
        return


if __name__ == "__main__":
    main()
