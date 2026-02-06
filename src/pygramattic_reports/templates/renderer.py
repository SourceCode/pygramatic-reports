"""Template renderer for pygramattic-reports.

Resolves Jinja2 template expressions in template sections, binding
template variables to actual data values.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from jinja2 import (
    BaseLoader,
    Environment,
    StrictUndefined,
    TemplateSyntaxError,
    Undefined,
    UndefinedError,
)

from pygramattic_reports.exceptions import TemplateError
from pygramattic_reports.logging import get_logger

if TYPE_CHECKING:
    from pygramattic_reports.models import TemplateSectionSpec, TemplateSpec

_logger = get_logger("templates.renderer")

_VALID_UNDEFINED_BEHAVIORS = frozenset({"warn", "strict", "ignore"})


class _LoggingUndefined(Undefined):
    """Jinja2 Undefined that logs warnings and renders as empty string."""

    def __str__(self) -> str:
        _logger.warning("Undefined template variable", name=self._undefined_name)
        return ""

    def __iter__(self) -> Any:  # noqa: ANN401
        return iter([])

    def __bool__(self) -> bool:
        return False


class _SilentUndefined(Undefined):
    """Jinja2 Undefined that silently renders as empty string."""

    def __str__(self) -> str:
        return ""

    def __iter__(self) -> Any:  # noqa: ANN401
        return iter([])

    def __bool__(self) -> bool:
        return False


class TemplateRenderer:
    """Resolves Jinja2 template expressions in template sections.

    This does NOT produce the final report output. It resolves
    template variables (``{{report_title}}``, ``{{dataset.name}}``) into
    concrete values. The Builder then uses these resolved sections
    to assemble the report.

    Usage::

        renderer = TemplateRenderer()
        resolved_content = renderer.render_string(
            "Revenue Report: {{ report_title }}",
            context={"report_title": "Q4 2024 Analysis"},
        )
    """

    def __init__(self, undefined_behavior: str = "warn") -> None:  # noqa: D107
        if undefined_behavior not in _VALID_UNDEFINED_BEHAVIORS:
            msg = (
                f"Invalid undefined_behavior {undefined_behavior!r}, "
                f"expected 'warn', 'strict', or 'ignore'"
            )
            raise ValueError(msg)

        self._behavior = undefined_behavior

        undefined_cls: type[Undefined] = Undefined
        if undefined_behavior == "strict":
            undefined_cls = StrictUndefined
        elif undefined_behavior == "warn":
            undefined_cls = _LoggingUndefined
        elif undefined_behavior == "ignore":
            undefined_cls = _SilentUndefined

        self._env = Environment(
            loader=BaseLoader(),
            undefined=undefined_cls,
            keep_trailing_newline=False,
            autoescape=False,  # noqa: S701  # plain text templates, not HTML
        )

        # Register standard filters
        self._env.filters["currency"] = _filter_currency
        self._env.filters["percent"] = _filter_percent
        self._env.filters["date"] = _filter_date
        self._env.filters["number"] = _filter_number

    def render_string(self, template_string: str, context: dict[str, Any]) -> str:
        """Render a single Jinja2 template string with the given context.

        Args:
            template_string: A string possibly containing ``{{ }}`` expressions.
            context: Variable bindings for rendering.

        Returns:
            Rendered string.

        Raises:
            TemplateError: If rendering fails in strict mode.
        """
        try:
            tmpl = self._env.from_string(template_string)
            return tmpl.render(context)
        except UndefinedError as exc:
            msg = f"Undefined variable in template: {exc}"
            raise TemplateError(msg) from exc
        except TemplateSyntaxError as exc:
            msg = f"Template syntax error: {exc}"
            raise TemplateError(msg) from exc

    def evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """Evaluate a Jinja2 conditional expression.

        Used for conditional section rendering.

        Args:
            condition: A Jinja2 expression that evaluates to truthy/falsy.
            context: Variable bindings for evaluation.

        Returns:
            Whether the condition is true.
        """
        try:
            expr = self._env.compile_expression(condition)
            result = expr(**context)
        except Exception:
            _logger.warning("Condition evaluation failed, treating as false", condition=condition)
            return False
        return bool(result)

    def resolve_template(
        self,
        template: TemplateSpec,
        context: dict[str, Any],
    ) -> list[TemplateSectionSpec]:
        """Resolve all template sections with the given context.

        Renders Jinja2 expressions in section content and titles,
        and filters out sections whose conditions evaluate to false.

        Args:
            template: The template specification.
            context: Variable bindings (report metadata, dataset info, etc.).

        Returns:
            List of resolved section specs ready for the Builder.
        """
        resolved: list[TemplateSectionSpec] = []

        for section in template.sections:
            # Check condition
            if section.condition and not self.evaluate_condition(section.condition, context):
                _logger.debug(
                    "Section filtered by condition",
                    type=section.type,
                    condition=section.condition,
                )
                continue

            # Render fields that may contain Jinja2 expressions
            updates: dict[str, Any] = {}

            if section.content is not None:
                updates["content"] = self.render_string(section.content, context)

            if section.title is not None:
                updates["title"] = self.render_string(section.title, context)

            if section.ai_prompt is not None:
                updates["ai_prompt"] = self.render_string(section.ai_prompt, context)

            if section.dataset is not None:
                updates["dataset"] = self.render_string(section.dataset, context)

            if updates:
                resolved.append(section.model_copy(update=updates))
            else:
                resolved.append(section)

        return resolved


# --- Filters ---


def _filter_currency(value: float | int | str, symbol: str = "$") -> str:
    """Format value as currency."""
    try:
        val = float(value)
        return f"{symbol}{val:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def _filter_percent(value: float | int | str, decimals: int = 1) -> str:
    """Format value as percentage."""
    try:
        val = float(value)
        # Assuming value is 0.5 for 50%
        return f"{val:.{decimals}%}"
    except (ValueError, TypeError):
        return str(value)


def _filter_date(value: Any, format: str = "%Y-%m-%d") -> str:
    """Format date string or object."""
    if isinstance(value, str):
        try:
            # Simple ISO parse attempt
            dt_val = datetime.fromisoformat(value)
            return dt_val.strftime(format)
        except ValueError:
            return value

    if isinstance(value, datetime):
        return value.strftime(format)
    return str(value)


def _filter_number(value: float | int | str, decimals: int = 2) -> str:
    """Format number with thousands separator."""
    try:
        val = float(value)
        return f"{val:,.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)
