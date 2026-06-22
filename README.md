# word-to-typst

Convert `.doc` and `.docx` files to [Typst](https://typst.app) format, with images extracted automatically.

## Requirements

- [podman](https://podman.io) installed and in PATH
- The `pandoc/extra` image is pulled automatically on first use

## Install

```bash
# From GitHub (latest)
uv tool install git+https://github.com/IoTReady/word-to-typst

# From PyPI (once published)
pip install word-to-typst
```

## Usage

```bash
# Single file — output alongside input
word-to-typst report.docx

# Single file — explicit output path
word-to-typst report.docx --output out/report.typ

# Multiple files to a directory
word-to-typst *.docx --output-dir out/

# Whole directory
word-to-typst --dir ./docs --output-dir ./typst-out

# Use a different pandoc image
word-to-typst report.docx --pandoc-image pandoc/core:latest
```

Images embedded in the source document are extracted to `{stem}_images/` next to each `.typ` file.

## How it works

Each file is converted by mounting it into a `pandoc/extra` container (via podman) and running:

```
pandoc input.docx --to=typst --extract-media=images -o output.typ
```

`pandoc/extra` includes LibreOffice, which gives full fidelity for legacy `.doc` files.

## Running tests

```bash
uv sync --dev
# Unit tests (no podman needed)
uv run pytest tests/test_converter.py tests/test_cli.py -v

# Integration tests (requires podman + network)
uv run pytest tests/test_integration.py -v -m integration
```

## License

MIT — see [LICENSE](LICENSE).
