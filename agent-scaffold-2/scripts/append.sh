#!/bin/sh
# Atomic single-line append for shared, append-only files (sources, questions, LOG).
# Usage: agents/scripts/append.sh <file> "<one line>"
# Many agents call this at the same time; one short O_APPEND write does not interleave.
# Never use an editor tool (Write/Edit) on these files: it replaces the whole file and
# loses other agents' lines.
set -eu
if [ "$#" -lt 2 ]; then
  echo "usage: $0 <file> \"<one line>\"" >&2
  exit 2
fi
file="$1"; shift
line="$*"
case "$line" in
  *"
"*) echo "error: entry must be a single line" >&2; exit 3;;
esac
mkdir -p "$(dirname "$file")"
printf '%s\n' "$line" >> "$file"
