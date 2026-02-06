"""Core data models for pygramattic-reports.

All inter-module contracts are defined here. Import models from this
package rather than from individual files.

Usage::

    from pygramattic_reports.models import Dataset, Report, ChartSpec
"""

from .base import PygramatticModel, generate_id, now_utc
from .chart_spec import (
    AnnotationSpec,
    AxisSpec,
    ChartFormat,
    ChartRenderer,
    ChartSpec,
    ChartType,
    DataLabelSpec,
    LegendSpec,
)
from .dataset import ColumnSchema, Dataset, DataType, Provenance
from .manifest import Manifest
from .raw_data import ContentType, RawData
from .report import (
    CoverPageSpec,
    DocumentMetadata,
    NumberClaim,
    PageLayout,
    Report,
    ReportSection,
    RunningElement,
    SectionType,
)
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
    "AnnotationSpec",
    "AxisSpec",
    "ChartFormat",
    "ChartRenderer",
    "ChartSpec",
    "ChartThemeSpec",
    "ChartType",
    "CheckStatus",
    "ColorSpec",
    "ColumnSchema",
    "ContentType",
    "CoverPageSpec",
    "DataLabelSpec",
    "DataType",
    "DatabaseSourceConfig",
    "Dataset",
    "DocumentMetadata",
    "FileSourceConfig",
    "FontSpec",
    "GoogleSourceConfig",
    "LegendSpec",
    "Manifest",
    "NumberClaim",
    "PageLayout",
    "Provenance",
    "PygramatticModel",
    "RawData",
    "Report",
    "ReportSection",
    "RunningElement",
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
