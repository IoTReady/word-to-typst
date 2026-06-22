from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from word_to_typst.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def docx_file(tmp_path):
    f = tmp_path / "report.docx"
    f.write_bytes(b"fake")
    return f


def test_no_inputs_shows_help(runner):
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    assert "Usage" in result.output or "Error" in result.output


def test_single_file_default_output(runner, docx_file):
    with patch("word_to_typst.cli.check_podman", return_value=True), \
         patch("word_to_typst.cli.convert", return_value=(True, "")) as mock_convert:
        result = runner.invoke(main, [str(docx_file)])

    assert result.exit_code == 0
    expected_output = docx_file.with_suffix(".typ")
    mock_convert.assert_called_once_with(
        docx_file, expected_output, "docker.io/pandoc/extra:latest"
    )


def test_single_file_explicit_output(runner, docx_file, tmp_path):
    out = tmp_path / "out" / "custom.typ"
    with patch("word_to_typst.cli.check_podman", return_value=True), \
         patch("word_to_typst.cli.convert", return_value=(True, "")) as mock_convert:
        result = runner.invoke(main, [str(docx_file), "--output", str(out)])

    assert result.exit_code == 0
    mock_convert.assert_called_once_with(docx_file, out, "docker.io/pandoc/extra:latest")


def test_batch_output_dir(runner, tmp_path):
    f1 = tmp_path / "a.docx"
    f2 = tmp_path / "b.docx"
    f1.write_bytes(b"x")
    f2.write_bytes(b"x")
    out_dir = tmp_path / "out"

    with patch("word_to_typst.cli.check_podman", return_value=True), \
         patch("word_to_typst.cli.convert", return_value=(True, "")) as mock_convert:
        result = runner.invoke(main, [str(f1), str(f2), "--output-dir", str(out_dir)])

    assert result.exit_code == 0
    assert mock_convert.call_count == 2
    calls = {c.args[1] for c in mock_convert.call_args_list}
    assert out_dir / "a.typ" in calls
    assert out_dir / "b.typ" in calls


def test_dir_flag(runner, tmp_path):
    (tmp_path / "x.docx").write_bytes(b"x")
    (tmp_path / "y.doc").write_bytes(b"x")
    (tmp_path / "z.txt").write_bytes(b"x")  # should be skipped

    with patch("word_to_typst.cli.check_podman", return_value=True), \
         patch("word_to_typst.cli.convert", return_value=(True, "")) as mock_convert:
        result = runner.invoke(main, ["--dir", str(tmp_path)])

    assert result.exit_code == 0
    assert mock_convert.call_count == 2


def test_podman_not_found_exits_early(runner, docx_file):
    with patch("word_to_typst.cli.check_podman", return_value=False):
        result = runner.invoke(main, [str(docx_file)])

    assert result.exit_code != 0
    assert "podman" in result.stderr.lower()


def test_conversion_failure_exits_nonzero(runner, docx_file):
    with patch("word_to_typst.cli.check_podman", return_value=True), \
         patch("word_to_typst.cli.convert", return_value=(False, "pandoc error")):
        result = runner.invoke(main, [str(docx_file)])

    assert result.exit_code != 0
    assert "pandoc error" in result.output


def test_batch_partial_failure_reports_summary(runner, tmp_path):
    f1 = tmp_path / "a.docx"
    f2 = tmp_path / "b.docx"
    f1.write_bytes(b"x")
    f2.write_bytes(b"x")

    results = [(True, ""), (False, "bad file")]
    with patch("word_to_typst.cli.check_podman", return_value=True), \
         patch("word_to_typst.cli.convert", side_effect=results):
        result = runner.invoke(main, [str(f1), str(f2)])

    assert result.exit_code != 0
    assert "1 of 2" in result.output


def test_output_with_multiple_files_warns(runner, tmp_path):
    f1 = tmp_path / "a.docx"
    f2 = tmp_path / "b.docx"
    f1.write_bytes(b"x")
    f2.write_bytes(b"x")

    with patch("word_to_typst.cli.check_podman", return_value=True), \
         patch("word_to_typst.cli.convert", return_value=(True, "")):
        result = runner.invoke(main, [str(f1), str(f2), "--output", "out.typ"])

    assert "warning" in result.output.lower()


def test_custom_pandoc_image(runner, docx_file):
    with patch("word_to_typst.cli.check_podman", return_value=True), \
         patch("word_to_typst.cli.convert", return_value=(True, "")) as mock_convert:
        result = runner.invoke(main, [str(docx_file), "--pandoc-image", "pandoc/core:3.1"])

    assert result.exit_code == 0
    assert mock_convert.call_args.args[2] == "pandoc/core:3.1"
