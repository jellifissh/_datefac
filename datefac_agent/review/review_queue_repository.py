"""Disabled review_queue repository interface skeleton.

This module defines the future repository boundary shape for review_queue
persistence. It intentionally performs no I/O, opens no database connection,
creates no schema or migration, and has no production hook.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Protocol, Sequence

REPOSITORY_INTERFACE_VERSION = "r7bu_review_queue_repository_disabled_skeleton_v1"
DISABLED_STATUS = "DISABLED"
DISABLED_REASON = "review_queue_repository_disabled_by_default_no_db_connection"

READINESS_GATES_CLOSED: dict[str, bool] = {
    "client_ready": False,
    "production_ready": False,
    "formal_client_export_allowed": False,
    "demo_export_only": True,
}


class ReviewQueueRepositoryError(ValueError):
    """Base error for the disabled review_queue repository skeleton."""


class ReviewQueueRepositoryDisabledError(ReviewQueueRepositoryError):
    """Raised when repository access is attempted while disabled."""


@dataclass(frozen=True, slots=True)
class ReviewQueueRepositoryWriteReceipt:
    """Non-persisting receipt shape for the disabled repository boundary."""

    repository_status: str = DISABLED_STATUS
    persistence_status: str = "NOT_PERSISTED"
    disabled_reason: str = DISABLED_REASON
    repository_interface_version: str = REPOSITORY_INTERFACE_VERSION
    clean_data_write_count: int = 0
    delivery_write_count: int = 0
    filesystem_write_count: int = 0
    database_write_count: int = 0
    network_call_count: int = 0
    export_write_count: int = 0

    def __post_init__(self) -> None:
        if self.disabled_reason != DISABLED_REASON:
            raise ReviewQueueRepositoryDisabledError("custom disabled reasons are not accepted")

    def as_dict(self) -> dict[str, Any]:
        """Return a metadata-only, non-persisting receipt dictionary."""

        return {
            "repository_status": self.repository_status,
            "persistence_status": self.persistence_status,
            "disabled_reason": self.disabled_reason,
            "repository_interface_version": self.repository_interface_version,
            "writes_database": False,
            "writes_filesystem": False,
            "writes_network": False,
            "writes_review_queue": False,
            "writes_clean_data": False,
            "writes_delivery": False,
            "writes_export": False,
            "clean_data_write_count": self.clean_data_write_count,
            "delivery_write_count": self.delivery_write_count,
            "filesystem_write_count": self.filesystem_write_count,
            "database_write_count": self.database_write_count,
            "network_call_count": self.network_call_count,
            "export_write_count": self.export_write_count,
            "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        }


class ReviewQueueRepositoryPort(Protocol):
    """Future repository boundary shape without an implementation."""

    def write_batch(
        self,
        candidates: Sequence[dict[str, Any]],
        *,
        run_id: str | None = None,
    ) -> ReviewQueueRepositoryWriteReceipt:
        """Persist a review_queue candidate batch in a future implementation."""

    def get_by_review_item_id(self, review_item_id: str) -> dict[str, Any] | None:
        """Return one review_queue item in a future implementation."""

    def list_by_run_id(self, run_id: str) -> list[dict[str, Any]]:
        """Return review_queue items for a run in a future implementation."""


@dataclass(frozen=True, slots=True)
class DisabledReviewQueueRepository:
    """Disabled repository skeleton that fails closed for every operation."""

    disabled_reason: str = DISABLED_REASON
    repository_interface_version: str = REPOSITORY_INTERFACE_VERSION

    def __post_init__(self) -> None:
        if self.disabled_reason != DISABLED_REASON:
            raise ReviewQueueRepositoryDisabledError("custom disabled reasons are not accepted")

    def write_batch(
        self,
        candidates: Sequence[dict[str, Any]],
        *,
        run_id: str | None = None,
    ) -> ReviewQueueRepositoryWriteReceipt:
        """Fail closed; no candidates are persisted or retained."""

        _raise_disabled("write_batch")

    def get_by_review_item_id(self, review_item_id: str) -> dict[str, Any] | None:
        """Fail closed; no repository state is available."""

        _raise_disabled("get_by_review_item_id")

    def list_by_run_id(self, run_id: str) -> list[dict[str, Any]]:
        """Fail closed; no repository state is available."""

        _raise_disabled("list_by_run_id")

    def disabled_receipt(self) -> ReviewQueueRepositoryWriteReceipt:
        """Return a metadata-only receipt that explicitly says no write happened."""

        return ReviewQueueRepositoryWriteReceipt(disabled_reason=self.disabled_reason)


def create_disabled_review_queue_repository(**repository_config: Any) -> DisabledReviewQueueRepository:
    """Create the only currently available repository: disabled and no-DB."""

    if repository_config:
        _raise_config_rejected()
    return DisabledReviewQueueRepository()


def _raise_disabled(operation: str) -> None:
    raise ReviewQueueRepositoryDisabledError(
        "review_queue repository is disabled by default; "
        f"{operation} is not available; no persistence occurred"
    )


def _raise_config_rejected() -> None:
    raise ReviewQueueRepositoryDisabledError(
        "review_queue repository is disabled by default; repository configuration is not accepted"
    )


__all__ = [
    "DISABLED_REASON",
    "DISABLED_STATUS",
    "READINESS_GATES_CLOSED",
    "REPOSITORY_INTERFACE_VERSION",
    "DisabledReviewQueueRepository",
    "ReviewQueueRepositoryDisabledError",
    "ReviewQueueRepositoryError",
    "ReviewQueueRepositoryPort",
    "ReviewQueueRepositoryWriteReceipt",
    "create_disabled_review_queue_repository",
]
