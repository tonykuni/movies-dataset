"""Local, bounded extraction for common article and document formats."""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".log", ".json", ".jsonl", ".csv", ".tsv", ".html", ".htm", ".xml",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".py", ".ps1", ".js", ".ts", ".sql", ".docx", ".pdf",
}
MARKITDOWN_EXTENSIONS = SUPPORTED_EXTENSIONS | {
    ".pptx", ".xlsx", ".xls", ".epub",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff",
    ".wav", ".mp3", ".m4a", ".flac",
}
DEFAULT_MAX_FILE_BYTES = 50 * 1024 * 1024
WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored += 1
        elif tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored:
            self._ignored -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self.parts)).strip()


def _decode_bytes(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "big5", "cp950", "gb18030"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def _flatten_json(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        output: list[str] = []
        for key, item in value.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            output.extend(_flatten_json(item, name))
        return output
    if isinstance(value, list):
        output = []
        for index, item in enumerate(value):
            output.extend(_flatten_json(item, f"{prefix}[{index}]"))
        return output
    return [f"{prefix}: {value}" if prefix else str(value)]


def _read_docx_stdlib(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        raw = archive.read("word/document.xml")
    root = ElementTree.fromstring(raw)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", WORD_NAMESPACE):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", WORD_NAMESPACE)).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def read_local_document(
    path: str | Path,
    max_bytes: int = DEFAULT_MAX_FILE_BYTES,
    use_markitdown: bool = False,
) -> dict[str, Any]:
    selected = Path(path).expanduser().resolve(strict=True)
    if not selected.is_file():
        raise ValueError("path must point to a regular file")
    suffix = selected.suffix.lower()
    allowed = MARKITDOWN_EXTENSIONS if use_markitdown else SUPPORTED_EXTENSIONS
    if suffix not in allowed:
        raise ValueError(f"Unsupported extension {suffix}; allowed: {sorted(allowed)}")
    size = selected.stat().st_size
    if size > max_bytes:
        raise ValueError(f"File exceeds maximum size of {max_bytes} bytes")

    metadata: dict[str, Any] = {"path": str(selected), "extension": suffix, "size_bytes": size}
    if use_markitdown:
        text = _read_with_markitdown(selected)
        metadata.update(
            {
                "backend": "microsoft_markitdown_local",
                "projection": "markdown_for_text_analysis_not_pixel_perfect_layout",
                "plugins_enabled": False,
                "llm_enabled": False,
                "network_enabled": False,
            }
        )
    elif suffix == ".docx":
        text = _read_docx_stdlib(selected)
        metadata["backend"] = "stdlib_ooxml"
    elif suffix == ".pdf":
        if importlib.util.find_spec("pypdf") is None:
            raise RuntimeError("Install the 'documents' extra to read PDF files")
        from pypdf import PdfReader

        reader = PdfReader(str(selected))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        metadata.update({"backend": "pypdf", "pages": len(reader.pages)})
    else:
        raw = selected.read_bytes()
        decoded, encoding = _decode_bytes(raw)
        metadata.update({"backend": "stdlib", "encoding": encoding})
        if suffix in {".html", ".htm"}:
            parser = _HTMLTextExtractor()
            parser.feed(decoded)
            text = parser.text()
        elif suffix == ".json":
            text = "\n".join(_flatten_json(json.loads(decoded)))
        elif suffix == ".jsonl":
            rows = [json.loads(line) for line in decoded.splitlines() if line.strip()]
            text = "\n".join(line for row in rows for line in _flatten_json(row))
        elif suffix in {".csv", ".tsv"}:
            dialect = csv.excel_tab if suffix == ".tsv" else csv.excel
            rows = csv.reader(io.StringIO(decoded), dialect=dialect)
            text = "\n".join(" | ".join(cell for cell in row) for row in rows)
        else:
            text = decoded
    metadata["text_chars"] = len(text)
    return {"text": text, "metadata": metadata}


def _read_with_markitdown(path: Path) -> str:
    if importlib.util.find_spec("markitdown") is None:
        raise RuntimeError("Install the 'markitdown' extra to enable Microsoft MarkItDown local extraction")
    from markitdown import MarkItDown

    converter = MarkItDown(enable_plugins=False)
    convert_local = getattr(converter, "convert_local", None)
    if convert_local is None:
        raise RuntimeError("Installed MarkItDown version lacks convert_local(); remote-capable fallback is intentionally blocked")
    result = convert_local(str(path))
    text = getattr(result, "text_content", None)
    if not isinstance(text, str):
        raise RuntimeError("MarkItDown did not return a text_content string")
    return text
