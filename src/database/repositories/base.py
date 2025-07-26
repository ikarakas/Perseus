# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Base repository class for database operations
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, or_, func

from ..connection import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository providing common CRUD operations"""
    
    def __init__(self, model: Type[ModelType], session: Session):
        self.model = model
        self.session = session
    
    def create(self, **kwargs) -> ModelType:
        """Create a new entity"""
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            self.session.flush()
            return instance
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Integrity error creating {self.model.__name__}: {str(e)}")
    
    def get(self, id: UUID) -> Optional[ModelType]:
        """Get entity by ID"""
        return self.session.query(self.model).filter(self.model.id == id).first()
    
    def get_by(self, **kwargs) -> Optional[ModelType]:
        """Get entity by specific field(s)"""
        return self.session.query(self.model).filter_by(**kwargs).first()
    
    def get_all(self, limit: int = None, offset: int = None) -> List[ModelType]:
        """Get all entities with optional pagination"""
        query = self.session.query(self.model)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def filter(self, limit: int = None, offset: int = None, **kwargs) -> List[ModelType]:
        """Filter entities by field values"""
        query = self.session.query(self.model).filter_by(**kwargs)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        """Update entity by ID"""
        instance = self.get(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            # Update the updated_at timestamp if it exists
            if hasattr(instance, 'updated_at'):
                instance.updated_at = datetime.utcnow()
            
            self.session.flush()
        return instance
    
    def delete(self, id: UUID) -> bool:
        """Delete entity by ID"""
        instance = self.get(id)
        if instance:
            self.session.delete(instance)
            self.session.flush()
            return True
        return False
    
    def count(self, **kwargs) -> int:
        """Count entities matching criteria"""
        return self.session.query(self.model).filter_by(**kwargs).count()
    
    def exists(self, **kwargs) -> bool:
        """Check if entity exists"""
        return self.session.query(
            self.session.query(self.model).filter_by(**kwargs).exists()
        ).scalar()
    
    def bulk_create(self, entities: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple entities efficiently"""
        instances = []
        for entity_data in entities:
            instance = self.model(**entity_data)
            instances.append(instance)
            self.session.add(instance)
        
        self.session.flush()
        return instances
    
    def commit(self):
        """Commit the current transaction"""
        self.session.commit()
    
    def rollback(self):
        """Rollback the current transaction"""
        self.session.rollback()