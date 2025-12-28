"""
👤 Convergio - User Model (Compatibility Wrapper)
Compatibility wrapper around Talent model for backward compatibility
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

# Import the actual model
from .talent import Talent


class User:
    """User compatibility wrapper around Talent model.

    Tests construct User directly with kwargs; support that by creating an
    underlying Talent instance when needed.
    """
    
    def __init__(self, talent: Optional[Talent] = None, **kwargs):
        if talent is None:
            # Map username/full_name to Talent fields
            username = kwargs.pop("username", None)
            email = kwargs.get("email")
            full_name = kwargs.pop("full_name", None)
            first_name = None
            last_name = None
            if full_name:
                parts = str(full_name).split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else None
            elif username and not full_name:
                first_name = username
            talent_kwargs = {
                "email": email or (f"{username}@example.com" if username else None),
                "first_name": first_name,
                "last_name": last_name,
            }
            talent = Talent(**{k: v for k, v in talent_kwargs.items() if v is not None})
        self.talent = talent
    
    @property
    def id(self) -> int:
        return self.talent.id
    
    @property
    def username(self) -> str:
        return self.talent.username
    
    @property
    def email(self) -> str:
        return self.talent.email
    
    @property
    def full_name(self) -> str:
        return self.talent.full_name
    
    @property
    def first_name(self) -> Optional[str]:
        return self.talent.first_name
    
    @property
    def last_name(self) -> Optional[str]:
        return self.talent.last_name
    
    @property
    def is_admin(self) -> Optional[bool]:
        return self.talent.is_admin
    
    @property
    def is_active(self) -> bool:
        return self.talent.is_active
    
    @property
    def created_at(self):
        return self.talent.created_at
    
    @property
    def updated_at(self):
        return self.talent.updated_at

    def __str__(self) -> str:
        return f"User(username={self.username}, email={self.email})"
    
    @classmethod
    async def get_all(
        cls, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List["User"]:
        """Get all users (wrapped talents)"""
        
        talents = await Talent.get_all(db, skip, limit, is_active)
        return [cls(talent) for talent in talents]
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, user_id: int) -> Optional["User"]:
        """Get user by ID"""
        
        talent = await Talent.get_by_id(db, user_id)
        return cls(talent) if talent else None
    
    @classmethod
    async def get_by_username(cls, db: AsyncSession, username: str) -> Optional["User"]:
        """Get user by username"""
        
        talent = await Talent.get_by_username(db, username)
        return cls(talent) if talent else None
    
    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> Optional["User"]:
        """Get user by email"""
        
        talent = await Talent.get_by_email(db, email)
        return cls(talent) if talent else None
    
    @classmethod
    async def get_total_count(cls, db: AsyncSession) -> int:
        """Get total count of all users"""
        return await Talent.get_total_count(db)
    
    @classmethod 
    async def get_active_count(cls, db: AsyncSession, since_date=None) -> int:
        """Get count of active users"""
        return await Talent.get_active_count(db, since_date)