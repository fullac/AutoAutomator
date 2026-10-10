#!/usr/bin/env python3
"""Build a source-preserving AppleScript app using macOS osacompile."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import plistlib
import re
import shutil
import subprocess
import sys


def application_id(name, explicit=None):
    slug = re.sub(r'[^a-z0-9-]+', '-', name.lower()).strip('-')[:80] or 'task'
    value = explicit or ('com.autoautomator.' + slug + '-' + hashlib.sha256(name.encode()).hexdigest()[:8])
    if len(value) > 255 or not re.fullmatch(r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', value):
        raise ValueError('--bundle-id must be a reverse-DNS identifier containing letters, digits, dots or hyphens')
    return value


def as_string(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t') + '"'


def shell_wrapper(shell, arguments, bundle_id, accept_drops=False):
    argument_code = "".join(" & \" \" & quoted form of " + as_string(arg) for arg in arguments)
    handlers = '''on run
    runTask({})
end run
'''
    if accept_drops:
        handlers += '''on open theItems
    runTask(theItems)
end open
'''
    return handlers + f'''on runTask(theItems)
    set resourcePath to POSIX path of (path to resource "task.sh")
    set logDirectory to POSIX path of (path to library folder from user domain) & "Logs/AutoAutomator/"
    set logPath to logDirectory & "{bundle_id}.log"
    set taskCommand to {as_string(shell)} & " " & quoted form of resourcePath{argument_code}
    repeat with theItem in theItems
        set taskCommand to taskCommand & " " & quoted form of (POSIX path of theItem)
    end repeat
    try
        do shell script "/bin/mkdir -p " & quoted form of logDirectory
        do shell script taskCommand & " >> " & quoted form of logPath & " 2>&1"
    on error errorMessage number errorNumber
        error (errorMessage & return & "Log: " & logPath) number errorNumber
    end try
end runTask
'''


def build(args):
    if platform.system() != "Darwin":
        raise ValueError("app building requires macOS")
    source = (args.source or args.shell_script).resolve(strict=True)
    if not source.is_file():
        raise ValueError("source must be a file")
    if not args.name or args.name in (".", "..") or any(c in args.name for c in "/:\n\r"):
        raise ValueError("name must be a single filename without slash, colon or newline")
    if args.source and args.arg:
        raise ValueError("--arg is only supported with --shell-script")
    if args.source and args.accept_drops:
        raise ValueError('--accept-drops is only supported with --shell-script; native source should define on open')
    bundle_id = application_id(args.name, args.bundle_id)
    if args.shell not in ("/bin/sh", "/bin/bash", "/bin/zsh"):
        raise ValueError("choose a system shell: /bin/sh, /bin/bash or /bin/zsh")
    if not all(Path(tool).is_file() for tool in ("/usr/bin/osacompile", "/usr/bin/codesign", args.shell)):
        raise ValueError("required macOS compiler, codesign or shell is missing")
    if args.shell_script:
        subprocess.run([args.shell, "-n", str(source)], check=True, capture_output=True, text=True)
    output = args.output.absolute()
    output.mkdir()  # exclusive: never overwrite a previous delivery
    try:
        source_dir = output / "source"
        source_dir.mkdir()
        if args.shell_script:
            saved_source = source_dir / "task.sh"
            shutil.copyfile(source, saved_source)
            apple_source = source_dir / "launcher.applescript"
            apple_source.write_text(shell_wrapper(args.shell, args.arg, bundle_id, args.accept_drops))
        else:
            apple_source = source_dir / "task.applescript"
            shutil.copyfile(source, apple_source)
            saved_source = apple_source
        application = output / (args.name + ".app")
        subprocess.run(["/usr/bin/osacompile", "-o", str(application), str(apple_source)],
                       check=True, capture_output=True, text=True)
        if args.shell_script:
            shutil.copyfile(saved_source, application / "Contents/Resources/task.sh")
        info_path = application / "Contents/Info.plist"
        info = plistlib.loads(info_path.read_bytes())
        info["CFBundleIdentifier"] = bundle_id
        if args.accept_drops:
            info['CFBundleDocumentTypes'] = [{'CFBundleTypeName': 'Files and folders',
                                            'LSItemContentTypes': ['public.item'],
                                            'CFBundleTypeRole': 'Viewer', 'LSHandlerRank': 'Alternate'}]
        info_path.write_bytes(plistlib.dumps(info))
        # Resource copying must finish before ad-hoc signing the complete local application.
        subprocess.run(["/usr/bin/codesign", "--force", "--sign", "-", str(application)],
                       check=True, capture_output=True, text=True)
        subprocess.run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(application)],
                       check=True, capture_output=True, text=True)
        record = {
            "schema_version": 2,
            "artifact": application.name,
            "signing": "ad-hoc; local integrity only, no Developer ID or notarization",
            "type": "applescript-application", "name": args.name,
            "bundle_id": bundle_id,
            "accept_drops": args.accept_drops,
            "macos": platform.mac_ver()[0],
            "shell": args.shell if args.shell_script else None,
            "arguments": args.arg,
            "log": "~/Library/Logs/AutoAutomator/" + bundle_id + ".log" if args.shell_script else None,
            "rebuild": ["python3", "<skill>/scripts/build_app.py",
                        "--shell-script" if args.shell_script else "--source",
                        str(saved_source.relative_to(output)), "--output", "<new-delivery-directory>",
                        "--name", args.name, "--bundle-id", bundle_id] + (["--shell", args.shell] if args.shell_script else [])
                       + ["--arg=" + arg for arg in args.arg]
                       + (["--accept-drops"] if args.accept_drops else []),
            "validation": "built; actual launch and task result must be tested separately",
        }
        (output / "build.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        return application
    except BaseException:
        shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", type=Path, help="AppleScript source")
    group.add_argument("--shell-script", type=Path, help="shell task bundled inside the app")
    parser.add_argument("--shell", default="/bin/zsh")
    parser.add_argument("--arg", action="append", default=[], help="fixed task argument; repeat as needed")
    parser.add_argument("--name", default="AutoAutomator Task")
    parser.add_argument("--bundle-id", help="stable reverse-DNS identity; defaults to a name-derived ID")
    parser.add_argument('--accept-drops', action='store_true', help='Shell app accepts files/folders dropped in Finder')
    parser.add_argument("--output", type=Path, required=True, help="new delivery directory, parent must exist")
    args = parser.parse_args()
    try:
        print(build(args))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(getattr(error, "stderr", None) or str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
