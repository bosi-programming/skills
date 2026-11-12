import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "build-index.py"
SPEC = importlib.util.spec_from_file_location("build_index", SCRIPT)
build_index = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_index)


def make_skill(root):
    skill = Path(root) / "sample"
    (skill / "scripts").mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: sample\n---\n")
    (skill / "scripts" / "check.py").write_text("print(1)\n")
    return skill


def add_cache(skill):
    cache = skill / "scripts" / "__pycache__"
    cache.mkdir()
    (cache / "check.cpython-312.pyc").write_bytes(b"\x00\x01")


class FilesOf(unittest.TestCase):
    def test_skips_pycache(self):
        with tempfile.TemporaryDirectory() as root:
            skill = make_skill(root)
            add_cache(skill)
            self.assertEqual(build_index.files_of(skill), ["SKILL.md", "scripts/check.py"])

    def test_version_ignores_pycache(self):
        with tempfile.TemporaryDirectory() as root:
            skill = make_skill(root)
            before = build_index.version_of(skill)
            add_cache(skill)
            self.assertEqual(build_index.version_of(skill), before)


if __name__ == "__main__":
    unittest.main()
