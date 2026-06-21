import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class RunScriptTests(unittest.TestCase):
    def test_build_command_uses_detected_python_and_script_path(self):
        from run import build_command

        cmd = build_command("doctor.py", ["--mode", "format"], python_exe="/opt/hermes/python")

        self.assertEqual(cmd[0], "/opt/hermes/python")
        self.assertEqual(Path(cmd[1]).name, "doctor.py")
        self.assertEqual(cmd[2:], ["--mode", "format"])

    def test_rejects_unknown_script_name(self):
        from run import build_command

        with self.assertRaises(SystemExit):
            build_command("missing.py", [], python_exe="/opt/hermes/python")


if __name__ == "__main__":
    unittest.main()
