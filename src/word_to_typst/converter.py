import shutil
import subprocess
import tempfile
from pathlib import Path


def check_podman() -> bool:
    return shutil.which("podman") is not None


def build_doc_to_docx_command(filename: str, libreoffice_image: str, tmpdir: str) -> list[str]:
    return [
        "podman", "run", "--rm",
        "-v", f"{tmpdir}:/data",
        "-w", "/data",
        "--entrypoint", "soffice",
        libreoffice_image,
        "--headless",
        "--convert-to", "docx",
        "--outdir", "/data",
        filename,
    ]


def build_podman_command(input_filename: str, pandoc_image: str, tmpdir: str) -> list[str]:
    return [
        "podman", "run", "--rm",
        "-v", f"{tmpdir}:/data",
        "-w", "/data",
        pandoc_image,
        input_filename,
        "--to=typst",
        "--extract-media=images",
        "-o", "output.typ",
    ]


def convert(
    input_path: Path,
    output_path: Path,
    pandoc_image: str = "docker.io/pandoc/extra:latest",
    libreoffice_image: str = "docker.io/linuxserver/libreoffice:latest",
) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        work_file = tmp / input_path.name
        shutil.copy2(input_path, work_file)

        pandoc_input = input_path.name
        if input_path.suffix.lower() == ".doc":
            lo_cmd = build_doc_to_docx_command(input_path.name, libreoffice_image, tmpdir)
            lo_result = subprocess.run(lo_cmd, capture_output=True, text=True)
            if lo_result.returncode != 0:
                return False, lo_result.stderr.strip() or lo_result.stdout.strip()
            pandoc_input = input_path.stem + ".docx"

        cmd = build_podman_command(pandoc_input, pandoc_image, tmpdir)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return False, result.stderr.strip() or result.stdout.strip()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp / "output.typ"), str(output_path))

        src_images = tmp / "images"
        if src_images.exists():
            dest_images = output_path.parent / f"{output_path.stem}_images"
            if dest_images.exists():
                shutil.rmtree(dest_images)
            shutil.move(str(src_images), str(dest_images))
            # Pandoc writes image paths as "images/..." — rewrite to match renamed dir
            typ_content = output_path.read_text(encoding="utf-8")
            output_path.write_text(
                typ_content.replace('"images/', f'"{output_path.stem}_images/'),
                encoding="utf-8",
            )

    return True, ""
