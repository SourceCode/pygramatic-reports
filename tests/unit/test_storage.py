"""Unit tests for the storage manager."""

import json

import pandas as pd
import pytest

from pygramattic_reports.config import load_config
from pygramattic_reports.exceptions import StorageError
from pygramattic_reports.models import ColumnSchema, DataType, Manifest, Provenance
from pygramattic_reports.models.base import generate_id, now_utc
from pygramattic_reports.models.dataset import Dataset
from pygramattic_reports.storage import StorageManager
from pygramattic_reports.storage.checksum import compute_checksum, verify_checksum
from pygramattic_reports.storage.manifest_io import read_manifest, write_manifest


@pytest.fixture
def storage(tmp_path):
    """Create an initialized StorageManager with a temp data directory."""
    config = load_config(overrides={"storage": {"data_dir": str(tmp_path)}})
    mgr = StorageManager(config)
    mgr.initialize()
    return mgr


@pytest.fixture
def sample_dataset():
    """Create a simple Dataset for testing."""
    df = pd.DataFrame({"region": ["US", "EU"], "revenue": [1000, 2000]})
    return Dataset(
        id=generate_id(),
        name="revenue",
        schema=[
            ColumnSchema(name="region", dtype=DataType.STRING),
            ColumnSchema(name="revenue", dtype=DataType.INTEGER),
        ],
        dataframe=df,
        provenance=Provenance(
            source_type="csv",
            source_name="test_revenue",
            source_path="/data/revenue.csv",
            loaded_at=now_utc(),
            normalized_at=now_utc(),
            row_count_raw=2,
        ),
    )


# ---- Directory Initialization ----


class TestInitialize:
    def test_creates_directories(self, storage, tmp_path):
        for subdir in ["raw", "processed", "derived", "reports", "media"]:
            assert (tmp_path / subdir).is_dir()

    def test_is_idempotent(self, storage):
        # Calling initialize again should not raise
        storage.initialize()
        storage.initialize()


# ---- Raw Data ----


class TestSaveRaw:
    def test_creates_manifest_and_data(self, storage, tmp_path):
        csv_data = "name,value\nalice,10\nbob,20\n"
        metadata = {
            "name": "test_raw",
            "source_type": "csv",
            "source_path": "/input/test.csv",
            "row_count": 2,
        }
        dataset_id = storage.save_raw(csv_data, metadata, format="csv")

        dataset_dir = tmp_path / "raw" / dataset_id
        assert dataset_dir.is_dir()
        assert (dataset_dir / "manifest.json").is_file()
        assert (dataset_dir / "data.csv").is_file()

        # Verify manifest content
        manifest = read_manifest(dataset_dir)
        assert manifest.id == dataset_id
        assert manifest.name == "test_raw"
        assert manifest.source_type == "csv"
        assert manifest.format == "csv"
        assert manifest.checksum is not None
        assert manifest.size_bytes is not None
        assert manifest.size_bytes > 0

    def test_save_raw_bytes(self, storage, tmp_path):
        raw_bytes = b'{"key": "value"}'
        metadata = {"name": "json_raw", "source_type": "json"}
        dataset_id = storage.save_raw(raw_bytes, metadata, format="json")

        data_file = tmp_path / "raw" / dataset_id / "data.json"
        assert data_file.read_bytes() == raw_bytes


# ---- Dataset Save/Load ----


class TestSaveDataset:
    def test_creates_parquet(self, storage, sample_dataset, tmp_path):
        storage.save_dataset(sample_dataset)

        dataset_dir = tmp_path / "processed" / sample_dataset.id
        assert dataset_dir.is_dir()
        assert (dataset_dir / "manifest.json").is_file()
        assert (dataset_dir / "provenance.json").is_file()
        # Should have a data file (parquet or csv)
        data_files = list(dataset_dir.glob("data.*"))
        assert len(data_files) == 1

    def test_roundtrip(self, storage, sample_dataset):
        storage.save_dataset(sample_dataset)
        loaded = storage.load_dataset(sample_dataset.id)

        assert loaded.id == sample_dataset.id
        assert loaded.name == sample_dataset.name
        assert loaded.row_count == 2
        assert list(loaded.dataframe.columns) == ["region", "revenue"]
        assert loaded.dataframe["revenue"].tolist() == [1000, 2000]

    def test_roundtrip_preserves_provenance(self, storage, sample_dataset):
        storage.save_dataset(sample_dataset)
        loaded = storage.load_dataset(sample_dataset.id)

        assert loaded.provenance.source_type == "csv"
        assert loaded.provenance.source_name == "test_revenue"
        assert loaded.provenance.source_path == "/data/revenue.csv"
        assert loaded.provenance.row_count_raw == 2

    def test_save_to_derived_stage(self, storage, sample_dataset):
        storage.save_dataset(sample_dataset, stage="derived")
        loaded = storage.load_dataset(sample_dataset.id, stage="derived")
        assert loaded.row_count == 2

    def test_invalid_stage_raises(self, storage, sample_dataset):
        with pytest.raises(StorageError, match="Invalid stage"):
            storage.save_dataset(sample_dataset, stage="raw")


class TestLoadDataset:
    def test_not_found_raises(self, storage):
        with pytest.raises(StorageError, match="not found"):
            storage.load_dataset("nonexistent-id")

    def test_not_found_in_stage(self, storage, sample_dataset):
        storage.save_dataset(sample_dataset, stage="processed")
        with pytest.raises(StorageError, match="not found"):
            storage.load_dataset(sample_dataset.id, stage="derived")


# ---- Manifest Operations ----


class TestManifest:
    def test_roundtrip(self, tmp_path):
        manifest = Manifest(
            id="test-id",
            name="test",
            source_type="csv",
            columns=[ColumnSchema(name="col1", dtype=DataType.STRING)],
            row_count=10,
            checksum="abc123",
            created_at=now_utc(),
            storage_path="processed/test-id",
            format="parquet",
            size_bytes=1024,
        )
        write_manifest(manifest, tmp_path)
        loaded = read_manifest(tmp_path)

        assert loaded.id == manifest.id
        assert loaded.name == manifest.name
        assert loaded.columns == manifest.columns
        assert loaded.checksum == manifest.checksum

    def test_read_missing_raises(self, tmp_path):
        with pytest.raises(StorageError, match="not found"):
            read_manifest(tmp_path / "nonexistent")

    def test_read_corrupt_raises(self, tmp_path):
        (tmp_path / "manifest.json").write_text("not valid json {{{")
        with pytest.raises(StorageError, match="Corrupt manifest"):
            read_manifest(tmp_path)

    def test_read_invalid_schema_raises(self, tmp_path):
        (tmp_path / "manifest.json").write_text('{"invalid": "schema"}')
        with pytest.raises(StorageError, match="Invalid manifest"):
            read_manifest(tmp_path)

    def test_get_manifest(self, storage, sample_dataset):
        storage.save_dataset(sample_dataset)
        manifest = storage.get_manifest(sample_dataset.id)
        assert manifest.id == sample_dataset.id
        assert manifest.row_count == 2


# ---- List Datasets ----


class TestListDatasets:
    def test_lists_all(self, storage, tmp_path):
        df = pd.DataFrame({"x": [1, 2, 3]})
        for name in ["alpha", "beta"]:
            ds = Dataset(
                id=generate_id(),
                name=name,
                schema=[ColumnSchema(name="x", dtype=DataType.INTEGER)],
                dataframe=df,
                provenance=Provenance(
                    source_type="csv",
                    source_name=name,
                    loaded_at=now_utc(),
                    normalized_at=now_utc(),
                    row_count_raw=3,
                ),
            )
            storage.save_dataset(ds)

        manifests = storage.list_datasets(stage="processed")
        assert len(manifests) == 2

    def test_filtered_by_stage(self, storage, sample_dataset):
        storage.save_dataset(sample_dataset, stage="processed")
        assert len(storage.list_datasets(stage="processed")) == 1
        assert len(storage.list_datasets(stage="derived")) == 0

    def test_empty_when_no_datasets(self, storage):
        assert storage.list_datasets() == []


# ---- Reports and Media ----


class TestSaveReport:
    def test_saves_report_file(self, storage, tmp_path):
        content = b"# My Report\n\nHello world."
        path = storage.save_report("rpt-001", content, "report.md")

        assert path.is_file()
        assert path.read_bytes() == content
        assert path == tmp_path / "reports" / "rpt-001" / "report.md"

    def test_saves_with_build_log(self, storage, tmp_path):
        content = b"Report content"
        log = {"status": "completed", "entries": []}
        storage.save_report("rpt-002", content, "report.docx", build_log=log)

        log_path = tmp_path / "reports" / "rpt-002" / "build_log.json"
        assert log_path.is_file()
        saved_log = json.loads(log_path.read_text())
        assert saved_log["status"] == "completed"


class TestSaveMedia:
    def test_saves_media_file(self, storage, tmp_path):
        # Fake PNG bytes
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        path = storage.save_media("rpt-001", png_bytes, "chart_revenue.png")

        assert path.is_file()
        assert path.read_bytes() == png_bytes
        assert path == tmp_path / "media" / "rpt-001" / "chart_revenue.png"


# ---- Checksum ----


class TestChecksum:
    def test_compute_checksum(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        checksum = compute_checksum(test_file)

        # SHA-256 of "hello world"
        assert len(checksum) == 64
        assert checksum == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def test_verify_checksum_valid(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        checksum = compute_checksum(test_file)
        assert verify_checksum(test_file, checksum) is True

    def test_verify_checksum_invalid(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        assert verify_checksum(test_file, "wrong_hash") is False

    def test_dataset_checksum_stored(self, storage, sample_dataset):
        storage.save_dataset(sample_dataset)
        manifest = storage.get_manifest(sample_dataset.id)
        assert manifest.checksum is not None
        assert len(manifest.checksum) == 64


# ---- Resolve Path ----


class TestResolvePath:
    def test_resolve_valid_path(self, storage, tmp_path):
        path = storage.resolve_path("processed", "ds-001")
        assert path == tmp_path / "processed" / "ds-001"

    def test_resolve_invalid_stage_raises(self, storage):
        with pytest.raises(StorageError, match="Invalid stage"):
            storage.resolve_path("invalid_stage", "ds-001")
