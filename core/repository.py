"""Repository pattern base class for database operations.

Provides common CRUD operations and transaction management utilities
to reduce boilerplate in API endpoints and service layers.
"""

from sqlalchemy.orm import Session
from typing import TypeVar, Generic, Type, Optional, List, Any
from database.models import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """Generic repository for common database operations.
    
    Attributes:
        model: SQLAlchemy model class to operate on.
        session: Database session for executing queries.
    """

    def __init__(self, model: Type[T], session: Session):
        """Initialize repository with model and session.
        
        Args:
            model: SQLAlchemy model class.
            session: Database session.
        """
        self.model = model
        self.session = session

    def create(self, obj: T) -> T:
        """Add, commit and refresh a new object.
        
        Args:
            obj: Model instance to persist.
            
        Returns:
            The persisted object with refreshed attributes.
        """
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def create_many(self, objects: List[T]) -> List[T]:
        """Add multiple objects, commit and refresh all.
        
        Args:
            objects: List of model instances to persist.
            
        Returns:
            List of persisted objects with refreshed attributes.
        """
        self.session.add_all(objects)
        self.session.commit()
        for obj in objects:
            self.session.refresh(obj)
        return objects

    def get_by_id(self, id: Any) -> Optional[T]:
        """Retrieve an object by its primary key.
        
        Args:
            id: Primary key value.
            
        Returns:
            Model instance or None if not found.
        """
        return self.session.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retrieve all objects with pagination.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            List of model instances.
        """
        return self.session.query(self.model).offset(skip).limit(limit).all()

    def update(self, obj: T) -> T:
        """Commit changes to an existing object and refresh.
        
        Args:
            obj: Model instance with modified attributes.
            
        Returns:
            The updated object with refreshed attributes.
        """
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, obj: T) -> None:
        """Delete an object and commit.
        
        Args:
            obj: Model instance to delete.
        """
        self.session.delete(obj)
        self.session.commit()

    def delete_by_id(self, id: Any) -> bool:
        """Delete an object by its primary key.
        
        Args:
            id: Primary key value.
            
        Returns:
            True if object was deleted, False if not found.
        """
        obj = self.get_by_id(id)
        if obj:
            self.delete(obj)
            return True
        return False

    def count(self) -> int:
        """Count total number of records.
        
        Returns:
            Total count of model instances.
        """
        return self.session.query(self.model).count()


def save(session: Session, obj: Base) -> Base:
    """Convenience function to add, commit and refresh an object.
    
    Args:
        session: Database session.
        obj: Model instance to persist.
        
    Returns:
        The persisted object with refreshed attributes.
    """
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def save_all(session: Session, objects: List[Base]) -> List[Base]:
    """Convenience function to add multiple objects, commit and refresh.
    
    Args:
        session: Database session.
        objects: List of model instances to persist.
        
    Returns:
        List of persisted objects with refreshed attributes.
    """
    session.add_all(objects)
    session.commit()
    for obj in objects:
        session.refresh(obj)
    return objects
