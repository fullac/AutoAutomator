#!/bin/zsh
# List immediate regular files, including hidden files. Never replace an output.
emulate -LR zsh
setopt ERR_EXIT NO_UNSET PIPE_FAIL NO_CLOBBER
if (( $# != 2 )); then
  print -u2 'usage: list_files.sh INPUT_DIRECTORY OUTPUT_FILE'
  exit 64
fi
input=${1:A}
output=${2:a}
[[ -d "$input" ]] || { print -u2 -- "input directory not found: $input"; exit 66; }
[[ -d "${output:h}" ]] || { print -u2 -- "output parent not found: ${output:h}"; exit 73; }
[[ ! -e "$output" && ! -L "$output" ]] || { print -u2 -- "output already exists: $output"; exit 73; }
# A denied directory must not be mistaken for an empty directory by a null glob.
/bin/ls -A -- "$input" >/dev/null || { print -u2 -- "cannot read input directory: $input"; exit 77; }
files=("$input"/*(ND.))
for file in "${files[@]}"; do
  [[ "${file:t}" != *$'\n'* ]] || { print -u2 'newline in filename cannot be represented in a line-based list'; exit 65; }
done
# Publish a complete file without following a destination symlink or replacing a racing writer.
staging=$(/usr/bin/mktemp "${output:h}/.autoautomator-list.XXXXXXXX")
trap '/bin/rm -f -- "$staging"' EXIT
trap 'exit 130' HUP INT TERM
{ for file in "${files[@]}"; do print -r -- "${file:t}"; done; } >| "$staging"
/bin/link "$staging" "$output"
print -r -- "$output"
