import shutil
import subprocess
import tempfile
from pathlib import Path


def check_podman() -> bool:
    return shutil.which("podman") is not None


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
    pandoc_image: str = "pandoc/extra:latest",
) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        work_file = tmp / input_path.name
        shutil.copy2(input_path, work_file)

        cmd = build_podman_command(input_path.name, pandoc_image, tmpdir)

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

    return True, ""
