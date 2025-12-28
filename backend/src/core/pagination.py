"""
Cursor-based Pagination for Scalable APIs
Implements keyset pagination for efficient large dataset navigation
"""

from typing import Dict, Any, List, Optional, Tuple, TypeVar, Generic
import base64
import json
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    limit: int = Field(default=50, ge=1, le=200)
    cursor: Optional[str] = None
    direction: str = Field(default="next", pattern="^(next|prev)$")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response structure"""
    items: List[T]
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_more: bool = False
    total_count: Optional[int] = None


class CursorPaginator:
    """
    Cursor-based pagination implementation.
    More efficient than offset-based for large datasets.
    """
    
    @staticmethod
    def encode_cursor(data: Dict[str, Any]) -> str:
        """
        Encode cursor data to base64 string.
        
        Args:
            data: Dictionary with cursor data
            
        Returns:
            Base64 encoded cursor string
        """
        try:
            json_str = json.dumps(data, default=str)
            return base64.b64encode(json_str.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to encode cursor: {e}")
            return ""
    
    @staticmethod
    def decode_cursor(cursor: str) -> Dict[str, Any]:
        """
        Decode cursor string to dictionary.
        
        Args:
            cursor: Base64 encoded cursor
            
        Returns:
            Decoded cursor data
        """
        try:
            if not cursor:
                return {}
            json_str = base64.b64decode(cursor.encode()).decode()
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to decode cursor: {e}")
            return {}
    
    @staticmethod
    def create_cursor_from_item(
        item: Dict[str, Any],
        key_fields: List[str]
    ) -> str:
        """
        Create cursor from an item using specified key fields.
        
        Args:
            item: Item to create cursor from
            key_fields: Fields to include in cursor
            
        Returns:
            Encoded cursor string
        """
        cursor_data = {
            field: item.get(field)
            for field in key_fields
            if field in item
        }
        return CursorPaginator.encode_cursor(cursor_data)
    
    @staticmethod
    def build_where_clause(
        cursor_data: Dict[str, Any],
        direction: str = "next",
        order_field: str = "id"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build SQL WHERE clause for cursor-based pagination.
        
        Args:
            cursor_data: Decoded cursor data
            direction: Pagination direction (next/prev)
            order_field: Field to order by
            
        Returns:
            Tuple of (where_clause, params)
        """
        if not cursor_data:
            return "", {}
        
        if order_field not in cursor_data:
            return "", {}
        
        cursor_value = cursor_data[order_field]
        
        if direction == "next":
            where_clause = f"WHERE {order_field} > :cursor_value"
        else:
            where_clause = f"WHERE {order_field} < :cursor_value"
        
        params = {"cursor_value": cursor_value}
        
        # Add compound cursor support for multiple fields
        compound_fields = [f for f in cursor_data.keys() if f != order_field]
        if compound_fields:
            for field in compound_fields:
                where_clause += f" AND {field} = :{field}"
                params[field] = cursor_data[field]
        
        return where_clause, params
    
    @staticmethod
    def paginate_query(
        query: str,
        params: Dict[str, Any],
        pagination: PaginationParams,
        order_field: str = "id",
        order_desc: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply pagination to a SQL query.
        
        Args:
            query: Base SQL query
            params: Query parameters
            pagination: Pagination parameters
            order_field: Field to order by
            order_desc: Whether to order descending
            
        Returns:
            Tuple of (paginated_query, updated_params)
        """
        # Decode cursor if provided
        cursor_data = {}
        if pagination.cursor:
            cursor_data = CursorPaginator.decode_cursor(pagination.cursor)
        
        # Build WHERE clause for cursor
        where_clause, cursor_params = CursorPaginator.build_where_clause(
            cursor_data,
            pagination.direction,
            order_field
        )
        
        # Merge parameters
        params.update(cursor_params)
        
        # Add WHERE clause to query
        if where_clause:
            # Check if query already has WHERE
            if "WHERE" in query.upper():
                query = query.replace("WHERE", f"{where_clause} AND", 1)
            else:
                # Find insertion point (before ORDER BY if exists)
                if "ORDER BY" in query.upper():
                    parts = query.upper().split("ORDER BY")
                    query = f"{parts[0]} {where_clause} ORDER BY {parts[1]}"
                else:
                    query = f"{query} {where_clause}"
        
        # Add ORDER BY if not present
        if "ORDER BY" not in query.upper():
            order_dir = "DESC" if order_desc else "ASC"
            if pagination.direction == "prev":
                # Reverse order for previous page
                order_dir = "ASC" if order_desc else "DESC"
            query = f"{query} ORDER BY {order_field} {order_dir}"
        
        # Add LIMIT
        query = f"{query} LIMIT :limit"
        params["limit"] = pagination.limit + 1  # Fetch one extra to check has_more
        
        return query, params
    
    @staticmethod
    def create_response(
        items: List[Dict[str, Any]],
        pagination: PaginationParams,
        key_fields: List[str],
        total_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create paginated response with cursors.
        
        Args:
            items: Result items
            pagination: Pagination parameters
            key_fields: Fields for cursor creation
            total_count: Optional total count
            
        Returns:
            Paginated response dictionary
        """
        has_more = len(items) > pagination.limit
        
        # Remove extra item if fetched
        if has_more:
            items = items[:pagination.limit]
        
        # Create cursors
        next_cursor = None
        prev_cursor = None
        
        if items:
            if has_more or pagination.cursor:
                # Create next cursor from last item
                next_cursor = CursorPaginator.create_cursor_from_item(
                    items[-1],
                    key_fields
                )
            
            if pagination.cursor:
                # Create prev cursor from first item
                prev_cursor = CursorPaginator.create_cursor_from_item(
                    items[0],
                    key_fields
                )
        
        return {
            "items": items,
            "next_cursor": next_cursor,
            "prev_cursor": prev_cursor,
            "has_more": has_more,
            "total_count": total_count
        }


class OffsetPaginator:
    """
    Traditional offset-based pagination.
    Less efficient but simpler for small datasets.
    """
    
    @staticmethod
    def paginate_query(
        query: str,
        params: Dict[str, Any],
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Apply offset pagination to query.
        
        Args:
            query: Base SQL query
            params: Query parameters
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Tuple of (paginated_query, updated_params)
        """
        offset = (page - 1) * page_size
        
        query = f"{query} LIMIT :limit OFFSET :offset"
        params["limit"] = page_size
        params["offset"] = offset
        
        return query, params
    
    @staticmethod
    def create_response(
        items: List[Dict[str, Any]],
        page: int,
        page_size: int,
        total_count: int
    ) -> Dict[str, Any]:
        """
        Create offset-based paginated response.
        
        Args:
            items: Result items
            page: Current page
            page_size: Items per page
            total_count: Total items count
            
        Returns:
            Paginated response dictionary
        """
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }


# Pagination utilities for common use cases
def paginate_list(
    items: List[T],
    limit: int = 50,
    cursor: Optional[str] = None
) -> PaginatedResponse[T]:
    """
    Paginate an in-memory list.
    
    Args:
        items: List to paginate
        limit: Items per page
        cursor: Optional cursor
        
    Returns:
        Paginated response
    """
    start_idx = 0
    
    if cursor:
        cursor_data = CursorPaginator.decode_cursor(cursor)
        start_idx = cursor_data.get("index", 0)
    
    end_idx = start_idx + limit
    page_items = items[start_idx:end_idx]
    
    has_more = end_idx < len(items)
    
    next_cursor = None
    if has_more:
        next_cursor = CursorPaginator.encode_cursor({"index": end_idx})
    
    prev_cursor = None
    if start_idx > 0:
        prev_idx = max(0, start_idx - limit)
        prev_cursor = CursorPaginator.encode_cursor({"index": prev_idx})
    
    return PaginatedResponse(
        items=page_items,
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
        has_more=has_more,
        total_count=len(items)
    )