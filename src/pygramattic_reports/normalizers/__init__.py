"""Data normalizers for converting raw data to typed Datasets.

Usage::

    from pygramattic_reports.normalizers import TabularNormalizer, DocumentNormalizer

    normalizer = TabularNormalizer()
    dataset = normalizer.normalize(raw_data)
"""

from .document import DocumentNormalizer
from .tabular import TabularNormalizer

__all__ = ["DocumentNormalizer", "TabularNormalizer"]
