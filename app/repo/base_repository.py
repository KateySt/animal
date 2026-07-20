from typing import Any, Generic, TypeVar, Callable
from uuid import UUID

from sqlalchemy import Select, asc, desc, func, select, ColumnElement, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import QueryableAttribute

from app.db.models.base import Base
from app.repo.enums import FilterOptions
from app.schemas import PaginatedResult

ModelT = TypeVar("ModelT", bound=Base)

FilterStrategy = Callable[[QueryableAttribute, Any], ColumnElement]

_STRATEGIES: dict[FilterOptions, FilterStrategy] = {
    FilterOptions.EQ: lambda col, val: col == val,
    FilterOptions.GT: lambda col, val: col > val,
    FilterOptions.GTE: lambda col, val: col >= val,
    FilterOptions.LT: lambda col, val: col < val,
    FilterOptions.LTE: lambda col, val: col <= val,
    FilterOptions.LIKE: lambda col, val: col.ilike(f"%{val}%"),
    FilterOptions.IN: lambda col, val: col.in_(val),
    FilterOptions.IS_NULL: lambda col, val: col.is_(None) if val else col.is_not(None),
}


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @classmethod
    def _column_allowlist(cls) -> frozenset[str]:
        return frozenset(inspect(cls.model).mapper.column_attrs.keys())

    def _base_query(self) -> Select:
        return select(self.model)

    def _apply_filters(self, query: Select, filters: dict[str, Any]) -> Select:
        allowlist = self._column_allowlist()
        for filter_key, filter_value in filters.items():
            field_name, operator = (
                filter_key.rsplit("__", 1) if "__" in filter_key else (filter_key, FilterOptions.EQ)
            )

            if field_name not in allowlist:
                continue

            column = getattr(self.model, field_name)

            build_condition = _STRATEGIES.get(FilterOptions(operator)) if operator in FilterOptions._value2member_map_ else None
            if build_condition is None:
                continue

            sql_condition = build_condition(column, filter_value)
            query = query.where(sql_condition)

        return query

    def _apply_order(self, query: Select, order_by: list[str]) -> Select:
        allowlist = self._column_allowlist()
        for order_field in order_by:
            if order_field.startswith("-"):
                field_name = order_field[1:]
                if field_name in allowlist:
                    query = query.order_by(desc(getattr(self.model, field_name)))
            else:
                if order_field in allowlist:
                    query = query.order_by(asc(getattr(self.model, order_field)))
        return query

    async def get_by_id(self, id: UUID) -> ModelT | None:
        result = await self.session.execute(
            self._base_query().where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        filters: dict[str, Any] | None = None,
        order_by: list[str] | None = None,
    ) -> list[ModelT]:
        query = self._base_query()
        if filters:
            query = self._apply_filters(query, filters)
        if order_by:
            query = self._apply_order(query, order_by)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: dict[str, Any] | None = None,
        order_by: list[str] | None = None,
    ) -> PaginatedResult[ModelT]:
        query = self._base_query()
        if filters:
            query = self._apply_filters(query, filters)

        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        if order_by:
            query = self._apply_order(query, order_by)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        return PaginatedResult(items=items, total=total, page=page, page_size=page_size)

    async def create(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: UUID, data: dict[str, Any]) -> ModelT | None:
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: UUID) -> bool:
        instance = await self.get_by_id(id)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
