#!/usr/bin/env python3
"""Build a single-action Automator workflow with embedded Shell task source."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import plistlib
import shlex
import shutil
import subprocess
import sys
import uuid

ACTION = Path('/System/Library/Automator/Run Shell Script.action')
TYPES = {'workflow': 'com.apple.Automator.workflow',
         'quick-action': 'com.apple.Automator.servicesMenu',
         'folder-action': 'com.apple.Automator.folderAction'}


def metadata(kind):
    result = {'workflowTypeIdentifier': TYPES[kind]}
    if kind == 'quick-action':
        result.update(applicationBundleID='com.apple.finder',
                      applicationPath='/System/Library/CoreServices/Finder.app',
                      applicationPaths=['/System/Library/CoreServices/Finder.app'],
                      applicationBundleIDsByPath={'/System/Library/CoreServices/Finder.app': 'com.apple.finder'},
                      inputTypeIdentifier='com.apple.Automator.fileSystemObject',
                      outputTypeIdentifier='com.apple.Automator.nothing',
                      serviceApplicationBundleID='com.apple.finder',
                      serviceApplicationPath='/System/Library/CoreServices/Finder.app',
                      serviceInputTypeIdentifier='com.apple.Automator.fileSystemObject',
                      serviceOutputTypeIdentifier='com.apple.Automator.nothing',
                      processesInput=False, serviceProcessesInput=False,
                      presentationMode=15, systemImageName='NSActionTemplate',
                      useAutomaticInputType=False)
    return result


def build(args):
    if platform.system() != 'Darwin':
        raise ValueError('workflow building requires macOS')
    source = args.script.resolve(strict=True)
    if not source.is_file():
        raise ValueError('source must be a file')
    if not args.name or args.name in ('.', '..') or any(c in args.name for c in '/:\n\r'):
        raise ValueError('name must be a single filename without slash, colon or newline')
    if args.shell not in ('/bin/zsh', '/bin/bash', '/bin/sh'):
        raise ValueError('choose a system shell: /bin/sh, /bin/bash or /bin/zsh')
    action_info = plistlib.loads((ACTION / 'Contents/Info.plist').read_bytes())
    automator_info = plistlib.loads(Path('/System/Applications/Automator.app/Contents/Info.plist').read_bytes())
    subprocess.run([args.shell, '-n', str(source)], check=True, capture_output=True, text=True)
    # Fixed arguments precede selected/added paths. Embedded source survives moving/installing the bundle.
    command = 'exec ' + shlex.join([args.shell, '-c', source.read_text(), 'autoautomator-task'] + args.arg) + ' "$@"\n'
    action = {
        'AMAccepts': action_info['AMAccepts'], 'AMProvides': action_info['AMProvides'],
        'AMActionVersion': action_info['CFBundleVersion'], 'CFBundleVersion': action_info['CFBundleVersion'],
        'AMApplication': ['Automator'], 'ActionBundlePath': str(ACTION),
        'ActionName': 'Run Shell Script', 'BundleIdentifier': action_info['CFBundleIdentifier'],
        'Class Name': action_info['NSPrincipalClass'],
        'AMParameterProperties': {key: {} for key in action_info['AMDefaultParameters']},
        'ActionParameters': {'COMMAND_STRING': command, 'CheckedForUserDefaultShell': True,
                             'inputMethod': 1, 'shell': args.shell, 'source': ''},
        'CanShowSelectedItemsWhenRun': False, 'CanShowWhenRun': True,
        'InputUUID': str(uuid.uuid4()).upper(), 'OutputUUID': str(uuid.uuid4()).upper(),
        'UUID': str(uuid.uuid4()).upper(), 'isViewVisible': 1,
        'nibPath': str(ACTION / 'Contents/Resources/Base.lproj/main.nib'),
    }
    document = {'AMApplicationBuild': automator_info['CFBundleVersion'],
                'AMApplicationVersion': automator_info['CFBundleShortVersionString'],
                'AMDocumentVersion': '2', 'actions': [{'action': action, 'isViewVisible': 1}],
                'connectors': {}, 'workflowMetaData': metadata(args.type)}
    output = args.output.absolute()
    output.mkdir()
    try:
        bundle = output / (args.name + '.workflow')
        contents = bundle / 'Contents'
        contents.mkdir(parents=True)
        (contents / 'document.wflow').write_bytes(plistlib.dumps(document))
        if args.type == 'quick-action':
            info = {'NSServices': [{'NSMenuItem': {'default': args.name},
                                   'NSMessage': 'runWorkflowAsService',
                                   'NSRequiredContext': {'NSApplicationIdentifier': 'com.apple.finder'},
                                   'NSSendFileTypes': ['public.item'],
                                   'NSIconName': 'NSActionTemplate', 'NSBackgroundColorName': 'background'}]}
            (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
        source_dir = output / 'source'
        source_dir.mkdir()
        shutil.copyfile(source, source_dir / 'task.sh')
        record = {'schema_version': 1, 'artifact': bundle.name,
                  'files': {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in sorted(output.rglob('*')) if path.is_file()},
                  'type': args.type, 'name': args.name, 'macos': platform.mac_ver()[0],
                  'shell': args.shell, 'arguments': args.arg,
                  'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                  'input': 'fixed arguments then each selected/added path as a separate argument',
                  'rebuild': ['python3', '<skill>/scripts/build_workflow.py', '--script', 'source/task.sh',
                              '--type', args.type, '--shell', args.shell, '--name', args.name,
                              '--output', '<new-delivery-directory>'] + ['--arg=' + arg for arg in args.arg],
                  'validation': 'built; actual Automator/system entry must be tested separately',
                  'installation': 'not installed or bound'}
        (output / 'build.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        return bundle
    except BaseException:
        shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--type', choices=TYPES, default='workflow')
    parser.add_argument('--shell', default='/bin/zsh')
    parser.add_argument('--arg', action='append', default=[])
    parser.add_argument('--name', default='AutoAutomator Task')
    parser.add_argument('--output', type=Path, required=True, help='new delivery directory')
    args = parser.parse_args()
    try:
        print(build(args))
    except (OSError, ValueError, subprocess.CalledProcessError, KeyError, plistlib.InvalidFileException) as error:
        print(getattr(error, 'stderr', None) or str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
