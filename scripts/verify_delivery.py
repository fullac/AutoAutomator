#!/usr/bin/env python3
"""Check saved-source and artifact integrity. Does not execute the task."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import sys

TYPES = {'workflow': 'com.apple.Automator.workflow',
         'quick-action': 'com.apple.Automator.servicesMenu',
         'folder-action': 'com.apple.Automator.folderAction'}


def verify(directory):
    root = directory.resolve(strict=True)
    record = json.loads((root / 'build.json').read_text())
    if not isinstance(record, dict) or record.get('schema_version') != 1 or not isinstance(record.get('files'), dict) or not record['files']:
        raise ValueError('unsupported or incomplete build record; rebuild with current tools')
    for name, expected in record['files'].items():
        path = root / name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('unsafe manifest path: ' + name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('file modified: ' + name)
    artifact_name = record['artifact']
    if Path(artifact_name).name != artifact_name or artifact_name in ('.', '..'):
        raise ValueError('invalid artifact filename')
    artifact = root / artifact_name
    if artifact.is_symlink() or not artifact.is_dir():
        raise ValueError('artifact must be a bundle directory')
    if record['type'] == 'applescript-application':
        subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(artifact)],
                       check=True, capture_output=True, text=True)
    elif record['type'] in TYPES:
        doc = plistlib.loads((artifact / 'Contents/document.wflow').read_bytes())
        if doc['workflowMetaData']['workflowTypeIdentifier'] != TYPES[record['type']]:
            raise ValueError('workflow type does not match build record')
        if record['type'] == 'quick-action':
            info = plistlib.loads((artifact / 'Contents/Info.plist').read_bytes())
            if info['NSServices'][0]['NSMenuItem']['default'] != record['name']:
                raise ValueError('service menu name does not match build record')
    else:
        raise ValueError('unknown artifact type')
    return {'artifact': str(artifact), 'integrity': 'passed',
            'execution': 'not performed; test actual entry and result separately'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.directory), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(getattr(error, 'stderr', None) or str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
