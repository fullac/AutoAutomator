#!/usr/bin/env python3
"""Report the macOS build dependencies without changing system settings."""
import argparse
import json
from pathlib import Path
import platform
import sys

REQUIRED = {
    'script': ['/bin/zsh', '/usr/bin/mktemp', '/bin/ls'],
    'app': ['/usr/bin/osacompile', '/usr/bin/codesign', '/bin/zsh'],
    'workflow': ['/usr/bin/automator', '/bin/zsh',
                 '/System/Library/Automator/Run Shell Script.action/Contents/Info.plist'],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--requires', choices=REQUIRED, default='script')
    parser.add_argument('--language', choices=('shell', 'applescript', 'jxa'), default='shell')
    args = parser.parse_args()
    required = list(REQUIRED[args.requires])
    if args.requires == 'workflow' and args.language != 'shell':
        action = 'Run AppleScript' if args.language == 'applescript' else 'Run JavaScript'
        required[-1] = '/System/Library/Automator/' + action + '.action/Contents/Info.plist'
        required.append('/usr/bin/osacompile')
    missing = [path for path in required if not Path(path).is_file()]
    result = {'platform': platform.system(), 'macos': platform.mac_ver()[0],
              'python': platform.python_version(), 'requires': args.requires, 'language': args.language,
              'missing': missing, 'ready': platform.system() == 'Darwin' and not missing,
              'scope': 'build dependencies only; task dependencies, permissions and actual entry need separate verification'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ready'] else 1


if __name__ == '__main__':
    sys.exit(main())
