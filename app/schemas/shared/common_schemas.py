import math
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response envelope for returning lists of items.
    """

    total: int
    page: int
    limit: int
    total_pages: int
    items: list[T]

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, limit: int
    ) -> "PaginatedResponse[T]":
        """
        Factory method that calculates total_pages automatically in 1 single place.
        """
        total_pages = math.ceil(total / limit) if (total > 0 and limit > 0) else 1
        return cls(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=items,
        )


class ActionSuccessResponse(BaseModel):
    """
    Generic status success response payload used across action and mutation endpoints.
    """

    status: str = "success"
