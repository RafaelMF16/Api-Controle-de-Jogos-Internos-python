from math import ceil
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int


def build_paginated_response(items: Sequence[T], page: int, page_size: int) -> PaginatedResponse[T]:
    total = len(items)
    total_pages = max(1, ceil(total / page_size)) if page_size else 1
    current_page = min(max(1, page), total_pages)
    start = (current_page - 1) * page_size
    end = start + page_size

    return PaginatedResponse(
        items=list(items[start:end]),
        page=current_page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )
