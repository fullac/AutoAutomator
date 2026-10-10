import pathlib
import platform
import plistlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == 'Darwin', 'requires macOS Automator')
class WorkflowTest(unittest.TestCase):
    def test_text_stdin_and_service_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            source = root / 'text.sh'
            source.write_text('/bin/cat\n')
            text = '中文 "quote"\nsecond line $() `literal`'
            for replaces in (False, True):
                output = root / str(replaces)
                command = ['python3', str(ROOT / 'scripts/build_workflow.py'), '--script', str(source),
                           '--type', 'quick-action', '--input', 'text', '--output', str(output)]
                if replaces:
                    command.append('--output-replaces-selection')
                built = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(built.returncode, 0, built.stderr)
                bundle = output / 'AutoAutomator Task.workflow'
                doc = plistlib.loads((bundle / 'Contents/document.wflow').read_bytes())
                service = plistlib.loads((bundle / 'Contents/Info.plist').read_bytes())['NSServices'][0]
                self.assertEqual(service['NSSendTypes'], ['public.utf8-plain-text'])
                self.assertNotIn('NSRequiredContext', service)
                self.assertEqual('NSReturnTypes' in service, replaces)
                self.assertEqual(doc['workflowMetaData']['serviceOutputTypeIdentifier'],
                                 'com.apple.Automator.text' if replaces else 'com.apple.Automator.nothing')
                result = subprocess.run(['/usr/bin/automator', '-i', text, str(bundle)], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('中文', result.stdout)
                # Execute the embedded command with exact stdin bytes too: no text is interpolated into code.
                parameters = doc['actions'][0]['action']['ActionParameters']
                result = subprocess.run([parameters['shell'], '-c', parameters['COMMAND_STRING']], input=text, capture_output=True, text=True)
                self.assertEqual(result.stdout, text)

    def test_no_input_custom_app_and_invalid_replace(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            source = root / 'task.sh'
            source.write_text('exit 0\n')
            base = ['python3', str(ROOT / 'scripts/build_workflow.py'), '--script', str(source), '--type', 'quick-action']
            output = root / 'none'
            result = subprocess.run(base + ['--input', 'none', '--app', 'com.apple.TextEdit', '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            service = plistlib.loads((output / 'AutoAutomator Task.workflow/Contents/Info.plist').read_bytes())['NSServices'][0]
            self.assertEqual(service['NSRequiredContext']['NSApplicationIdentifier'], 'com.apple.TextEdit')
            self.assertNotIn('NSSendTypes', service)
            result = subprocess.run(base + ['--output-replaces-selection', '--output', str(root / 'invalid')], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / 'invalid').exists())

    def test_each_type_passes_input_as_arguments(self):
        with tempfile.TemporaryDirectory(prefix='AutoAutomator workflow 中文 ') as folder:
            root = pathlib.Path(folder)
            receipts = root / 'receipts'
            receipts.mkdir()
            item = root / "quote' 中文$.txt"
            item.touch()
            for kind in ('workflow', 'quick-action', 'folder-action'):
                with self.subTest(kind=kind):
                    output = root / kind
                    command = ['python3', str(ROOT / 'scripts/build_workflow.py'), '--script',
                               str(ROOT / 'scripts/record_paths.sh'), '--type', kind,
                               '--arg=' + str(receipts), '--output', str(output)]
                    built = subprocess.run(command, capture_output=True, text=True)
                    self.assertEqual(built.returncode, 0, built.stderr)
                    bundle = output / 'AutoAutomator Task.workflow'
                    result = subprocess.run(['/usr/bin/automator', '-i', str(item), str(bundle)],
                                            capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    files = list(receipts.iterdir())
                    self.assertEqual(len(files), ('workflow', 'quick-action', 'folder-action').index(kind) + 1)
                    self.assertTrue(all(p.read_bytes() == str(item).encode() + b'\0' for p in files))
                    if kind == 'quick-action':
                        info = plistlib.loads((bundle / 'Contents/Info.plist').read_bytes())
                        self.assertEqual(info['NSServices'][0]['NSMessage'], 'runWorkflowAsService')
                    again = subprocess.run(command, capture_output=True, text=True)
                    self.assertNotEqual(again.returncode, 0)

    def test_task_failure_is_visible(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            output = root / 'delivery'
            built = subprocess.run(['python3', str(ROOT / 'scripts/build_workflow.py'), '--script',
                                    str(ROOT / 'scripts/list_files.sh'), '--output', str(output)],
                                   capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            result = subprocess.run(['/usr/bin/automator', str(output / 'AutoAutomator Task.workflow')],
                                    capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('usage: list_files.sh', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
