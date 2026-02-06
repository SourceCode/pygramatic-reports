"""Core data models for pygramattic-reports.

All inter-module contracts are defined here. Import models from this
package rather than from individual files.

Usage::

    from pygramattic_reports.models import Dataset, Report, ChartSpec
"""

from .base import PygramatticModel, generate_id, now_utc
from .chart_spec import ChartFormat, ChartRenderer, ChartSpec, ChartType
from .dataset import ColumnSchema, Dataset, DataType, Provenance
from .manifest import Manifest
from .raw_data import ContentType, RawData
from .report import NumberClaim, Report, ReportSection, SectionType
from .sources import (
    DatabaseSourceConfig,
    FileSourceConfig,
    GoogleSourceConfig,
    SourceConfig,
    SourceType,
)
from .template_spec import (
    ChartThemeSpec,
    ColorSpec,
    FontSpec,
    SectionSource,
    SpacingSpec,
    TemplateSectionSpec,
    TemplateSpec,
    ThemeSpec,
)
from .validation import CheckStatus, ValidationCheck, ValidationResult

__all__ = [
    "ChartFormat",
    "ChartRenderer",
    "ChartSpec",
    "ChartThemeSpec",
    "ChartType",
    "CheckStatus",
    "ColorSpec",
    "ColumnSchema",
    "ContentType",
    "DataType",
    "DatabaseSourceConfig",
    "Dataset",
    "FileSourceConfig",
    "FontSpec",
    "GoogleSourceConfig",
    "Manifest",
    "NumberClaim",
    "Provenance",
    "PygramatticModel",
    "RawData",
    "Report",
    "ReportSection",
    "SectionSource",
    "SectionType",
    "SourceConfig",
    "SourceType",
    "SpacingSpec",
    "TemplateSectionSpec",
    "TemplateSpec",
    "ThemeSpec",
    "ValidationCheck",
    "ValidationResult",
    "generate_id",
    "now_utc",
]
