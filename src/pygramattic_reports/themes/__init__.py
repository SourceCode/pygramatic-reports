"""Theme engine for pygramattic-reports.

Load themes and translate them to format-specific styling.

Usage::

    from pygramattic_reports.themes import ThemeLoader, ThemeApplicator

    loader = ThemeLoader(themes_dir)
    theme = loader.load("corporate_blue")
    applicator = ThemeApplicator(theme)
    mpl_params = applicator.to_matplotlib_params()
"""

from .applicator import ThemeApplicator
from .loader import ThemeLoader

__all__ = ["ThemeApplicator", "ThemeLoader"]
