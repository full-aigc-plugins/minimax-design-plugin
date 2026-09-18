"""Unit tests for scripts/minimax_video.py (offline: no network, no key)."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("minimax_video", ROOT / "scripts" / "minimax_video.py")
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)


class CheckTests(unittest.TestCase):
    def test_check_without_key_reports_actionable_guidance(self, ) -> None:
        import os
        old = os.environ.pop("MINIMAX_API_KEY", None)
        try:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = mm.check()
            out = buf.getvalue()
            self.assertEqual(rc, 0, "check 永远 exit 0（advisory）")
            self.assertIn("未设置", out)
            self.assertIn("platform.minimaxi.com", out, "必须给出可操作的申请地址")
            self.assertIn("export MINIMAX_API_KEY=", out, "必须给出可操作的配置命令")
        finally:
            if old is not None:
                os.environ["MINIMAX_API_KEY"] = old

    def test_check_with_key_masks_secret(self) -> None:
        import os
        import io
        import contextlib
        os.environ["MINIMAX_API_KEY"] = "sk-test-abcdef1234"
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                mm.check()
            out = buf.getvalue()
            self.assertIn("已设置", out)
            self.assertIn("1234", out, "只显示尾号")
            self.assertNotIn("sk-test-abcdef1234", out, "完整密钥禁止回显")
        finally:
            os.environ.pop("MINIMAX_API_KEY", None)


class PayloadTests(unittest.TestCase):
    def test_encode_image_local_file_is_base64_data_url(self) -> None:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG fake")
            path = f.name
        encoded = mm.encode_image(path)
        self.assertTrue(encoded.startswith("data:image/png;base64,"))

    def test_encode_image_url_passes_through(self) -> None:
        self.assertEqual(mm.encode_image("https://example.com/a.png"),
                         "https://example.com/a.png")


class ApiGuardTests(unittest.TestCase):
    def test_api_without_key_exits_with_guidance(self) -> None:
        import os
        old = os.environ.pop("MINIMAX_API_KEY", None)
        try:
            with self.assertRaises(SystemExit) as ctx:
                mm.api("/v1/video_generation", {})
            self.assertIn("MINIMAX_API_KEY", str(ctx.exception))
        finally:
            if old is not None:
                os.environ["MINIMAX_API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
