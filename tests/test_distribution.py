"""Distribution contract tests for partme-minimax-design."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys_path = ROOT / "scripts"
import sys  # noqa: E402

sys.path.insert(0, str(sys_path))

import validate_distribution  # noqa: E402


class DistributionTests(unittest.TestCase):
    def test_validator_accepts_distribution(self) -> None:
        self.assertEqual(validate_distribution.main(), 0)

    def test_manifest_identity(self) -> None:
        import json
        manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "minimax-design")
        self.assertEqual(manifest["repository"],
                         "https://github.com/partme-ai/partme-minimax-design")

    def test_zcode_and_kimi_versions_match(self) -> None:
        import json
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        for rel in (".zcode-plugin/plugin.json", "kimi.plugin.json"):
            m = json.loads((ROOT / rel).read_text())
            self.assertEqual(m["name"], codex["name"], rel)
            self.assertEqual(m["version"], codex["version"], rel)

    def test_vendored_skills_match_lock(self) -> None:
        import json
        lock = json.loads((ROOT / "skills.lock.json").read_text())
        for source in lock["sources"]:
            for name, digest in source["sha256"].items():
                self.assertTrue((ROOT / "skills" / name / "SKILL.md").is_file(),
                                f"missing vendored skill {name}")


if __name__ == "__main__":
    unittest.main()
