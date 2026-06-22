"""Integration tests — require podman and network access to pull pandoc/extra."""
import shutil
from pathlib import Path

import pytest

from word_to_typst.converter import convert

PANDOC_IMAGE = "docker.io/pandoc/extra:latest"


@pytest.fixture(scope="session")
def sample_docx(tmp_path_factory):
    """Create a minimal valid .docx for integration testing."""
    import zipfile, io
    tmp = tmp_path_factory.mktemp("integration")
    docx_path = tmp / "sample.docx"

    # Minimal valid .docx structure
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
            xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Hello from integration test</w:t></w:r></w:p>
  </w:body>
</w:document>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("_rels/.rels", rels_xml)
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("word/document.xml", document_xml)
    docx_path.write_bytes(buf.getvalue())
    return docx_path


@pytest.mark.integration
def test_convert_docx_produces_typ(sample_docx, tmp_path):
    output = tmp_path / "out.typ"
    success, error = convert(sample_docx, output, PANDOC_IMAGE)
    assert success, f"Conversion failed: {error}"
    assert output.exists(), "output.typ not created"
    content = output.read_text()
    assert len(content) > 0, "output.typ is empty"


@pytest.mark.integration
def test_convert_docx_typ_is_valid(sample_docx, tmp_path):
    """Verify typst can compile the output without error."""
    import subprocess
    output = tmp_path / "out.typ"
    convert(sample_docx, output, PANDOC_IMAGE)
    result = subprocess.run(
        ["typst", "compile", str(output), str(tmp_path / "out.pdf")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"typst compile failed:\n{result.stderr}"
