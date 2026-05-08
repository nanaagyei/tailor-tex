"""Text extraction from resume files (PDF, DOCX, Markdown, plain text).

Each extractor returns raw text and diagnostics. File type is detected
by extension with a magic-byte fallback for PDF.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExtractionResult:
    text: str
    file_type: str
    diagnostics: list[str] = field(default_factory=list)
    page_count: int | None = None


def extract_text(path: str | Path) -> ExtractionResult:
    """Extract raw text from a resume file.

    Supports: PDF (.pdf), DOCX (.docx), Markdown (.md), plain text (.txt).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    # Magic-byte fallback for PDF
    if suffix not in (".pdf", ".docx", ".md", ".txt"):
        with open(path, "rb") as f:
            header = f.read(5)
        if header == b"%PDF-":
            suffix = ".pdf"
        else:
            raise ValueError(
                f"Unsupported file type: {path.suffix}. Accepted: .pdf, .docx, .md, .txt"
            )

    if suffix == ".pdf":
        return _extract_pdf(path)
    elif suffix == ".docx":
        return _extract_docx(path)
    elif suffix == ".md":
        return _extract_markdown(path)
    else:
        return _extract_plaintext(path)


def _extract_pdf(path: Path) -> ExtractionResult:
    """Extract text from PDF using PyMuPDF."""
    try:
        import pymupdf
    except ImportError as err:
        raise ImportError(
            "PyMuPDF is required for PDF extraction. Install with: pip install pymupdf"
        ) from err

    diagnostics: list[str] = []
    pages: list[str] = []

    doc = pymupdf.open(str(path))
    for i, page in enumerate(doc):
        text = page.get_text()
        if not text.strip():
            diagnostics.append(f"Page {i + 1} has no extractable text (may be image-based).")
        pages.append(text)

    full_text = "\n".join(pages).strip()
    if not full_text:
        diagnostics.append("No text extracted from PDF. The file may be image-based or empty.")

    return ExtractionResult(
        text=full_text,
        file_type="pdf",
        diagnostics=diagnostics,
        page_count=len(doc),
    )


def _extract_docx(path: Path) -> ExtractionResult:
    """Extract text from DOCX using python-docx."""
    try:
        import docx
    except ImportError as err:
        raise ImportError(
            "python-docx is required for DOCX extraction. Install with: pip install python-docx"
        ) from err

    diagnostics: list[str] = []
    doc = docx.Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs]
    full_text = "\n".join(paragraphs).strip()

    if not full_text:
        diagnostics.append("No text extracted from DOCX. The file may be empty.")

    return ExtractionResult(
        text=full_text,
        file_type="docx",
        diagnostics=diagnostics,
    )


def _extract_markdown(path: Path) -> ExtractionResult:
    """Extract text from Markdown, stripping frontmatter."""
    raw = path.read_text(encoding="utf-8")

    # Strip YAML frontmatter
    text = raw
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2].strip()

    return ExtractionResult(
        text=text,
        file_type="markdown",
        diagnostics=[],
    )


def _extract_plaintext(path: Path) -> ExtractionResult:
    """Read plain text as-is."""
    text = path.read_text(encoding="utf-8").strip()
    return ExtractionResult(
        text=text,
        file_type="plaintext",
        diagnostics=[],
    )
