#!/usr/bin/env python3
"""MiniMax 海螺视频生成客户端（Hailuo-02 / 2.3，video_generation 异步任务）。

用法:
  export MINIMAX_API_KEY=...            # platform.minimaxi.com 或 platform.minimax.io 申请
  python3 minimax_video.py t2v --prompt "..." --out shot-01.mp4
  python3 minimax_video.py i2v --first-frame first.png [--last-frame last.png] \
      --prompt "..." --out shot-01.mp4
  python3 minimax_video.py query --task-id <id>

说明:
  - 端点: 国内 https://api.minimaxi.com  /  国际 https://api.minimax.io
    用 MINIMAX_BASE 覆盖。鉴权: Bearer MINIMAX_API_KEY。
  - 模型: MiniMax-Hailuo-02（另有 2.3 系列，同一端点）。分辨率 768P/1080P，
    时长 6s/10s（1080P 仅 6s）。
  - i2v: first_frame_image 支持本地文件（自动 base64）或 URL；
    last_frame_image 尾帧同理（首尾帧模式 = 白模预演的逐镜锚定）。
  - 异步: POST /v1/video_generation 建 task → 轮询 GET /v1/query/video_generation
    → file_id → GET /v1/files/retrieve 换下载链接。
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import sys
import time
import urllib.request

BASE = os.environ.get("MINIMAX_BASE", "https://api.minimaxi.com")
MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-Hailuo-02")


def check() -> int:
    """能力预检：鉴权与依赖是否就绪。永远 exit 0，只输出可操作的状态行。"""
    key = os.environ.get("MINIMAX_API_KEY")
    lines = []
    if key:
        lines.append(f"MINIMAX_API_KEY: 已设置（尾号 {key[-4:]}）")
        lines.append(f"网关: {BASE}")
    else:
        lines.append("MINIMAX_API_KEY: 未设置")
        lines.append("  获取: https://platform.minimaxi.com （国内）或 https://platform.minimax.io （国际）"
                     "→ 用户中心 → 接口密钥")
        lines.append("  配置: export MINIMAX_API_KEY=你的密钥   # 建议写入 shell 配置或项目 .env")
    mmx = shutil.which("mmx")
    lines.append(f"mmx CLI: {mmx}" if mmx else
                 "mmx CLI: 未安装（可选，minimax-multimodal-toolkit 技能需要；"
                 "npm install -g mmx-cli 后 `mmx auth login --api-key sk-...`）")
    creds = os.path.expanduser("~/.mmx/credentials.json")
    lines.append("mmx 凭据: 已登录" if os.path.isfile(creds) else "mmx 凭据: 未登录（可选）")
    print("MiniMax 设计插件环境：" + "；".join(lines))
    return 0


def api(path: str, payload: dict) -> dict:
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        sys.exit("缺 MINIMAX_API_KEY 环境变量（platform.minimaxi.com → 接口密钥）")
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.loads(r.read())
    if body.get("base_resp", {}).get("status_code", 0) != 0:
        sys.exit(f"API 错误: {body.get('base_resp')}")
    return body


def encode_image(path: str) -> str:
    if path.startswith(("http://", "https://")):
        return path
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def create_task(args) -> dict:
    payload = {"model": MODEL, "prompt": args.prompt,
               "duration": args.duration, "resolution": args.resolution,
               "prompt_optimizer": True}
    if args.mode == "i2v":
        payload["first_frame_image"] = encode_image(args.first_frame)
        if args.last_frame:
            payload["last_frame_image"] = encode_image(args.last_frame)
    return api("/v1/video_generation", payload)


def download(url: str, out: str) -> None:
    urllib.request.urlretrieve(url, out)
    print("downloaded:", out)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="能力预检（鉴权/依赖，exit 0）")

    t2v = sub.add_parser("t2v")
    t2v.add_argument("--prompt", required=True)
    i2v = sub.add_parser("i2v")
    i2v.add_argument("--first-frame", required=True)
    i2v.add_argument("--last-frame")
    for p in (t2v, i2v):
        p.add_argument("--out", required=True)
        p.add_argument("--duration", type=int, default=6, choices=[6, 10])
        p.add_argument("--resolution", default="768P", choices=["768P", "1080P"])
        p.add_argument("--wait", type=int, default=600, help="最长轮询秒数")

    q = sub.add_parser("query")
    q.add_argument("--task-id", required=True)
    q.add_argument("--out")

    args = ap.parse_args()

    if args.cmd == "check":
        sys.exit(check())

    if args.cmd == "query":
        body = api("/v1/query/video_generation", {"task_id": args.task_id})
        print(json.dumps(body, ensure_ascii=False, indent=2)[:800])
        sys.exit(0)

    res = create_task(args)
    task_id = res.get("task_id")
    print("task_id:", task_id, flush=True)

    deadline = time.time() + args.wait
    file_id = None
    while time.time() < deadline:
        time.sleep(10)
        q = api("/v1/query/video_generation", {"task_id": task_id})
        status = (q.get("data") or {}).get("status") or q.get("status")
        print("status:", status, flush=True)
        if status == "Fail":
            sys.exit(f"生成失败: {json.dumps(q, ensure_ascii=False)[:500]}")
        if status == "Success":
            file_id = (q.get("data") or {}).get("file_id") or q.get("file_id")
            break
    if not file_id:
        sys.exit(f"超时未完成，task_id={task_id}（可稍后 query --task-id 续查）")

    f = api("/v1/files/retrieve", {"file_id": file_id})
    url = (f.get("data") or {}).get("file", {}).get("download_url") or f.get("file", {}).get("download_url")
    if not url:
        sys.exit(f"拿不到下载链接: {json.dumps(f, ensure_ascii=False)[:400]}")
    download(url, args.out)


if __name__ == "__main__":
    main()
