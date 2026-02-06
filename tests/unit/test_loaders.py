"""Unit tests for data loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pygramattic_reports.exceptions import LoaderError
from pygramattic_reports.loaders import CsvLoader, JsonLoader, LoaderRegistry
from pygramattic_reports.models import (
    ContentType,
    FileSourceConfig,
    SourceConfig,
    SourceType,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _csv_config(path: Path, **kwargs: object) -> SourceConfig:
    """Build a SourceConfig for a CSV file."""
    return SourceConfig(
        source_type=SourceType.CSV,
        name="test_csv",
        file=FileSourceConfig(path=path, **kwargs),
    )


def _json_config(path: Path) -> SourceConfig:
    """Build a SourceConfig for a JSON file."""
    return SourceConfig(
        source_type=SourceType.JSON,
        name="test_json",
        file=FileSourceConfig(path=path),
    )


# ---- CSV Loader ----


class TestCsvLoaderBasic:
    def test_loads_sample_csv(self):
        loader = CsvLoader()
        config = _csv_config(FIXTURES_DIR / "sample.csv")
        raw = loader.load(config)

        assert raw.content_type == ContentType.TABULAR
        assert raw.tabular_headers == [
            "region",
            "revenue",
            "quarter",
            "growth_pct",
            "is_active",
        ]
        assert raw.row_count == 5
        assert len(raw.tabular_data) == 5
        assert raw.tabular_data[0]["region"] == "US"
        assert raw.tabular_data[0]["revenue"] == "1500.50"
        assert raw.source_checksum is not None

    def test_supported_types(self):
        loader = CsvLoader()
        assert SourceType.CSV in loader.supported_types()


class TestCsvLoaderCustomDelimiter:
    def test_semicolon_delimiter(self, tmp_path):
        csv_file = tmp_path / "semicolon.csv"
        csv_file.write_text("name;value;active\nalice;10;true\nbob;20;false\n")

        loader = CsvLoader()
        config = _csv_config(csv_file, delimiter=";")
        raw = loader.load(config)

        assert raw.tabular_headers == ["name", "value", "active"]
        assert raw.row_count == 2
        assert raw.tabular_data[0]["name"] == "alice"
        assert raw.tabular_data[1]["value"] == "20"


class TestCsvLoaderNoHeader:
    def test_generates_column_names(self, tmp_path):
        csv_file = tmp_path / "no_header.csv"
        csv_file.write_text("alice,10\nbob,20\n")

        loader = CsvLoader()
        config = _csv_config(csv_file, has_header=False)
        raw = loader.load(config)

        assert raw.tabular_headers == ["col_0", "col_1"]
        assert raw.row_count == 2
        assert raw.tabular_data[0]["col_0"] == "alice"


class TestCsvLoaderFileNotFound:
    def test_raises_loader_error(self, tmp_path):
        loader = CsvLoader()
        config = _csv_config(tmp_path / "nonexistent.csv")

        with pytest.raises(LoaderError, match="File not found"):
            loader.load(config)

    def test_raises_without_file_config(self):
        loader = CsvLoader()
        config = SourceConfig(source_type=SourceType.CSV, name="no_file")

        with pytest.raises(LoaderError, match="requires file configuration"):
            loader.load(config)


class TestCsvLoaderEncoding:
    def test_utf8_with_bom(self, tmp_path):
        csv_file = tmp_path / "bom.csv"
        bom = b"\xef\xbb\xbf"
        csv_file.write_bytes(bom + b"name,value\nalice,10\n")

        loader = CsvLoader()
        config = _csv_config(csv_file, encoding="utf-8")
        raw = loader.load(config)

        assert raw.tabular_headers == ["name", "value"]
        assert raw.tabular_data[0]["name"] == "alice"

    def test_latin1_encoding(self, tmp_path):
        csv_file = tmp_path / "latin1.csv"
        csv_file.write_bytes("name,city\nalice,Z\xfcrich\n".encode("latin-1"))

        loader = CsvLoader()
        config = _csv_config(csv_file, encoding="latin-1")
        raw = loader.load(config)

        assert raw.tabular_data[0]["city"] == "Z\u00fcrich"

    def test_wrong_encoding_raises(self, tmp_path):
        csv_file = tmp_path / "bad_enc.csv"
        csv_file.write_bytes(b"\xff\xfe" + "name\n".encode("utf-16-le"))

        loader = CsvLoader()
        config = _csv_config(csv_file, encoding="utf-8")

        with pytest.raises(LoaderError, match="Encoding error"):
            loader.load(config)


# ---- JSON Loader ----


class TestJsonLoaderTabular:
    def test_loads_tabular_json(self):
        loader = JsonLoader()
        config = _json_config(FIXTURES_DIR / "sample_tabular.json")
        raw = loader.load(config)

        assert raw.content_type == ContentType.TABULAR
        assert raw.tabular_headers == ["name", "price", "quantity", "launch_date"]
        assert raw.row_count == 3
        assert raw.tabular_data[0]["name"] == "Product A"
        assert raw.tabular_data[0]["price"] == 29.99
        assert raw.source_checksum is not None

    def test_supported_types(self):
        loader = JsonLoader()
        assert SourceType.JSON in loader.supported_types()


class TestJsonLoaderDocument:
    def test_loads_document_json(self):
        loader = JsonLoader()
        config = _json_config(FIXTURES_DIR / "sample_document.json")
        raw = loader.load(config)

        assert raw.content_type == ContentType.DOCUMENT
        assert raw.document_text is not None
        assert len(raw.document_text) == 1
        parsed = json.loads(raw.document_text[0])
        assert parsed["title"] == "Quarterly Report"

    def test_empty_object_is_document(self, tmp_path):
        json_file = tmp_path / "empty_obj.json"
        json_file.write_text("{}")

        loader = JsonLoader()
        config = _json_config(json_file)
        raw = loader.load(config)

        assert raw.content_type == ContentType.DOCUMENT

    def test_empty_array_is_document(self, tmp_path):
        json_file = tmp_path / "empty_arr.json"
        json_file.write_text("[]")

        loader = JsonLoader()
        config = _json_config(json_file)
        raw = loader.load(config)

        assert raw.content_type == ContentType.DOCUMENT


class TestJsonLoaderInvalid:
    def test_invalid_json_raises(self, tmp_path):
        json_file = tmp_path / "bad.json"
        json_file.write_text("{not valid json")

        loader = JsonLoader()
        config = _json_config(json_file)

        with pytest.raises(LoaderError, match="Invalid JSON"):
            loader.load(config)

    def test_file_not_found_raises(self, tmp_path):
        loader = JsonLoader()
        config = _json_config(tmp_path / "nonexistent.json")

        with pytest.raises(LoaderError, match="File not found"):
            loader.load(config)


# ---- Registry ----


class TestRegistryGetLoader:
    def test_returns_correct_loader(self):
        registry = LoaderRegistry()
        registry.register(CsvLoader())
        registry.register(JsonLoader())

        csv_loader = registry.get_loader(SourceType.CSV)
        assert isinstance(csv_loader, CsvLoader)

        json_loader = registry.get_loader(SourceType.JSON)
        assert isinstance(json_loader, JsonLoader)

    def test_available_types(self):
        registry = LoaderRegistry()
        registry.register(CsvLoader())
        registry.register(JsonLoader())

        types = registry.available_types()
        assert "csv" in types
        assert "json" in types


class TestRegistryUnknownType:
    def test_raises_loader_error(self):
        registry = LoaderRegistry()

        with pytest.raises(LoaderError, match="No loader registered"):
            registry.get_loader(SourceType.XLSX)
