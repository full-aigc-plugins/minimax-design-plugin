"""Vendor gate tests: vendored skills match skills.lock.json digests.

Adapted from the blender plugin pattern; runs the vendor script as a
subprocess the way CI does, plus tamper detection (mutation checks).
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "vendor" / "skill_vendor.py"
LOCK = ROOT / "skills.lock.json"


def run_vendor(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=120,
    )


class VendorCheckTests(unittest.TestCase):
    def test_offline_check_passes_on_clean_tree(self) -> None:
        r = run_vendor("check", "--offline", "--lock", str(LOCK))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("all managed skills match", r.stdout)

    def test_tampered_skill_body_is_detected(self) -> None:
        """Mutation check: a gate that cannot catch tampering proves nothing."""
        target = ROOT / "skills" / "minimax-music-gen" / "SKILL.md"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\n<!-- tampered -->\n")
            r = run_vendor("check", "--offline", "--lock", str(LOCK))
            self.assertNotEqual(r.returncode, 0, "篡改必须被摘要校验拦下")
        finally:
            target.write_bytes(original)
        r = run_vendor("check", "--offline", "--lock", str(LOCK))
        self.assertEqual(r.returncode, 0, "还原后必须恢复通过")

    def test_deleted_vendored_skill_is_detected(self) -> None:
        import shutil
        target = ROOT / "skills" / "minimax-music-playlist"
        original = target.read_bytes() if False else None
        backup = Path(str(target) + ".bak")
        shutil.copytree(target, backup)
        try:
            shutil.rmtree(target)
            r = run_vendor("check", "--offline", "--lock", str(LOCK))
            self.assertNotEqual(r.returncode, 0, "缺失技能必须被拦下")
        finally:
            shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(backup, target)
            shutil.rmtree(backup)
        r = run_vendor("check", "--offline", "--lock", str(LOCK))
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
