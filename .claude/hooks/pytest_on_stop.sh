#!/usr/bin/env bash
# Stop hook: if Python code changed this session, run the test suite before finishing.
# Green  -> exit 0 (silent, let the turn end).
# Red    -> exit 2 with reason on stderr, so Claude is told to fix the failing tests.
# Guarded against infinite loops via stop_hook_active.

PY=.venv/Scripts/python.exe

# Read the hook payload once.
payload=$(cat)

# Don't re-trigger if we're already inside a Stop-hook-driven continuation.
active=$("$PY" -c "import sys,json; print(json.load(sys.stdin).get('stop_hook_active', False))" <<<"$payload" 2>/dev/null)
if [ "$active" = "True" ]; then
  exit 0
fi

# Only run if tracked/untracked Python files under app/ or tests/ changed.
changed=$(git status --porcelain -- 'app/*.py' 'tests/*.py' 'app/**/*.py' 'tests/**/*.py' 2>/dev/null)
if [ -z "$changed" ]; then
  exit 0
fi

# Run the suite quietly. Capture output; keep the tail for the reason message.
out=$("$PY" -m pytest -q --tb=short 2>&1)
code=$?

if [ "$code" -eq 0 ]; then
  # All green — nothing to say, end the turn.
  exit 0
fi

if [ "$code" -eq 5 ]; then
  # pytest exit 5 = no tests collected; not a failure worth blocking on.
  exit 0
fi

# Tests failed. Emit the tail so Claude sees exactly what broke and fixes it.
tail=$(printf '%s\n' "$out" | tail -n 40)
{
  echo "Test suite is RED after your code changes. Fix the failing tests (or the code they cover), then re-run:"
  echo "  $PY -m pytest -q --tb=short"
  echo
  echo "----- pytest output (tail) -----"
  echo "$tail"
} >&2
exit 2
