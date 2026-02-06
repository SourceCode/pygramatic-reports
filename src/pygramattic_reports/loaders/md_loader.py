"""Markdown file loader."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import mistune

from pygramattic_reports.exceptions import LoaderError
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import ContentType, RawData, SourceType
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.storage.checksum import compute_checksum

from .base import BaseLoader

if TYPE_CHECKING:
    from pathlib import Path

    from pygramattic_reports.models import SourceConfig

_logger = get_logger("loaders.md")

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class MdLoader(BaseLoader):
    """Loads Markdown files into RawData objects.

    Uses ``mistune`` to parse the markdown structure, extracting
    headings, paragraphs, code blocks, lists, and tables.
    """

    def load(self, config: SourceConfig) -> RawData:
        """Load a Markdown file into a RawData object.

        Args:
            config: Source configuration with file path and options.

        Returns:
            RawData with ``content_type=DOCUMENT``.

        Raises:
            LoaderError: If the file cannot be read or parsed.
        """
        if config.file is None:
            msg = "MD loader requires file configuration"
            raise LoaderError(msg, source_type="md")

        file_path = config.file.path
        if not file_path.is_file():
            msg = f"File not found: {file_path}"
            raise LoaderError(msg, source_type="md", source_path=str(file_path))

        checksum = _compute_checksum(file_path)
        text = _read_file(file_path, config.file.encoding)
        text = _strip_frontmatter(text)

        tokens = _parse_markdown(text)
        document_text = _extract_blocks(tokens)
        tabular_data, tabular_headers = _extract_tables(tokens)

        _logger.info(
            "Loaded Markdown file",
            path=str(file_path),
            blocks=len(document_text),
            has_table=tabular_headers is not None,
        )

        return RawData(
            id=generate_id(),
            source_config=config,
            content_type=ContentType.DOCUMENT,
            document_text=document_text,
            tabular_data=tabular_data,
            tabular_headers=tabular_headers,
            loaded_at=now_utc(),
            source_checksum=checksum,
        )

    def supported_types(self) -> list[str]:
        """Return supported source types."""
        return [SourceType.MD]


def _compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of the source file."""
    try:
        return compute_checksum(file_path)
    except OSError as exc:
        msg = f"Failed to compute checksum for {file_path}: {exc}"
        raise LoaderError(msg, source_type="md", source_path=str(file_path)) from exc


def _read_file(file_path: Path, encoding: str) -> str:
    """Read the entire file as text."""
    try:
        return file_path.read_text(encoding=encoding)
    except UnicodeDecodeError as exc:
        msg = f"Encoding error reading {file_path}: {exc}"
        raise LoaderError(msg, source_type="md", source_path=str(file_path)) from exc
    except OSError as exc:
        msg = f"Failed to read {file_path}: {exc}"
        raise LoaderError(msg, source_type="md", source_path=str(file_path)) from exc


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter from the beginning of the text."""
    match = _FRONTMATTER_RE.match(text)
    if match:
        _logger.debug("Stripped YAML frontmatter")
        return text[match.end() :]
    return text


def _parse_markdown(text: str) -> list[dict[str, Any]]:
    """Parse markdown text into AST tokens using mistune."""
    md = mistune.create_markdown(renderer="ast", plugins=["table"])
    return md(text)  # type: ignore[return-value]


def _extract_text(token: dict[str, Any]) -> str:
    """Recursively extract plain text from a mistune AST token."""
    if "raw" in token:
        return str(token["raw"])
    if "children" in token and isinstance(token["children"], list):
        return "".join(_extract_text(child) for child in token["children"])
    return ""


def _extract_blocks(tokens: list[dict[str, Any]]) -> list[str]:
    """Convert AST tokens into document text blocks."""
    blocks: list[str] = []
    for token in tokens:
        block = _token_to_block(token)
        if block is not None:
            blocks.append(block)
    return blocks


def _token_to_block(token: dict[str, Any]) -> str | None:
    """Convert a single AST token to a text block."""
    kind = token.get("type", "")

    if kind == "heading":
        level: int = token.get("attrs", {}).get("level", 1)
        text = _extract_text(token)
        return "#" * level + " " + text

    if kind == "paragraph":
        text = _extract_text(token)
        return text if text.strip() else None

    if kind == "block_code":
        info = token.get("attrs", {}).get("info", "")
        code = token.get("raw", "").rstrip("\n")
        return f"```{info}\n{code}\n```"

    if kind == "list":
        return _list_to_block(token)

    if kind in ("blank_line", "thematic_break", "table"):
        return None

    # Fallback: extract any text content
    text = _extract_text(token)
    return text if text.strip() else None


def _list_to_block(token: dict[str, Any]) -> str:
    """Convert a list token to a text block with bullet markers."""
    items: list[str] = []
    ordered = token.get("attrs", {}).get("ordered", False)
    for i, child in enumerate(token.get("children", []), start=1):
        text = _extract_text(child).strip()
        prefix = f"{i}. " if ordered else "- "
        items.append(prefix + text)
    return "\n".join(items)


def _extract_tables(
    tokens: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]] | None, list[str] | None]:
    """Extract the first table from AST tokens as tabular data."""
    for token in tokens:
        if token.get("type") != "table":
            continue
        return _parse_table_token(token)
    return None, None


def _parse_table_token(
    token: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse a mistune table AST token into headers and row dicts."""
    headers: list[str] = []
    rows: list[dict[str, Any]] = []

    for child in token.get("children", []):
        if child.get("type") == "table_head":
            headers = [
                _extract_text(cell).strip()
                for cell in child.get("children", [])
            ]
        elif child.get("type") == "table_body":
            for row_token in child.get("children", []):
                values = [
                    _extract_text(cell).strip()
                    for cell in row_token.get("children", [])
                ]
                rows.append(dict(zip(headers, values, strict=False)))

    return rows, headers
