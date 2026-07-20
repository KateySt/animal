from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int = field(init=False)

    def __post_init__(self) -> None:
        self.pages = (self.total + self.page_size - 1) // self.page_size if self.page_size else 0
