"""
📊 Convergio - Database Models Package
"""

from .talent import Talent
from .user import User

try:
    from .document import Document, DocumentEmbedding
except ImportError:
    # document model might not be available in all environments
    pass

__all__ = ["Talent", "User"]