import pathlib
import platform
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == 'Darwin', 'requires macOS')
class DeliveryTest(unittest.TestCase):
    def test_invalid_shell_and_bad_source_leave_no_delivery(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            for builder, option in [('build_app.py', '--shell-script'), ('build_workflow.py', '--script')]:
                for extra in [['--shell=/not/installed'], []]:
                    with self.subTest(builder=builder, extra=extra):
                        source = root / 'invalid.sh'
                        source.write_text('if then\n')
                        output = root / 'delivery'
                        result = subprocess.run(['python3', str(ROOT / 'scripts' / builder), option,
                                                 str(source), '--output', str(output)] + extra,
                                                capture_output=True, text=True)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertFalse(output.exists())

    def test_dependency_report(self):
        for kind in ['script', 'app', 'workflow']:
            result = subprocess.run(['python3', str(ROOT / 'scripts/doctor.py'), '--requires', kind],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
