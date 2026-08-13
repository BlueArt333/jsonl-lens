# JSONL Lens

JSONL Lens is a small, dependency-free command-line tool for validating and inspecting
[JSON Lines](https://jsonlines.org/) files. It streams input one line at a time, so it is
useful for logs, model datasets, exports, and other files that should not be loaded fully
into memory.

## Features

- Reports malformed JSON with line and column numbers.
- Counts valid records, blank lines, top-level JSON types, and common object fields.
- Emits human-readable text or JSON for automation.
- Streams `.jsonl.gz` files directly without manual decompression.
- Reads a file or standard input.
- Uses only the Python standard library at runtime.

## Install for development

```bash
git clone https://github.com/BlueArt333/jsonl-lens.git
cd jsonl-lens
python -m pip install -e ".[dev]"
```

## Usage

```bash
jsonl-lens events.jsonl
jsonl-lens archived-events.jsonl.gz
jsonl-lens events.jsonl --format json
jsonl-lens events.jsonl --require-field id --require-field timestamp
Get-Content events.jsonl | jsonl-lens
```

Use repeatable `--require-field` options to check that every object record contains the
fields your pipeline expects. Non-object records are reported when this validation is enabled.

Exit status is `0` when every nonblank line is valid JSON, `1` when malformed lines are
found, and `2` for file or encoding errors.

## Contributing

Issues and focused pull requests are welcome. Run the checks locally with:

```bash
python -m pytest
python -m ruff check .
```

## License

MIT
