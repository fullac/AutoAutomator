import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ListFilesTest(unittest.TestCase):
    def test_names_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="AMCreate 中文 ") as folder:
            root = pathlib.Path(folder)
            source = root / "input"
            source.mkdir()
            names = ["中文.txt", "space name.txt", "quote'$.txt", ".hidden"]
            for name in names:
                (source / name).touch()
            (source / "directory").mkdir()
            output = root / "result.txt"
            command = ["/bin/zsh", str(ROOT / "scripts/list_files.sh"), str(source), str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(set(output.read_text().splitlines()), set(names))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 73)
            self.assertEqual(set(output.read_text().splitlines()), set(names))


if __name__ == "__main__":
    unittest.main()
