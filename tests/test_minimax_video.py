"""Unit tests for scripts/minimax_video.py v2 (offline: no network, no key)."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("minimax_video", ROOT / "scripts" / "minimax_video.py")
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)


class CheckTests(unittest.TestCase):
    def test_check_without_key_reports_actionable_guidance(self) -> None:
        import contextlib
        import io
        import os
        old = os.environ.pop("MINIMAX_API_KEY", None)
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = mm.check()
            out = buf.getvalue()
            self.assertEqual(rc, 0, "check 永远 exit 0（advisory）")
            self.assertIn("未设置", out)
            self.assertIn("platform.minimax.cn", out, "必须给出可操作的申请地址")
            self.assertIn("export MINIMAX_API_KEY=", out, "必须给出可操作的配置命令")
            self.assertIn("mmx-cli", out, "必须提示 mmx 安装路径")
        finally:
            if old is not None:
                os.environ["MINIMAX_API_KEY"] = old

    def test_check_with_key_masks_secret(self) -> None:
        import contextlib
        import io
        import os
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


class ContentBuilderTests(unittest.TestCase):
    def test_t2v_content_is_text_only(self) -> None:
        c = mm.build_content("一个男孩在海边打篮球", None, None, [])
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]["type"], "text")

    def test_fl2v_roles_are_exact(self) -> None:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG first")
            first = f.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG last")
            last = f.name
        c = mm.build_content("路径描述", first, last, [])
        self.assertEqual([x.get("role") for x in c if x["type"] == "image_url"],
                         ["first_frame", "last_frame"])
        for x in c:
            if x["type"] == "image_url":
                self.assertIn("url", x["image_url"])

    def test_local_frame_becomes_data_url(self) -> None:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG fake")
            c = mm.build_content("p", f.name, None, [])
        url = c[1]["image_url"]["url"]
        self.assertTrue(url.startswith("data:image/png;base64,"))

    def test_reference_mode_mutually_exclusive_with_fl2v(self) -> None:
        with self.assertRaises(SystemExit):
            mm.build_content("p", "first.png", None, ["ref.png"])

    def test_url_frames_pass_through(self) -> None:
        c = mm.build_content("p", "https://example.com/a.png", None, [])
        self.assertEqual(c[1]["image_url"]["url"], "https://example.com/a.png")


class ApiGuardTests(unittest.TestCase):
    def test_api_without_key_exits_with_guidance(self) -> None:
        import os
        old = os.environ.pop("MINIMAX_API_KEY", None)
        try:
            with self.assertRaises(SystemExit) as ctx:
                mm.call("POST", "/v2/video_generation", {})
            self.assertIn("MINIMAX_API_KEY", str(ctx.exception))
        finally:
            if old is not None:
                os.environ["MINIMAX_API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
