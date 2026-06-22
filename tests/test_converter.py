import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from word_to_typst.converter import build_podman_command, check_podman, convert


def test_check_podman_found():
    with patch("word_to_typst.converter.shutil.which", return_value="/usr/bin/podman"):
        assert check_podman() is True


def test_check_podman_not_found():
    with patch("word_to_typst.converter.shutil.which", return_value=None):
        assert check_podman() is False


def test_build_podman_command_default_image():
    cmd = build_podman_command("report.docx", "pandoc/extra:latest", "/tmp/work")
    assert cmd[0] == "podman"
    assert "pandoc/extra:latest" in cmd
    assert "--to=typst" in cmd
    assert "--extract-media=images" in cmd
    assert "-o" in cmd
    assert "output.typ" in cmd
    assert "report.docx" in cmd
    assert "/tmp/work:/data" in cmd


def test_build_podman_command_custom_image():
    cmd = build_podman_command("report.docx", "pandoc/core:3.1", "/tmp/work")
    assert "pandoc/core:3.1" in cmd


def test_convert_success(tmp_path):
    input_file = tmp_path / "input" / "test.docx"
    input_file.parent.mkdir()
    input_file.write_bytes(b"fake")
    output_file = tmp_path / "output" / "test.typ"
    output_file.parent.mkdir()

    def fake_run(cmd, **kwargs):
        # Simulate pandoc writing output into the working dir mounted as /data
        # We need to find the tmpdir from the -v argument
        v_idx = cmd.index("-v")
        host_dir = Path(cmd[v_idx + 1].split(":")[0])
        (host_dir / "output.typ").write_text("#heading[Hello]")
        images_dir = host_dir / "images"
        images_dir.mkdir()
        (images_dir / "fig1.png").write_bytes(b"PNG")
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        return result

    with patch("word_to_typst.converter.subprocess.run", side_effect=fake_run):
        success, error = convert(input_file, output_file)

    assert success is True
    assert error == ""
    assert output_file.exists()
    images_dir = output_file.parent / "test_images"
    assert images_dir.exists()
    assert (images_dir / "fig1.png").exists()


def test_convert_no_images(tmp_path):
    input_file = tmp_path / "test.docx"
    input_file.write_bytes(b"fake")
    output_file = tmp_path / "out" / "test.typ"
    output_file.parent.mkdir()

    def fake_run(cmd, **kwargs):
        v_idx = cmd.index("-v")
        host_dir = Path(cmd[v_idx + 1].split(":")[0])
        (host_dir / "output.typ").write_text("#heading[Hello]")
        # No images dir created
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        return result

    with patch("word_to_typst.converter.subprocess.run", side_effect=fake_run):
        success, error = convert(input_file, output_file)

    assert success is True
    images_dir = output_file.parent / "test_images"
    assert not images_dir.exists()


def test_convert_podman_failure(tmp_path):
    input_file = tmp_path / "test.docx"
    input_file.write_bytes(b"fake")
    output_file = tmp_path / "test.typ"

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "pandoc: unknown format"

    with patch("word_to_typst.converter.subprocess.run", return_value=mock_result):
        success, error = convert(input_file, output_file)

    assert success is False
    assert "pandoc: unknown format" in error
