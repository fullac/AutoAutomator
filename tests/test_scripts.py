import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ListFilesTest(unittest.TestCase):
    def run_list(self, source, output):
        return subprocess.run(['/bin/zsh', str(ROOT / 'scripts/list_files.sh'), str(source), str(output)],
                              capture_output=True, text=True)

    def test_empty_and_missing_input(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            source = root / 'empty'
            source.mkdir()
            output = root / 'result.txt'
            result = self.run_list(source, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), b'')
            missing_output = root / 'should-not-exist.txt'
            self.assertEqual(self.run_list(root / 'missing', missing_output).returncode, 66)
            self.assertFalse(missing_output.exists())

    def test_unreadable_input_is_not_an_empty_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            source = root / 'input'
            source.mkdir()
            (source / 'private.txt').touch()
            source.chmod(0)
            try:
                output = root / 'result.txt'
                result = self.run_list(source, output)
                self.assertEqual(result.returncode, 77, result.stderr)
                self.assertFalse(output.exists())
            finally:
                source.chmod(0o700)

    def test_dangling_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            source = root / 'input'
            source.mkdir()
            link = root / 'result.txt'
            target = root / 'not-created.txt'
            link.symlink_to(target)
            result = self.run_list(source, link)
            self.assertEqual(result.returncode, 73, result.stderr)
            self.assertTrue(link.is_symlink())
            self.assertFalse(target.exists())

    def test_path_receipt_supports_newline_and_missing_input(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            receipts = root / 'receipts'
            receipts.mkdir()
            item = root / 'line\nname.txt'
            item.touch()
            command = ['/bin/zsh', str(ROOT / 'scripts/record_paths.sh'), str(receipts)]
            result = subprocess.run(command + [str(item)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(next(receipts.iterdir()).read_bytes(), str(item).encode() + b'\0')
            result = subprocess.run(command + [str(root / 'missing')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 66)
            self.assertEqual(len(list(receipts.iterdir())), 1)

    def test_names_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="AutoAutomator 中文 ") as folder:
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
