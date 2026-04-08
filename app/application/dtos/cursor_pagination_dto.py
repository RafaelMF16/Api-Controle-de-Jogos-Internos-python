from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(default_factory=list)
    page_size: int = Field(default=10, ge=1)
    next_cursor: str | None = None
    has_next: bool = False
