"""Unit tests for the exception hierarchy."""

import pytest

from pygramattic_reports.exceptions import (
    AIError,
    BuildError,
    ChartError,
    ConfigError,
    ConversionError,
    ErrorSeverity,
    FeedbackError,
    LoaderError,
    NormalizationError,
    OutputError,
    PygramatticError,
    StorageError,
    TemplateError,
    ThemeError,
    ValidationError,
)

# ---- ErrorSeverity ----


class TestErrorSeverity:
    def test_severity_values(self):
        assert ErrorSeverity.FATAL == "fatal"
        assert ErrorSeverity.RECOVERABLE == "recoverable"
        assert ErrorSeverity.RETRIABLE == "retriable"

    def test_severity_is_str(self):
        assert isinstance(ErrorSeverity.FATAL, str)


# ---- PygramatticError Base ----


class TestPygramatticError:
    def test_message_accessible(self):
        exc = PygramatticError("something broke")
        assert exc.message == "something broke"
        assert str(exc) == "something broke"

    def test_defaults(self):
        exc = PygramatticError("oops")
        assert exc.error_code == "UNKNOWN"
        assert exc.severity == ErrorSeverity.FATAL
        assert exc.context == {}

    def test_custom_fields(self):
        exc = PygramatticError(
            "bad",
            error_code="CUSTOM",
            severity=ErrorSeverity.RECOVERABLE,
            context={"key": "val"},
        )
        assert exc.error_code == "CUSTOM"
        assert exc.severity == ErrorSeverity.RECOVERABLE
        assert exc.context == {"key": "val"}

    def test_is_exception(self):
        with pytest.raises(PygramatticError):
            raise PygramatticError("test")


# ---- Inheritance ----


ALL_EXCEPTIONS = [
    ConfigError,
    LoaderError,
    NormalizationError,
    StorageError,
    ConversionError,
    TemplateError,
    ThemeError,
    ChartError,
    BuildError,
    ValidationError,
    AIError,
    FeedbackError,
    OutputError,
]


class TestInheritance:
    @pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
    def test_is_subclass_of_pygramattic_error(self, exc_cls):
        assert issubclass(exc_cls, PygramatticError)

    @pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
    def test_catchable_as_base(self, exc_cls):
        with pytest.raises(PygramatticError):
            raise exc_cls("test")

    @pytest.mark.parametrize("exc_cls", ALL_EXCEPTIONS)
    def test_catchable_as_exception(self, exc_cls):
        with pytest.raises(Exception, match="test"):
            raise exc_cls("test")


# ---- Default Error Codes and Severities ----


class TestDefaultErrorCodes:
    def test_config_error(self):
        exc = ConfigError("bad config")
        assert exc.error_code == "CONFIG_ERROR"
        assert exc.severity == ErrorSeverity.FATAL

    def test_loader_error(self):
        exc = LoaderError("load fail")
        assert exc.error_code == "LOADER_ERROR"
        assert exc.severity == ErrorSeverity.FATAL

    def test_normalization_error(self):
        exc = NormalizationError("norm fail")
        assert exc.error_code == "NORMALIZATION_ERROR"

    def test_storage_error(self):
        exc = StorageError("disk full")
        assert exc.error_code == "STORAGE_ERROR"

    def test_conversion_error(self):
        exc = ConversionError("bad type")
        assert exc.error_code == "CONVERSION_ERROR"

    def test_template_error(self):
        exc = TemplateError("render fail")
        assert exc.error_code == "TEMPLATE_ERROR"

    def test_theme_error(self):
        exc = ThemeError("theme missing")
        assert exc.error_code == "THEME_ERROR"

    def test_chart_error_is_recoverable(self):
        exc = ChartError("render fail")
        assert exc.error_code == "CHART_ERROR"
        assert exc.severity == ErrorSeverity.RECOVERABLE

    def test_build_error(self):
        exc = BuildError("build fail")
        assert exc.error_code == "BUILD_ERROR"

    def test_validation_error(self):
        exc = ValidationError("check fail")
        assert exc.error_code == "VALIDATION_ERROR"

    def test_ai_error_is_retriable(self):
        exc = AIError("timeout")
        assert exc.error_code == "AI_ERROR"
        assert exc.severity == ErrorSeverity.RETRIABLE

    def test_feedback_error(self):
        exc = FeedbackError("parse fail")
        assert exc.error_code == "FEEDBACK_ERROR"

    def test_output_error(self):
        exc = OutputError("write fail")
        assert exc.error_code == "OUTPUT_ERROR"


# ---- Context Merging ----


class TestContextMerging:
    def test_loader_error_captures_source_info(self):
        exc = LoaderError("fail", source_type="csv", source_path="/data/x.csv")
        assert exc.context["source_type"] == "csv"
        assert exc.context["source_path"] == "/data/x.csv"

    def test_loader_error_merges_extra_context(self):
        exc = LoaderError("fail", source_type="csv", context={"extra": "info"})
        assert exc.context["source_type"] == "csv"
        assert exc.context["extra"] == "info"

    def test_template_error_captures_name(self):
        exc = TemplateError("fail", template_name="monthly.jinja2")
        assert exc.context["template_name"] == "monthly.jinja2"

    def test_chart_error_captures_type(self):
        exc = ChartError("fail", chart_type="bar")
        assert exc.context["chart_type"] == "bar"

    def test_output_error_captures_format(self):
        exc = OutputError("fail", output_format="docx")
        assert exc.context["output_format"] == "docx"

    def test_severity_override_via_kwargs(self):
        exc = ConfigError("bad", severity=ErrorSeverity.RECOVERABLE)
        assert exc.severity == ErrorSeverity.RECOVERABLE

    def test_simple_exception_passes_context(self):
        exc = StorageError("fail", context={"path": "/data"})
        assert exc.context == {"path": "/data"}
