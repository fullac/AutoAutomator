#!/usr/bin/env python3
"""Unbind and remove only an installation owned by AutoAutomator."""
import argparse
import json
import subprocess
import sys
from installation import uninstall


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('id', help='installation id returned by install.py')
    args = parser.parse_args()
    try:
        print(json.dumps(uninstall(args.id), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(getattr(error, 'stderr', None) or str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
