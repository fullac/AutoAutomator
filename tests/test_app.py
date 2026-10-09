import json
import pathlib
import platform
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == "Darwin", "requires macOS osacompile")
class AppTest(unittest.TestCase):
    def test_build_preserves_source_and_refuses_existing_delivery(self):
        with tempfile.TemporaryDirectory(prefix="AMCreate app 中文 ") as folder:
            output = pathlib.Path(folder) / "delivery"
            command = ["python3", str(ROOT / "scripts/build_app.py"), "--shell-script",
                       str(ROOT / "scripts/list_files.sh"), "--arg=quote'\"$ value",
                       "--name", "中文 App", "--output", str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "中文 App.app/Contents/MacOS/applet").is_file())
            self.assertEqual((output / "source/task.sh").read_bytes(),
                             (ROOT / "scripts/list_files.sh").read_bytes())
            record = json.loads((output / "build.json").read_text())
            self.assertEqual(record["arguments"], ["quote'\"$ value"])
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((output / "source/task.sh").is_file())

    def test_bad_applescript_leaves_no_delivery(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            source = root / "bad.applescript"
            source.write_text("this is not valid AppleScript !!!")
            result = subprocess.run(["python3", str(ROOT / "scripts/build_app.py"),
                                     "--source", str(source), "--output", str(root / "delivery")],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("error", result.stderr)
            self.assertFalse((root / "delivery").exists())


if __name__ == "__main__":
    unittest.main()
