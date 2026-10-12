"""Owned macOS service installation with receipts and reversible folder bindings."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import uuid

LIBRARY = Path.home() / 'Library'
STATE = LIBRARY / 'Application Support/AutoAutomator/installations'
DESTINATIONS = {'quick-action': LIBRARY / 'Services',
                'folder-action': LIBRARY / 'Workflows/Applications/Folder Actions'}
TYPES = {'quick-action': 'com.apple.Automator.servicesMenu',
         'folder-action': 'com.apple.Automator.folderAction'}


def folder_request(operation, **values):
    result = subprocess.run(['/usr/bin/osascript', '-l', 'JavaScript',
                             str(Path(__file__).with_name('folder_actions.js')),
                             json.dumps(dict(operation=operation, **values))],
                            check=True, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout)


def refresh():
    subprocess.run(['/System/Library/CoreServices/pbs', '-update'], check=True,
                   capture_output=True, text=True, timeout=30)


@contextmanager
def locked():
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / '.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def fingerprint(bundle):
    files = {}
    for path in sorted(bundle.rglob('*')):
        if path.is_symlink():
            raise ValueError('installation does not accept symlinks in bundles')
        if path.is_file():
            files[str(path.relative_to(bundle))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def active_folders(exclude=None):
    records = [json.loads(p.read_text()) for p in STATE.glob('*.json') if p.name != 'folder-state.json']
    return [r for r in records if r.get('type') == 'folder-action'
            and r.get('status') != 'uninstalled' and r.get('id') != exclude]


def uninstall_record(record, path, rollback=False):
    dest = Path(record['destination'])
    parent = DESTINATIONS[record['type']].resolve()
    if dest.parent != parent or dest.name != record['artifact'] or dest.is_symlink():
        raise ValueError('invalid installation destination')
    if dest.exists() and not rollback:
        actual = fingerprint(dest)
        intact = actual == record['files']
        if record['status'] == 'installing':
            intact = all(record['files'].get(name) == digest for name, digest in actual.items())
        if not intact:
            raise ValueError('installed bundle was modified; preserve it and resolve changes before uninstalling')
    if record['type'] == 'folder-action':
        siblings = [r for r in active_folders(record['id']) if r['folder'] == record['folder']]
        folder_request('unbind', folder=record['folder'], script=str(dest),
                       created=record['created_action'],
                       previousEnabled=True if siblings else record['previous_action_enabled'])
    if dest.exists():
        shutil.rmtree(dest)
    warning = None
    if record['type'] == 'quick-action':
        refresh()
    baseline_path = STATE / 'folder-state.json'
    if record['type'] == 'folder-action' and not active_folders(record['id']) and baseline_path.exists():
        baseline = json.loads(baseline_path.read_text())
        current = folder_request('snapshot')
        if current['actions'] == baseline['actions']:
            folder_request('enabled', enabled=baseline['enabled'])
        else:
            warning = 'other folder bindings changed; global enabled state preserved'
        baseline_path.unlink()
    record['status'] = 'uninstalled'
    save(path, record)
    return {'id': record['id'], 'status': 'uninstalled', 'warning': warning}


def install(bundle, folder=None):
    if bundle.is_symlink():
        raise ValueError('bundle must not be a symlink')
    bundle = bundle.resolve(strict=True)
    if not bundle.is_dir() or bundle.suffix != '.workflow':
        raise ValueError('install a .workflow bundle')
    document = plistlib.loads((bundle / 'Contents/document.wflow').read_bytes())
    type_id = document['workflowMetaData']['workflowTypeIdentifier']
    kind = next((key for key, value in TYPES.items() if value == type_id), None)
    if kind is None:
        raise ValueError('only quick actions and folder actions can be installed')
    if kind == 'quick-action':
        services = plistlib.loads((bundle / 'Contents/Info.plist').read_bytes())['NSServices']
        if not services or services[0]['NSMessage'] != 'runWorkflowAsService':
            raise ValueError('missing workflow service declaration')
        if folder:
            raise ValueError('--folder is only for folder actions')
    elif not folder or not folder.resolve(strict=True).is_dir():
        raise ValueError('folder actions require --folder pointing to an existing directory')
    files = fingerprint(bundle)
    with locked():
        parent = DESTINATIONS[kind]
        parent.mkdir(parents=True, exist_ok=True)
        dest = parent.resolve() / bundle.name
        if dest.exists() or dest.is_symlink():
            raise ValueError('installation target already exists: ' + str(dest))
        previous = None
        existing = None
        peers = []
        if kind == 'folder-action':
            folder = folder.resolve(strict=True)
            previous = folder_request('snapshot')
            existing = next((a for a in previous['actions'] if a['path'] == str(folder)), None)
            peers = [r for r in active_folders() if r['folder'] == str(folder)]
            if existing and not existing['enabled'] and existing['scripts']:
                raise ValueError('target folder has disabled scripts; enabling them requires a separate user decision')
            baseline = STATE / 'folder-state.json'
            if not active_folders():
                save(baseline, previous)
        identity = uuid.uuid4().hex
        record = {'schema_version': 1, 'id': identity, 'type': kind, 'artifact': bundle.name,
                  'destination': str(dest), 'files': files, 'status': 'installing',
                  'folder': str(folder) if kind == 'folder-action' else None,
                  'previous_state': previous,
                  'created_action': peers[0]['created_action'] if peers else existing is None,
                  'previous_action_enabled': peers[0]['previous_action_enabled'] if peers else (existing['enabled'] if existing else False)}
        receipt = STATE / (identity + '.json')
        # Reserve the destination exclusively before recording ownership.
        dest.mkdir()
        try:
            save(receipt, record)
            shutil.copytree(bundle, dest, dirs_exist_ok=True)
            if fingerprint(dest) != files:
                raise ValueError('bundle changed during installation')
            if kind == 'quick-action':
                refresh()
            else:
                folder_request('bind', folder=str(folder), script=str(dest))
            record['status'] = 'installed'
            save(receipt, record)
        except BaseException as error:
            # If cleanup fails, the receipt stays available for a retry of uninstall.
            try:
                uninstall_record(record, receipt, rollback=True)
            except Exception as cleanup_error:
                raise ValueError(f'installation failed: {error}; cleanup failed: {cleanup_error}; retry uninstall.py {identity}') from error
            raise
        return {'id': identity, 'status': 'installed', 'destination': str(dest), 'receipt': str(receipt)}


def uninstall(identity):
    if len(identity) != 32 or any(c not in '0123456789abcdef' for c in identity):
        raise ValueError('use the installation id returned by install')
    with locked():
        path = STATE / (identity + '.json')
        record = json.loads(path.read_text())
        if record['schema_version'] != 1 or record['id'] != identity or record['type'] not in TYPES:
            raise ValueError('invalid installation receipt')
        if record['status'] == 'uninstalled':
            return {'id': identity, 'status': 'already uninstalled'}
        return uninstall_record(record, path)
