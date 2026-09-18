#!/usr/bin/env python3
"""Distribution validator for partme-minimax-design.

Checks what the three platform loaders and the vendor gate actually rely on:
manifest identity, skills frontmatter, vendor lock digests, hook wiring, and
the legal file set. Exits 0 only when every check passes.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ID = "minimax-design"
REPOSITORY = "https://github.com/partme-ai/partme-minimax-design"
LEGAL = ("LICENSE", "NOTICE", "PRIVACY.md", "README.md", "README.zh-CN.md",
         "TERMS.md", "THIRD_PARTY_NOTICES.md")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def load_json(rel: str) -> dict:
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{rel}: invalid JSON ({exc})")
        raise


def kebab(name: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name or ""))


def main() -> int:
    codex = load_json(".codex-plugin/plugin.json")
    zcode = load_json(".zcode-plugin/plugin.json")
    kimi = load_json("kimi.plugin.json")
    market = load_json(".agents/plugins/marketplace.json")

    if codex.get("name") != PLUGIN_ID or not kebab(PLUGIN_ID):
        fail(f"codex manifest name must be '{PLUGIN_ID}'")
    if codex.get("repository") != REPOSITORY:
        fail("codex manifest repository mismatch")
    version = codex.get("version", "")
    if not re.match(r"\d+\.\d+\.\d+", version):
        fail(f"codex manifest version not semver: {version}")
    for label, m in (("zcode", zcode), ("kimi", kimi)):
        if m.get("name") != PLUGIN_ID or m.get("version") != version:
            fail(f"{label} manifest name/version must match codex manifest")
    entry = market["plugins"][0]
    if entry.get("name") != PLUGIN_ID or entry.get("version") != version:
        fail("marketplace entry name/version must match codex manifest")

    for legal in LEGAL:
        if not (ROOT / legal).is_file():
            fail(f"missing legal file: {legal}")

    skills_dir = ROOT / "skills"
    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        md = skill_dir / "SKILL.md"
        if not md.is_file():
            fail(f"skills/{skill_dir.name}: directory without SKILL.md")
        text = md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.+?)\n---\n", text, re.DOTALL)
        if not m:
            fail(f"skills/{skill_dir.name}: missing frontmatter")
        block = m.group(1)
        names = re.findall(r"^name: (\S+)$", block, re.MULTILINE)
        if names != [skill_dir.name]:
            fail(f"skills/{skill_dir.name}: frontmatter name must equal directory name")
        descs = re.findall(r"^description: ", block, re.MULTILINE)
        if len(descs) != 1:
            fail(f"skills/{skill_dir.name}: exactly one description key required")
        if re.search(r"^description: [|>]", block, re.MULTILINE):
            fail(f"skills/{skill_dir.name}: block-scalar description banned")

    lock = load_json("skills.lock.json")
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts/vendor/skill_vendor.py"), "check", "--offline",
         "--lock", str(ROOT / "skills.lock.json")],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        fail(f"vendor digests mismatch: {res.stdout + res.stderr}")

    hooks = load_json("hooks/hooks.json")
    for event in ("SessionStart", "UserPromptSubmit"):
        if event not in hooks.get("hooks", {}):
            fail(f"hooks.json missing {event}")
    for hook_file in ("hooks/env_check.py", "hooks/check_minimax_intent.py"):
        if not (ROOT / hook_file).is_file():
            fail(f"missing hook script: {hook_file}")

    print(f"validated {PLUGIN_ID} {version}: "
          f"{len(list(skills_dir.iterdir()))} skills, {len(lock['sources'])} vendor sources, hooks wired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
