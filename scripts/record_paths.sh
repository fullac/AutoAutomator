#!/bin/zsh
# Example for Finder selection / added-folder-items. First argument is output directory.
emulate -LR zsh
setopt ERR_EXIT NO_UNSET PIPE_FAIL NO_CLOBBER
(( $# >= 2 )) || { print -u2 'usage: record_paths.sh OUTPUT_DIRECTORY INPUT_PATH ...'; exit 64; }
output_dir=${1:A}
shift
[[ -d "$output_dir" ]] || { print -u2 -- "output directory not found: $output_dir"; exit 73; }
for item in "$@"; do
  [[ -e "$item" ]] || { print -u2 -- "input not found: $item"; exit 66; }
done
# NUL-separated paths support every valid filename. One receipt per invocation.
receipt=$(/usr/bin/mktemp "$output_dir/paths.XXXXXXXX")
# mktemp already created this private file; >| only opens that new file.
printf '%s\0' "$@" >| "$receipt"
print -r -- "$receipt"
