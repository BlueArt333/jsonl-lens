from __future__ import annotations

import io
import json

from jsonl_lens.cli import inspect_stream, run


def test_inspect_stream_counts_records_fields_and_errors() -> None:
    data = io.StringIO('{"id": 1, "name": "Ada"}\n\nnot-json\n[1, 2]\n')

    result = inspect_stream(data)

    assert result.records == 2
    assert result.blank_lines == 1
    assert result.fields == {"id": 1, "name": 1}
    assert result.types == {"object": 1, "array": 1}
    assert result.errors == ["line 3: column 1: Expecting value"]


def test_run_emits_machine_readable_summary(tmp_path, capsys) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text('{"kind": "start"}\n{"kind": "stop"}\n', encoding="utf-8")

    exit_code = run([str(path), "--format", "json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid_records"] == 2
    assert payload["fields"] == {"kind": 2}


def test_run_returns_one_for_invalid_json(tmp_path, capsys) -> None:
    path = tmp_path / "broken.jsonl"
    path.write_text('{"ok": true}\n{broken}\n', encoding="utf-8")

    assert run([str(path)]) == 1
    assert "line 2" in capsys.readouterr().out

