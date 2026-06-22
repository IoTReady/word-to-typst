import sys
from pathlib import Path

import click

from word_to_typst.converter import check_podman, convert

SUPPORTED = {".doc", ".docx"}
DEFAULT_IMAGE = "docker.io/pandoc/extra:latest"


@click.command()
@click.argument("inputs", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--output", "output", type=click.Path(path_type=Path), default=None,
              help="Output .typ path (single file only).")
@click.option("--output-dir", "output_dir", type=click.Path(path_type=Path), default=None,
              help="Directory for output files.")
@click.option("--dir", "input_dir", type=click.Path(exists=True, file_okay=False, path_type=Path),
              default=None, help="Convert all .doc/.docx files in this directory.")
@click.option("--pandoc-image", "pandoc_image", default=DEFAULT_IMAGE, show_default=True,
              help="Pandoc Docker image to use.")
def main(inputs, output, output_dir, input_dir, pandoc_image):
    """Convert .doc and .docx files to Typst format."""
    if not check_podman():
        click.echo(
            "Error: podman not found in PATH.\n"
            "Install podman: https://podman.io/docs/installation",
            err=True,
        )
        sys.exit(1)

    files = list(inputs)
    if input_dir:
        files += [p for p in input_dir.iterdir() if p.suffix in SUPPORTED]

    if not files:
        click.echo("Error: no input files provided. Pass files or use --dir.", err=True)
        sys.exit(1)

    valid_files = []
    for f in files:
        if Path(f).suffix in SUPPORTED:
            valid_files.append(f)
        else:
            click.echo(f"Warning: skipping {f} (not .doc or .docx)")
    files = valid_files

    failures = 0
    total = len(files)

    if output and total > 1:
        click.echo("Warning: --output is ignored when multiple files are given; use --output-dir instead.")

    for input_path in files:
        input_path = Path(input_path)
        if output_dir:
            output_path = Path(output_dir) / input_path.with_suffix(".typ").name
        elif output and total == 1:
            output_path = Path(output)
        else:
            output_path = input_path.with_suffix(".typ")

        click.echo(f"Converting {input_path.name} ...", nl=False)
        success, error = convert(input_path, output_path, pandoc_image)
        if success:
            click.echo(f" done -> {output_path}")
        else:
            click.echo(f" FAILED\n  {error}")
            failures += 1

    if total > 1:
        click.echo(f"\n{total - failures} of {total} files converted successfully.")

    if failures:
        sys.exit(1)
