import json
import pathlib
import platform
import plistlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == "Darwin", "requires macOS osacompile")
class AppTest(unittest.TestCase):
    def test_droplet_open_event_and_double_click(self):
        with tempfile.TemporaryDirectory(prefix='AutoAutomator drops ') as folder:
            root = pathlib.Path(folder)
            receipt = root / 'args.bin'
            source = root / 'task.sh'
            source.write_text('out=$1; shift\n: > "$out"\nfor item in "$@"; do printf "%s\\0" "$item" >> "$out"; done\n')
            items = [root / "space 中文 quote'\"$.txt", root / 'second.txt', root / 'folder 中文']
            for item in items[:2]:
                item.touch()
            items[2].mkdir()
            output = root / 'delivery'
            built = subprocess.run(['python3', str(ROOT / 'scripts/build_app.py'), '--shell-script', str(source),
                                    '--name', 'AutoAutomator Drop Test', '--accept-drops', '--arg=' + str(receipt),
                                    '--arg=fixed literal', '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            app = output / 'AutoAutomator Drop Test.app'
            info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
            self.assertEqual(info['CFBundleDocumentTypes'][0]['LSItemContentTypes'], ['public.item'])
            result = subprocess.run(['/usr/bin/open', '-W', '-n', '-a', str(app)] + [str(p) for p in items], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = receipt.read_bytes().split(b'\0')[:-1]
            self.assertEqual(paths[0], b'fixed literal')
            self.assertEqual([p.rstrip(b'/') for p in paths[1:]], [str(p.resolve()).encode() for p in items])
            result = subprocess.run(['/usr/bin/open', '-W', '-n', str(app)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(receipt.read_bytes(), b'fixed literal\0')

    def test_identity_and_log_survive_rebuild(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            source = root / 'task.sh'
            source.write_text('exit 0\n')
            command = ['python3', str(ROOT / 'scripts/build_app.py'), '--shell-script', str(source), '--name', '中文 App']
            records = []
            for i in range(2):
                output = root / str(i)
                result = subprocess.run(command + ['--output', str(output)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                info = plistlib.loads((output / '中文 App.app/Contents/Info.plist').read_bytes())
                record = json.loads((output / 'build.json').read_text())
                self.assertEqual(info['CFBundleIdentifier'], record['bundle_id'])
                self.assertIn(record['bundle_id'], record['rebuild'])
                records.append(record)
            self.assertEqual(records[0]['bundle_id'], records[1]['bundle_id'])
            self.assertEqual(records[0]['log'], records[1]['log'])
            result = subprocess.run(command + ['--bundle-id', 'org.example.stable', '--output', str(root / 'explicit')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((root / 'explicit/build.json').read_text())['bundle_id'], 'org.example.stable')
            bad = root / 'bad'
            result = subprocess.run(command + ['--bundle-id', '../invalid', '--output', str(bad)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(bad.exists())

    def test_build_preserves_source_and_refuses_existing_delivery(self):
        with tempfile.TemporaryDirectory(prefix="AutoAutomator app 中文 ") as folder:
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
