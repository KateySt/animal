#!/usr/bin/env bash
# Run mypy type-check on the edited Python file
f=$(.venv/Scripts/python.exe -c "import sys,json; d=json.load(sys.stdin); ti=d.get('tool_input',{}); tr=d.get('tool_response',{}); print(ti.get('file_path') or tr.get('filePath') or '')")
case "$f" in
  *.py)
    .venv/Scripts/python.exe -m mypy "$f" --ignore-missing-imports --no-error-summary 2>&1 \
      | grep -E '(error|warning):' || true
    ;;
esac
