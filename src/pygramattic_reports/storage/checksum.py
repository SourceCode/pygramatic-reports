"""SHA-256 checksum utilities for verifying data integrity."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_CHUNK_SIZE = 65536  # 64 KB


def compute_checksum(file_path: Path) -> str:
    """Compute the SHA-256 checksum of a file.

    Reads the file in chunks to support large files without
    excessive memory usage.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    sha = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            sha.update(chunk)
    return sha.hexdigest()


def verify_checksum(file_path: Path, expected: str) -> bool:
    """Verify that a file's checksum matches the expected value.

    Args:
        file_path: Path to the file to verify.
        expected: Expected hex-encoded SHA-256 hash.

    Returns:
        ``True`` if the checksums match, ``False`` otherwise.
    """
    return compute_checksum(file_path) == expected
