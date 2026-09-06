"""
StockSense AI — Base Async Repository
Provides generic CRUD, pagination, and transaction safety.
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from pydantic import BaseModel
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class PaginationResult(BaseModel, Generic[ModelType]):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Fetch single entity by primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """List entities with offset/limit pagination."""
        query = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        """Count total entities."""
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, **kwargs) -> ModelType:
        """Instantiate and persist a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def bulk_create(self, objects: List[Dict[str, Any]]) -> List[ModelType]:
        """Bulk insert instances."""
        instances = [self.model(**obj) for obj in objects]
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        """Update fields on an existing instance."""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Physical delete."""
        await self.session.delete(instance)
        await self.session.flush()
