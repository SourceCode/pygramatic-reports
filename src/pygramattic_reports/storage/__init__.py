"""Storage manager for pygramattic-reports.

Handles the ``data/`` directory structure, dataset persistence,
manifest tracking, and file retrieval.

Usage::

    from pygramattic_reports.storage import StorageManager

    storage = StorageManager(config)
    storage.initialize()
    dataset_id = storage.save_dataset(dataset)
"""

from .manager import StorageManager

__all__ = ["StorageManager"]
