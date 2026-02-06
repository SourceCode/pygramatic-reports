"""Tests for Fluent API."""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from pygramattic_reports.api import BuiltReport, Pygramattic
from pygramattic_reports.models import DataType


class TestFluentApi(unittest.TestCase):
    def test_init(self):
        pg = Pygramattic()
        self.assertIsInstance(pg, Pygramattic)

    def test_configure(self):
        pg = Pygramattic().configure(title="My Title", author="Me")
        self.assertEqual(pg._metadata.title, "My Title")
        self.assertEqual(pg._metadata.author, "Me")

    def test_add_dataset_dataframe(self):
        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        pg = Pygramattic().add_dataset("test", df)

        self.assertIn("test", pg._datasets)
        ds = pg._datasets["test"]
        self.assertEqual(len(ds.dataframe), 2)
        # Check inferred schema
        col_a = next(c for c in ds.schema if c.name == "A")
        self.assertEqual(col_a.dtype, DataType.INTEGER)
        col_b = next(c for c in ds.schema if c.name == "B")
        self.assertEqual(col_b.dtype, DataType.STRING)

    def test_add_dataset_list(self):
        data = [{"col1": 1}, {"col1": 2}]
        pg = Pygramattic().add_dataset("test", data)
        self.assertIn("test", pg._datasets)
        self.assertEqual(len(pg._datasets["test"].dataframe), 2)

    def test_add_section(self):
        pg = Pygramattic().add_section("Intro", "Hello")
        self.assertEqual(len(pg._sections), 1)
        self.assertEqual(pg._sections[0].title, "Intro")
        self.assertEqual(pg._sections[0].type, "narrative")

    def test_add_chart(self):
        pg = Pygramattic().add_chart("My Chart", "ds1", "bar", "x", ["y"])
        self.assertEqual(len(pg._sections), 1)
        self.assertEqual(pg._sections[0].type, "chart")
        self.assertEqual(pg._sections[0].chart_type, "bar")

    @patch("pygramattic_reports.api.ApiReportBuilder")
    def test_build(self, mock_builder_cls):
        mock_builder = mock_builder_cls.return_value
        mock_builder.build_from_memory.return_value = (MagicMock(), MagicMock())

        pg = Pygramattic().configure(title="T").add_section("S1")
        result = pg.build()

        self.assertIsInstance(result, BuiltReport)
        mock_builder.build_from_memory.assert_called_once()
