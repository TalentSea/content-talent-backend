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


class ActionSuccessResponse(BaseModel):
    """
    Generic status success response payload used across action and mutation endpoints.
    """

    status: str = "success"
