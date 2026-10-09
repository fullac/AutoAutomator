#!/usr/bin/env python3
"""Report the macOS build dependencies without changing system settings."""
import argparse
import json
from pathlib import Path
import platform
import sys

REQUIRED = {
    'script': ['/bin/zsh', '/usr/bin/mktemp', '/bin/link', '/bin/ls'],
    'app': ['/usr/bin/osacompile', '/usr/bin/codesign', '/bin/zsh'],
    'workflow': ['/usr/bin/automator', '/bin/zsh',
                 '/System/Library/Automator/Run Shell Script.action/Contents/Info.plist'],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--requires', choices=REQUIRED, default='script')
    args = parser.parse_args()
    missing = [path for path in REQUIRED[args.requires] if not Path(path).is_file()]
    result = {'platform': platform.system(), 'macos': platform.mac_ver()[0],
              'python': platform.python_version(), 'requires': args.requires,
              'missing': missing, 'ready': platform.system() == 'Darwin' and not missing,
              'scope': 'build dependencies only; task dependencies, permissions and actual entry need separate verification'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ready'] else 1


if __name__ == '__main__':
    sys.exit(main())
