#!/usr/bin/env python3
"""Install a quick action, or install and bind a folder action."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from installation import install


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--folder', type=Path, help='existing target directory for a folder action')
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.bundle, args.folder), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(getattr(error, 'stderr', None) or str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
