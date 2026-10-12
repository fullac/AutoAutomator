import copy
import importlib.util
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installation', ROOT / 'scripts/installation.py')
installation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installation)


class InstallationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.destinations = {k: self.root / k for k in installation.TYPES}
        self.state = {'enabled': False, 'actions': []}
        for name, value in [('STATE', self.root / 'state'), ('DESTINATIONS', self.destinations)]:
            patcher = patch.object(installation, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name, value in [('folder_request', self.request), ('refresh', lambda: None)]:
            patcher = patch.object(installation, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def request(self, operation, **values):
        action = next((a for a in self.state['actions'] if a['path'] == values.get('folder')), None)
        if operation == 'enabled':
            self.state['enabled'] = values['enabled']
        elif operation == 'bind':
            if action is None:
                action = {'path': values['folder'], 'enabled': True, 'scripts': []}
                self.state['actions'].append(action)
            action['scripts'].append({'path': values['script'], 'enabled': True})
            action['enabled'] = True
            self.state['enabled'] = True
        elif operation == 'unbind' and action:
            action['scripts'] = [s for s in action['scripts'] if s['path'] != values['script']]
            if values['created'] and not action['scripts']:
                self.state['actions'].remove(action)
            elif not values['created']:
                action['enabled'] = values['previousEnabled']
        return copy.deepcopy(self.state)

    def bundle(self, kind, name='Example'):
        bundle = self.root / (name + '.workflow')
        contents = bundle / 'Contents'
        contents.mkdir(parents=True)
        (contents / 'document.wflow').write_bytes(plistlib.dumps({'workflowMetaData': {
            'workflowTypeIdentifier': installation.TYPES[kind]}}))
        if kind == 'quick-action':
            (contents / 'Info.plist').write_bytes(plistlib.dumps({'NSServices': [{'NSMessage': 'runWorkflowAsService'}]}))
        return bundle

    def test_service_round_trip_and_existing_destination(self):
        bundle = self.bundle('quick-action')
        result = installation.install(bundle)
        dest = Path(result['destination'])
        self.assertEqual((dest / 'Contents/document.wflow').read_bytes(), (bundle / 'Contents/document.wflow').read_bytes())
        with self.assertRaisesRegex(ValueError, 'already exists'):
            installation.install(bundle)
        with self.assertRaises(ValueError):
            installation.uninstall('../Example')
        installation.uninstall(result['id'])
        self.assertFalse(dest.exists())
        self.assertEqual(installation.uninstall(result['id'])['status'], 'already uninstalled')

    def test_modified_installation_is_preserved(self):
        result = installation.install(self.bundle('quick-action'))
        dest = Path(result['destination'])
        (dest / 'custom.txt').write_text('user change')
        with self.assertRaisesRegex(ValueError, 'modified'):
            installation.uninstall(result['id'])
        self.assertTrue(dest.exists())

    def test_folder_round_trip_preserves_existing_bindings_and_enabled_state(self):
        folder = self.root / 'watched'; folder.mkdir()
        self.state['actions'] = [{'path': str(folder), 'enabled': True,
                                 'scripts': [{'path': '/user/original.scpt', 'enabled': False}]}]
        original = copy.deepcopy(self.state)
        result = installation.install(self.bundle('folder-action'), folder)
        self.assertTrue(self.state['enabled'])
        self.assertEqual(len(self.state['actions'][0]['scripts']), 2)
        installation.uninstall(result['id'])
        self.assertEqual(self.state, original)

    def test_multiple_folder_installs_restore_after_last_uninstall(self):
        folder = self.root / 'watched'; folder.mkdir()
        original = copy.deepcopy(self.state)
        one = installation.install(self.bundle('folder-action', 'One'), folder)
        two = installation.install(self.bundle('folder-action', 'Two'), folder)
        installation.uninstall(one['id'])
        self.assertTrue(self.state['enabled'])
        self.assertEqual(len(self.state['actions'][0]['scripts']), 1)
        installation.uninstall(two['id'])
        self.assertEqual(self.state, original)

    def test_disabled_existing_scripts_are_not_activated(self):
        folder = self.root / 'watched'; folder.mkdir()
        self.state['actions'] = [{'path': str(folder), 'enabled': False,
                                 'scripts': [{'path': '/user/original.scpt', 'enabled': True}]}]
        original = copy.deepcopy(self.state)
        with self.assertRaisesRegex(ValueError, 'disabled scripts'):
            installation.install(self.bundle('folder-action'), folder)
        self.assertEqual(self.state, original)
        self.assertFalse((self.destinations['folder-action'] / 'Example.workflow').exists())

    def test_failure_rolls_back_copied_bundle_and_partial_binding(self):
        folder = self.root / 'watched'; folder.mkdir()
        original = copy.deepcopy(self.state)
        def fail(operation, **values):
            result = self.request(operation, **values)
            if operation == 'bind':
                raise RuntimeError('failed after binding')
            return result
        with patch.object(installation, 'folder_request', fail):
            with self.assertRaisesRegex(RuntimeError, 'failed after binding'):
                installation.install(self.bundle('folder-action'), folder)
        self.assertEqual(self.state, original)
        self.assertFalse((self.destinations['folder-action'] / 'Example.workflow').exists())

    def test_external_binding_change_does_not_disable_other_work(self):
        folder = self.root / 'watched'; folder.mkdir()
        result = installation.install(self.bundle('folder-action'), folder)
        self.state['actions'].append({'path': '/another/folder', 'enabled': True, 'scripts': []})
        result = installation.uninstall(result['id'])
        self.assertTrue(self.state['enabled'])
        self.assertIn('changed', result['warning'])

    def test_failed_restoration_can_be_retried(self):
        folder = self.root / 'watched'; folder.mkdir()
        result = installation.install(self.bundle('folder-action'), folder)
        def fail(operation, **values):
            if operation == 'enabled':
                raise RuntimeError('restore failed')
            return self.request(operation, **values)
        with patch.object(installation, 'folder_request', fail):
            with self.assertRaisesRegex(RuntimeError, 'restore failed'):
                installation.uninstall(result['id'])
        record = json.loads(Path(result['receipt']).read_text())
        self.assertEqual(record['status'], 'installed')
        installation.uninstall(result['id'])
        self.assertFalse(self.state['enabled'])


if __name__ == '__main__':
    unittest.main()
