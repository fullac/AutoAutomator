#!/bin/zsh
# List immediate regular files, including hidden files. Never replace an output.
emulate -LR zsh
setopt ERR_EXIT NO_UNSET PIPE_FAIL NO_CLOBBER
if (( $# != 2 )); then
  print -u2 'usage: list_files.sh INPUT_DIRECTORY OUTPUT_FILE'
  exit 64
fi
input=${1:A}
output=${2:A}
[[ -d "$input" ]] || { print -u2 -- "input directory not found: $input"; exit 66; }
[[ -d "${output:h}" ]] || { print -u2 -- "output parent not found: ${output:h}"; exit 73; }
[[ ! -e "$output" && ! -L "$output" ]] || { print -u2 -- "output already exists: $output"; exit 73; }
files=("$input"/*(ND.))
for file in "${files[@]}"; do
  [[ "${file:t}" != *$'\n'* ]] || { print -u2 'newline in filename cannot be represented in a line-based list'; exit 65; }
done
# Array is collected before creating the output, so it never lists itself.
{ for file in "${files[@]}"; do print -r -- "${file:t}"; done; } > "$output"
print -r -- "$output"
