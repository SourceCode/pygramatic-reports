"""Core storage manager for pygramattic-reports.

Manages the ``data/`` directory structure, dataset persistence,
manifest tracking, and file retrieval for all pipeline stages.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pandas as pd

from pygramattic_reports.exceptions import StorageError
from pygramattic_reports.logging import get_logger
from pygramattic_reports.models import (
    Manifest,
    Provenance,
)
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.models.dataset import Dataset

from .checksum import compute_checksum
from .manifest_io import read_manifest, write_manifest

if TYPE_CHECKING:
    from pathlib import Path

    from pygramattic_reports.config import AppConfig

_VALID_DATA_STAGES = frozenset({"raw", "processed", "derived"})
_VALID_STAGES = frozenset({"raw", "processed", "derived", "reports", "media"})


class StorageManager:
    """Manages the ``data/`` directory structure and dataset persistence.

    Directory layout::

        data/
          raw/{dataset_id}/
            manifest.json
            data.csv (or .json)
          processed/{dataset_id}/
            manifest.json
            provenance.json
            data.parquet (or .csv fallback)
          derived/{dataset_id}/
            manifest.json
            provenance.json
            data.parquet (or .csv fallback)
          reports/{report_id}/
            {filename}
            build_log.json
          media/{report_id}/
            chart_001.png

    Usage::

        storage = StorageManager(config)
        storage.initialize()
        dataset_id = storage.save_dataset(dataset)
        loaded = storage.load_dataset(dataset_id)
    """

    def __init__(self, config: AppConfig) -> None:  # noqa: D107
        self._data_dir = config.storage.data_dir
        self._stage_dirs: dict[str, str] = {
            "raw": config.storage.raw_dir,
            "processed": config.storage.processed_dir,
            "derived": config.storage.derived_dir,
            "reports": config.storage.reports_dir,
            "media": config.storage.media_dir,
        }
        self._logger = get_logger("storage")

    def initialize(self) -> None:
        """Create the ``data/`` directory structure if it does not exist.

        Creates: raw/, processed/, derived/, reports/, media/.
        Idempotent: safe to call multiple times.
        """
        for subdir_name in self._stage_dirs.values():
            (self._data_dir / subdir_name).mkdir(parents=True, exist_ok=True)
        self._logger.info("Storage initialized", data_dir=str(self._data_dir))

    def save_raw(
        self,
        data: bytes | str,
        metadata: dict[str, Any],
        format: str = "csv",  # noqa: A002
    ) -> str:
        """Save raw ingested data to ``data/raw/{id}/``.

        Args:
            data: Raw file content (bytes or string).
            metadata: Source metadata (``name``, ``source_type``,
                ``source_path``, ``row_count``, ``tags``).
            format: File format extension (e.g. ``"csv"``, ``"json"``).

        Returns:
            Dataset ID (UUID string).
        """
        dataset_id = generate_id()
        dataset_dir = self._resolve_stage_dir("raw") / dataset_id
        dataset_dir.mkdir(parents=True, exist_ok=True)

        data_file = dataset_dir / f"data.{format}"
        content = data.encode("utf-8") if isinstance(data, str) else data
        self._atomic_write_bytes(data_file, content)

        checksum = compute_checksum(data_file)

        manifest = Manifest(
            id=dataset_id,
            name=metadata.get("name", "raw_data"),
            source_type=metadata.get("source_type", "unknown"),
            source_path=metadata.get("source_path"),
            columns=[],
            row_count=metadata.get("row_count", 0),
            checksum=checksum,
            created_at=now_utc(),
            storage_path=f"raw/{dataset_id}",
            format=format,
            size_bytes=data_file.stat().st_size,
            tags=metadata.get("tags", []),
        )
        write_manifest(manifest, dataset_dir)
        self._logger.info(
            "Saved raw data",
            dataset_id=dataset_id,
            format=format,
            size_bytes=manifest.size_bytes,
        )
        return dataset_id

    def save_dataset(self, dataset: Dataset, stage: str = "processed") -> str:
        """Save a normalized Dataset to the specified stage directory.

        Args:
            dataset: The Dataset object (with DataFrame).
            stage: ``"processed"`` or ``"derived"``.

        Returns:
            Dataset ID.

        Raises:
            StorageError: If the stage is invalid or the write fails.
        """
        if stage not in ("processed", "derived"):
            msg = f"Invalid stage for save_dataset: {stage!r} (expected 'processed' or 'derived')"
            raise StorageError(msg)

        dataset_dir = self._resolve_stage_dir(stage) / dataset.id
        dataset_dir.mkdir(parents=True, exist_ok=True)

        data_path, fmt = self._write_dataframe(dataset.dataframe, dataset_dir)
        checksum = compute_checksum(data_path)

        manifest = Manifest(
            id=dataset.id,
            name=dataset.name,
            source_type=dataset.provenance.source_type,
            source_path=dataset.provenance.source_path,
            columns=list(dataset.schema),
            row_count=dataset.row_count,
            checksum=checksum,
            created_at=dataset.created_at,
            storage_path=f"{stage}/{dataset.id}",
            format=fmt,
            size_bytes=data_path.stat().st_size,
        )
        write_manifest(manifest, dataset_dir)
        self._write_provenance(dataset.provenance, dataset_dir)

        self._logger.info(
            "Saved dataset",
            dataset_id=dataset.id,
            stage=stage,
            format=fmt,
            rows=dataset.row_count,
        )
        return dataset.id

    def load_dataset(self, dataset_id: str, stage: str = "processed") -> Dataset:
        """Load a Dataset from storage by ID.

        Args:
            dataset_id: UUID of the dataset.
            stage: Which directory to look in.

        Returns:
            Reconstructed Dataset with DataFrame loaded.

        Raises:
            StorageError: If the dataset is not found or data is corrupt.
        """
        dataset_dir = self._resolve_stage_dir(stage) / dataset_id
        if not dataset_dir.is_dir():
            msg = f"Dataset {dataset_id!r} not found in stage {stage!r}"
            raise StorageError(msg)

        manifest = read_manifest(dataset_dir)
        df = self._read_dataframe(dataset_dir, manifest.format)
        provenance = self._read_provenance(dataset_dir, manifest)

        return Dataset(
            id=manifest.id,
            name=manifest.name,
            schema=list(manifest.columns),
            dataframe=df,
            provenance=provenance,
            created_at=manifest.created_at,
        )

    def get_manifest(self, dataset_id: str, stage: str = "processed") -> Manifest:
        """Load just the manifest for a dataset without loading the data.

        Useful for listing and querying datasets without memory overhead.

        Args:
            dataset_id: UUID of the dataset.
            stage: Which directory to look in.

        Returns:
            The dataset's ``Manifest``.

        Raises:
            StorageError: If the dataset or manifest is not found.
        """
        dataset_dir = self._resolve_stage_dir(stage) / dataset_id
        if not dataset_dir.is_dir():
            msg = f"Dataset {dataset_id!r} not found in stage {stage!r}"
            raise StorageError(msg)
        return read_manifest(dataset_dir)

    def list_datasets(self, stage: str | None = None) -> list[Manifest]:
        """List all datasets, optionally filtered by stage.

        Args:
            stage: Stage to filter by (``"raw"``, ``"processed"``,
                ``"derived"``), or ``None`` for all data stages.

        Returns:
            Manifests sorted by creation date (newest first).
        """
        stages = [stage] if stage else sorted(_VALID_DATA_STAGES)
        manifests: list[Manifest] = []

        for s in stages:
            stage_dir = self._resolve_stage_dir(s)
            if not stage_dir.is_dir():
                continue
            for dataset_dir in sorted(stage_dir.iterdir()):
                if not dataset_dir.is_dir():
                    continue
                try:
                    manifests.append(read_manifest(dataset_dir))
                except StorageError:
                    self._logger.warning(
                        "Skipping corrupt manifest",
                        path=str(dataset_dir),
                    )

        manifests.sort(key=lambda m: m.created_at, reverse=True)
        return manifests

    def save_report(
        self,
        report_id: str,
        content: bytes,
        filename: str,
        build_log: dict[str, Any] | None = None,
    ) -> Path:
        """Save a generated report file.

        Args:
            report_id: UUID of the report.
            content: Report file content.
            filename: Output filename (e.g. ``"report.docx"``).
            build_log: Optional build log dict to save alongside.

        Returns:
            Path to the saved report file.
        """
        report_dir = self._resolve_stage_dir("reports") / report_id
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / filename
        self._atomic_write_bytes(report_path, content)

        if build_log is not None:
            log_path = report_dir / "build_log.json"
            log_bytes = json.dumps(build_log, indent=2, default=str).encode("utf-8")
            self._atomic_write_bytes(log_path, log_bytes)

        self._logger.info(
            "Saved report",
            report_id=report_id,
            filename=filename,
            size_bytes=len(content),
        )
        return report_path

    def save_media(self, report_id: str, content: bytes, filename: str) -> Path:
        """Save a media file (chart image) associated with a report.

        Args:
            report_id: UUID of the report this media belongs to.
            content: Image bytes.
            filename: Filename (e.g. ``"chart_revenue.png"``).

        Returns:
            Path to the saved media file.
        """
        media_dir = self._resolve_stage_dir("media") / report_id
        media_dir.mkdir(parents=True, exist_ok=True)

        media_path = media_dir / filename
        self._atomic_write_bytes(media_path, content)

        self._logger.info(
            "Saved media",
            report_id=report_id,
            filename=filename,
            size_bytes=len(content),
        )
        return media_path

    def resolve_path(self, stage: str, dataset_id: str) -> Path:
        """Resolve the full filesystem path for a dataset directory.

        Args:
            stage: Stage name (e.g. ``"processed"``).
            dataset_id: UUID of the dataset.

        Returns:
            Full path to the dataset directory.

        Raises:
            StorageError: If the stage name is invalid.
        """
        return self._resolve_stage_dir(stage) / dataset_id

    # ---- Private helpers ----

    def _resolve_stage_dir(self, stage: str) -> Path:
        """Resolve the directory path for a given stage."""
        if stage not in _VALID_STAGES:
            msg = f"Invalid stage: {stage!r}"
            raise StorageError(msg)
        return self._data_dir / self._stage_dirs[stage]

    def _write_dataframe(
        self,
        df: pd.DataFrame,
        directory: Path,
    ) -> tuple[Path, str]:
        """Write a DataFrame to storage, preferring Parquet.

        Returns:
            Tuple of (data file path, format string).
        """
        try:
            path = directory / "data.parquet"
            tmp = path.with_suffix(".parquet.tmp")
            df.to_parquet(tmp)
            tmp.replace(path)
        except ImportError:
            path = directory / "data.csv"
            tmp = path.with_suffix(".csv.tmp")
            df.to_csv(tmp, index=False)
            tmp.replace(path)
            return path, "csv"
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        return path, "parquet"

    def _read_dataframe(self, directory: Path, fmt: str) -> pd.DataFrame:
        """Read a DataFrame from a data file."""
        data_file = directory / f"data.{fmt}"
        if not data_file.is_file():
            msg = f"Data file not found: {data_file}"
            raise StorageError(msg)
        if fmt == "parquet":
            return pd.read_parquet(data_file)
        return pd.read_csv(data_file)

    def _write_provenance(self, provenance: Provenance, directory: Path) -> None:
        """Save provenance data alongside the dataset."""
        prov_path = directory / "provenance.json"
        content = provenance.model_dump_json(indent=2).encode("utf-8")
        self._atomic_write_bytes(prov_path, content)

    def _read_provenance(self, directory: Path, manifest: Manifest) -> Provenance:
        """Load provenance data, falling back to manifest metadata."""
        prov_path = directory / "provenance.json"
        if prov_path.is_file():
            try:
                return Provenance.model_validate_json(prov_path.read_text())
            except Exception:
                self._logger.warning(
                    "Could not read provenance.json, reconstructing from manifest",
                    path=str(prov_path),
                )
        return Provenance(
            source_type=manifest.source_type,
            source_path=manifest.source_path,
            source_name=manifest.name,
            loaded_at=manifest.created_at,
            normalized_at=manifest.created_at,
            row_count_raw=manifest.row_count,
        )

    @staticmethod
    def _atomic_write_bytes(path: Path, content: bytes) -> None:
        """Write bytes to a file atomically via temp file + rename."""
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            tmp.write_bytes(content)
            tmp.replace(path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
