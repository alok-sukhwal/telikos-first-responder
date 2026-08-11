#!/usr/bin/env bash
# PreToolUse gate for `git commit`: runs the coverage-gated suite and blocks on failure.
#
# Exit 0 = allow, silently. Exit 2 = block the commit; stderr is the only thing Claude gets
# to act on, so it stays short and names what to fix. Reads no stdin. Restricting this to
# `git commit` belongs in the hook config (`if: "Bash(git commit*)"`), not here.

set -uo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
log=$(cd "$root" && uv run pytest --cov 2>&1) && exit 0

{
  echo "test-gate: commit blocked — 'uv run pytest --cov' failed."

  failed=$(grep -E '^(FAILED|ERROR) ' <<<"$log" | awk '{print $2}' | sort -u)
  if [[ -n $failed ]]; then
    echo "  failing tests ($(grep -c . <<<"$failed")):"
    head -10 <<<"$failed" | sed 's/^/    /'
  fi

  if grep -q 'Required test coverage.*not reached' <<<"$log"; then
    grep -o 'Required test coverage of.*' <<<"$log" | sed 's/^/  /'
    grep -E '^[^ ]+\.py +[0-9]+ +[1-9]' <<<"$log" \
      | sed -E 's/^([^ ]+) +[0-9]+ +[0-9]+ +([0-9]+%) +(.*)$/    \1 \2, uncovered: \3/' \
      | head -5
  fi

  # Neither pattern matched: don't block with an empty explanation.
  if [[ -z $failed ]] && ! grep -q 'Required test coverage.*not reached' <<<"$log"; then
    tail -3 <<<"$log" | sed 's/^/  /'
  fi

  echo "  rerun: uv run pytest --cov"
} >&2
exit 2
