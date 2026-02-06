"""Manifest file serialization for the storage subsystem.

Handles reading and writing ``manifest.json`` files with atomic
write support to prevent corruption on crash.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pydantic import ValidationError as PydanticValidationError

if TYPE_CHECKING:
    from pathlib import Path

from pygramattic_reports.exceptions import StorageError
from pygramattic_reports.models import Manifest


def write_manifest(manifest: Manifest, directory: Path) -> Path:
    """Write a ``manifest.json`` file to the specified directory.

    Uses atomic write (write to temp file, then rename) to prevent
    corruption if the process crashes mid-write.

    Args:
        manifest: The manifest model to serialize.
        directory: Target directory for the manifest file.

    Returns:
        Path to the written manifest file.

    Raises:
        StorageError: If the write fails.
    """
    manifest_path = directory / "manifest.json"
    tmp_path = manifest_path.with_suffix(".json.tmp")
    try:
        tmp_path.write_text(manifest.model_dump_json(indent=2))
        tmp_path.replace(manifest_path)
    except OSError as exc:
        tmp_path.unlink(missing_ok=True)
        msg = f"Failed to write manifest to {manifest_path}: {exc}"
        raise StorageError(msg) from exc
    return manifest_path


def read_manifest(directory: Path) -> Manifest:
    """Read and parse a ``manifest.json`` file from a directory.

    Args:
        directory: Directory containing the manifest file.

    Returns:
        The parsed ``Manifest`` model.

    Raises:
        StorageError: If the file is missing, corrupt, or invalid.
    """
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        msg = f"Manifest not found: {manifest_path}"
        raise StorageError(msg)
    try:
        data = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        msg = f"Corrupt manifest JSON in {manifest_path}: {exc}"
        raise StorageError(msg) from exc
    try:
        return Manifest.model_validate(data)
    except PydanticValidationError as exc:
        msg = f"Invalid manifest schema in {manifest_path}: {exc}"
        raise StorageError(msg) from exc
