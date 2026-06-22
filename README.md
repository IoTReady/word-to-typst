# word-to-typst

Convert `.doc` and `.docx` files to [Typst](https://typst.app) format.

## Requirements

- [podman](https://podman.io) installed and in PATH

## Install

```bash
uv tool install git+https://github.com/IoTReady/word-to-typst
```

## Usage

```bash
# Single file
word-to-typst report.docx

# Explicit output path
word-to-typst report.docx --output out/report.typ

# Batch: multiple files
word-to-typst *.docx --output-dir out/

# Batch: whole directory
word-to-typst --dir ./docs --output-dir ./typst-out

# Use a different pandoc image
word-to-typst report.docx --pandoc-image pandoc/core:latest
```

Images are extracted to `{stem}_images/` next to each `.typ` file.

## License

MIT
