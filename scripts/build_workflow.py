#!/usr/bin/env python3
"""Build a single-action Automator workflow with embedded Shell, AppleScript or JXA."""
import argparse
import json
from pathlib import Path
import platform
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid

ACTIONS = {'shell': 'Run Shell Script', 'applescript': 'Run AppleScript', 'jxa': 'Run JavaScript'}
SOURCES = {'shell': 'task.sh', 'applescript': 'task.applescript', 'jxa': 'task.js'}
TYPES = {'workflow': 'com.apple.Automator.workflow',
         'quick-action': 'com.apple.Automator.servicesMenu',
         'folder-action': 'com.apple.Automator.folderAction'}


def metadata(kind, input_kind='files', app='finder', replaces=False):
    result = {'workflowTypeIdentifier': TYPES[kind]}
    if kind == 'quick-action':
        input_type = 'com.apple.Automator.' + {'files': 'fileSystemObject', 'text': 'text', 'none': 'nothing'}[input_kind]
        output_type = 'com.apple.Automator.text' if replaces else 'com.apple.Automator.nothing'
        result.update(applicationPaths=[], applicationBundleIDsByPath={},
                      inputTypeIdentifier=input_type,
                      outputTypeIdentifier=output_type,
                      serviceInputTypeIdentifier=input_type,
                      serviceOutputTypeIdentifier=output_type,
                      processesInput=False, serviceProcessesInput=False,
                      presentationMode=11 if input_kind == 'text' else 15, systemImageName='NSActionTemplate',
                      useAutomaticInputType=False)
        if app != 'any':
            bundle_id = 'com.apple.finder' if app == 'finder' else app
            result.update(applicationBundleID=bundle_id, serviceApplicationBundleID=bundle_id)
            if app == 'finder':
                path = '/System/Library/CoreServices/Finder.app'
                result.update(applicationPath=path, serviceApplicationPath=path,
                              applicationPaths=[path], applicationBundleIDsByPath={path: bundle_id})
    return result


def service_info(name, input_kind, app, replaces):
    service = {'NSMenuItem': {'default': name}, 'NSMessage': 'runWorkflowAsService',
               'NSIconName': 'NSActionTemplate', 'NSBackgroundColorName': 'background'}
    if app != 'any':
        service['NSRequiredContext'] = {'NSApplicationIdentifier': 'com.apple.finder' if app == 'finder' else app}
    if input_kind == 'files':
        service['NSSendFileTypes'] = ['public.item']
    elif input_kind == 'text':
        service['NSSendTypes'] = ['public.utf8-plain-text']
    if replaces:
        service['NSReturnTypes'] = ['public.utf8-plain-text']
    return {'NSServices': [service]}


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
    app = args.app or ('finder' if args.input == 'files' else 'any')
    if app not in ('finder', 'any') and not re.fullmatch(r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', app):
        raise ValueError('--app must be finder, any or an application bundle ID')
    if args.output_replaces_selection and (args.type != 'quick-action' or args.input != 'text'):
        raise ValueError('--output-replaces-selection requires a text quick action')
    if args.app and args.type != 'quick-action':
        raise ValueError('--app is only supported for quick actions')
    if args.type == 'folder-action' and args.input != 'files':
        raise ValueError('folder actions require file input')
    if args.language != 'shell' and args.arg:
        raise ValueError('--arg is only supported for Shell; native actions receive input and parameters')
    action_path = Path('/System/Library/Automator') / (ACTIONS[args.language] + '.action')
    action_info = plistlib.loads((action_path / 'Contents/Info.plist').read_bytes())
    automator_info = plistlib.loads(Path('/System/Applications/Automator.app/Contents/Info.plist').read_bytes())
    # Validate and embed the same immutable source snapshot.
    source_bytes = source.read_bytes()
    source_text = source_bytes.decode('utf-8')
    parameters = dict(action_info['AMDefaultParameters'])
    if args.language == 'shell':
        subprocess.run([args.shell, '-n'], input=source_text, check=True, capture_output=True, text=True)
        command = 'exec ' + shlex.join([args.shell, '-c', source_text, 'autoautomator-task'] + args.arg) + (' "$@"' if args.input == 'files' else '') + '\n'
        parameters.update(COMMAND_STRING=command, CheckedForUserDefaultShell=True,
                          inputMethod=1 if args.input == 'files' else 0, shell=args.shell)
    else:
        with tempfile.TemporaryDirectory(prefix='autoautomator-syntax-') as temporary:
            saved = Path(temporary) / SOURCES[args.language]
            saved.write_bytes(source_bytes)
            subprocess.run(['/usr/bin/osacompile', '-l', 'AppleScript' if args.language == 'applescript' else 'JavaScript',
                            '-o', str(Path(temporary) / 'check.scpt'), str(saved)],
                           check=True, capture_output=True, text=True)
        parameters['source'] = source_text
    action = {
        'AMAccepts': action_info['AMAccepts'], 'AMProvides': action_info['AMProvides'],
        'AMActionVersion': action_info['CFBundleVersion'], 'CFBundleVersion': action_info['CFBundleVersion'],
        'AMApplication': ['Automator'], 'ActionBundlePath': str(action_path),
        'ActionName': ACTIONS[args.language], 'BundleIdentifier': action_info['CFBundleIdentifier'],
        'Class Name': action_info['NSPrincipalClass'],
        'AMParameterProperties': {key: {} for key in action_info['AMDefaultParameters']},
        'ActionParameters': parameters,
        'CanShowSelectedItemsWhenRun': False, 'CanShowWhenRun': True,
        'InputUUID': str(uuid.uuid4()).upper(), 'OutputUUID': str(uuid.uuid4()).upper(),
        'UUID': str(uuid.uuid4()).upper(), 'isViewVisible': 1,
        'nibPath': str(action_path / 'Contents/Resources/Base.lproj/main.nib'),
    }
    document = {'AMApplicationBuild': automator_info['CFBundleVersion'],
                'AMApplicationVersion': automator_info['CFBundleShortVersionString'],
                'AMDocumentVersion': '2', 'actions': [{'action': action, 'isViewVisible': 1}],
                'connectors': {}, 'workflowMetaData': metadata(args.type, args.input, app, args.output_replaces_selection)}
    output = args.output.absolute()
    output.mkdir()
    try:
        bundle = output / (args.name + '.workflow')
        contents = bundle / 'Contents'
        contents.mkdir(parents=True)
        (contents / 'document.wflow').write_bytes(plistlib.dumps(document))
        if args.type == 'quick-action':
            info = service_info(args.name, args.input, app, args.output_replaces_selection)
            (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
        source_dir = output / 'source'
        source_dir.mkdir()
        (source_dir / SOURCES[args.language]).write_bytes(source_bytes)
        record = {'schema_version': 2, 'artifact': bundle.name,
                  'type': args.type, 'name': args.name, 'macos': platform.mac_ver()[0],
                  'language': args.language, 'shell': args.shell if args.language == 'shell' else None, 'arguments': args.arg,
                  'input': args.input, 'app': app if args.type == 'quick-action' else None,
                  'output_replaces_selection': args.output_replaces_selection,
                  'rebuild': ['python3', '<skill>/scripts/build_workflow.py', '--script', 'source/' + SOURCES[args.language],
                              '--type', args.type, '--language', args.language, '--name', args.name,
                              '--output', '<new-delivery-directory>', '--input', args.input]
                             + (['--shell', args.shell] if args.language == 'shell' else [])
                             + (['--app', app] if args.type == 'quick-action' else [])
                             + (['--output-replaces-selection'] if args.output_replaces_selection else [])
                             + ['--arg=' + arg for arg in args.arg],
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
    parser.add_argument('--language', choices=ACTIONS, default='shell')
    parser.add_argument('--shell', default='/bin/zsh')
    parser.add_argument('--arg', action='append', default=[])
    parser.add_argument('--input', choices=('files', 'text', 'none'), default='files')
    parser.add_argument('--app', help='finder, any or bundle ID; defaults to finder for files, any for text/none')
    parser.add_argument('--output-replaces-selection', action='store_true')
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
