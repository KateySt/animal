#!/usr/bin/env bash
# Run ruff check+format on the edited Python file
f=$(.venv/Scripts/python.exe -c "import sys,json; d=json.load(sys.stdin); ti=d.get('tool_input',{}); tr=d.get('tool_response',{}); print(ti.get('file_path') or tr.get('filePath') or '')")
case "$f" in
  *.py)
    .venv/Scripts/python.exe -m ruff check --fix "$f"
    .venv/Scripts/python.exe -m ruff format "$f"
    ;;
esac 2>/dev/null || true
