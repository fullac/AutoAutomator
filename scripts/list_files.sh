#!/bin/zsh
# Minimal example: list immediate regular files without replacing output.
emulate -LR zsh
setopt ERR_EXIT NO_UNSET PIPE_FAIL NO_CLOBBER
(( $# == 2 )) || { print -u2 'usage: list_files.sh INPUT_DIRECTORY OUTPUT_FILE'; exit 64; }
input=${1:A}
output=${2:a}
[[ -d "$input" ]] || { print -u2 -- "input directory not found: $input"; exit 66; }
[[ -d "${output:h}" ]] || { print -u2 -- "output parent not found: ${output:h}"; exit 73; }
[[ ! -e "$output" && ! -L "$output" ]] || { print -u2 -- "output already exists: $output"; exit 73; }
/bin/ls -A -- "$input" >/dev/null || { print -u2 -- "cannot read input directory: $input"; exit 77; }
for file in "$input"/*(ND.); do print -r -- "${file:t}"; done > "$output"
print -r -- "$output"
