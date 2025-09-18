"""
Custom Fields System - Dynamic data model customization
Allows extending any entity with custom fields
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, Float,
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    SELECT = "select"
    MULTISELECT = "multiselect"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    FILE = "file"
    REFERENCE = "reference"  # Reference to another entity
    JSON = "json"
    RICH_TEXT = "rich_text"
    COLOR = "color"
    RATING = "rating"


class EntityType(str, Enum):
    PROJECT = "project"
    TASK = "task"
    USER = "user"
    CLIENT = "client"
    WORKFLOW = "workflow"
    AGENT = "agent"
    CONVERSATION = "conversation"


class CustomFieldDefinition(Base):
    """Defines a custom field that can be added to entities"""
    __tablename__ = 'custom_field_definitions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Field metadata
    name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text)
    field_type = Column(SQLEnum(FieldType), nullable=False)
    entity_type = Column(SQLEnum(EntityType), nullable=False)
    
    # Field configuration
    is_required = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    is_searchable = Column(Boolean, default=True)
    is_visible = Column(Boolean, default=True)
    is_editable = Column(Boolean, default=True)
    
    # Display configuration
    display_order = Column(Integer, default=0)
    group_name = Column(String(100))
    placeholder = Column(String(200))
    help_text = Column(Text)
    icon = Column(String(50))
    
    # Validation rules
    validation_rules = Column(JSON, default=dict)
    # Examples:
    # {
    #   "min": 0,
    #   "max": 100,
    #   "pattern": "^[A-Z][0-9]+$",
    #   "min_length": 3,
    #   "max_length": 50,
    #   "allowed_values": ["option1", "option2"],
    #   "custom_validator": "validate_email_domain"
    # }
    
    # Default value
    default_value = Column(JSON)
    
    # Options for select/multiselect fields
    options = Column(JSON, default=list)
    # Format: [{"value": "val1", "label": "Label 1", "color": "#FF0000"}]
    
    # Reference configuration (for reference fields)
    reference_entity = Column(String(50))
    reference_field = Column(String(50))
    
    # Computed field configuration
    is_computed = Column(Boolean, default=False)
    compute_formula = Column(Text)  # Python expression or function name
    
    # Permissions
    required_role = Column(String(50))  # Role required to view/edit
    
    # Metadata
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    values = relationship("CustomFieldValue", back_populates="field_definition", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('entity_type', 'name', name='uq_entity_field_name'),
        Index('idx_field_entity_type', 'entity_type'),
        Index('idx_field_searchable', 'is_searchable'),
    )
    
    def validate_value(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate a value against field rules"""
        if self.is_required and value in [None, "", []]:
            return False, f"{self.label} is required"
        
        if value is None:
            return True, None
        
        rules = self.validation_rules or {}
        
        # Type-specific validation
        if self.field_type == FieldType.TEXT:
            if not isinstance(value, str):
                return False, f"{self.label} must be text"
            
            if "min_length" in rules and len(value) < rules["min_length"]:
                return False, f"{self.label} must be at least {rules['min_length']} characters"
            
            if "max_length" in rules and len(value) > rules["max_length"]:
                return False, f"{self.label} must be at most {rules['max_length']} characters"
            
            if "pattern" in rules:
                import re
                if not re.match(rules["pattern"], value):
                    return False, f"{self.label} format is invalid"
        
        elif self.field_type == FieldType.NUMBER:
            try:
                num_value = float(value)
            except (TypeError, ValueError):
                return False, f"{self.label} must be a number"
            
            if "min" in rules and num_value < rules["min"]:
                return False, f"{self.label} must be at least {rules['min']}"
            
            if "max" in rules and num_value > rules["max"]:
                return False, f"{self.label} must be at most {rules['max']}"
        
        elif self.field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                return False, f"{self.label} must be true or false"
        
        elif self.field_type in [FieldType.SELECT, FieldType.MULTISELECT]:
            allowed_values = [opt["value"] for opt in self.options] if self.options else []
            
            if self.field_type == FieldType.SELECT:
                if value not in allowed_values:
                    return False, f"{self.label} must be one of the allowed values"
            else:  # MULTISELECT
                if not isinstance(value, list):
                    return False, f"{self.label} must be a list"
                
                for v in value:
                    if v not in allowed_values:
                        return False, f"{v} is not an allowed value for {self.label}"
        
        elif self.field_type == FieldType.EMAIL:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                return False, f"{self.label} must be a valid email address"
        
        elif self.field_type == FieldType.URL:
            import re
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, value):
                return False, f"{self.label} must be a valid URL"
        
        elif self.field_type == FieldType.PHONE:
            import re
            phone_pattern = r'^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$'
            if not re.match(phone_pattern, value):
                return False, f"{self.label} must be a valid phone number"
        
        elif self.field_type in [FieldType.CURRENCY, FieldType.PERCENTAGE]:
            try:
                float(value)
            except (TypeError, ValueError):
                return False, f"{self.label} must be a number"
        
        elif self.field_type == FieldType.RATING:
            try:
                rating = int(value)
                min_rating = rules.get("min", 1)
                max_rating = rules.get("max", 5)
                if rating < min_rating or rating > max_rating:
                    return False, f"{self.label} must be between {min_rating} and {max_rating}"
            except (TypeError, ValueError):
                return False, f"{self.label} must be an integer"
        
        return True, None


class CustomFieldValue(Base):
    """Stores actual values for custom fields"""
    __tablename__ = 'custom_field_values'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to field definition
    field_definition_id = Column(UUID(as_uuid=True), ForeignKey('custom_field_definitions.id'), nullable=False)
    
    # Entity reference (polymorphic)
    entity_type = Column(SQLEnum(EntityType), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Value storage (using JSON for flexibility)
    value = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    
    # Relationships
    field_definition = relationship("CustomFieldDefinition", back_populates="values")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('field_definition_id', 'entity_id', name='uq_field_entity'),
        Index('idx_value_entity', 'entity_type', 'entity_id'),
        Index('idx_value_field', 'field_definition_id'),
    )
    
    def get_display_value(self) -> str:
        """Get formatted display value"""
        if self.value is None:
            return ""
        
        field = self.field_definition
        
        if field.field_type == FieldType.BOOLEAN:
            return "Yes" if self.value else "No"
        
        elif field.field_type == FieldType.SELECT:
            if field.options:
                for opt in field.options:
                    if opt["value"] == self.value:
                        return opt["label"]
            return str(self.value)
        
        elif field.field_type == FieldType.MULTISELECT:
            if field.options and isinstance(self.value, list):
                labels = []
                for v in self.value:
                    for opt in field.options:
                        if opt["value"] == v:
                            labels.append(opt["label"])
                            break
                return ", ".join(labels)
            return str(self.value)
        
        elif field.field_type == FieldType.CURRENCY:
            return f"${self.value:,.2f}"
        
        elif field.field_type == FieldType.PERCENTAGE:
            return f"{self.value}%"
        
        elif field.field_type == FieldType.RATING:
            return "⭐" * int(self.value)
        
        elif field.field_type in [FieldType.DATE, FieldType.DATETIME]:
            if isinstance(self.value, str):
                return self.value
            return self.value.strftime("%Y-%m-%d %H:%M:%S" if field.field_type == FieldType.DATETIME else "%Y-%m-%d")
        
        return str(self.value)


class CustomFieldTemplate(Base):
    """Pre-defined templates for common custom field sets"""
    __tablename__ = 'custom_field_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    entity_type = Column(SQLEnum(EntityType), nullable=False)
    category = Column(String(50))  # e.g., "CRM", "Project Management", "HR"
    
    # Field definitions as JSON
    fields = Column(JSON, nullable=False)
    # Format: [
    #   {
    #     "name": "customer_id",
    #     "label": "Customer ID",
    #     "field_type": "text",
    #     "is_required": true,
    #     "validation_rules": {"pattern": "^CUS-[0-9]{6}$"}
    #   }
    # ]
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Helper functions for custom field management

def create_field_definition(
    name: str,
    label: str,
    field_type: FieldType,
    entity_type: EntityType,
    **kwargs
) -> CustomFieldDefinition:
    """Create a new custom field definition"""
    field = CustomFieldDefinition(
        name=name,
        label=label,
        field_type=field_type,
        entity_type=entity_type,
        **kwargs
    )
    return field


def set_custom_field_value(
    entity_type: EntityType,
    entity_id: str,
    field_name: str,
    value: Any,
    db_session
) -> CustomFieldValue:
    """Set a custom field value for an entity"""
    # Get field definition
    field_def = db_session.query(CustomFieldDefinition).filter_by(
        entity_type=entity_type,
        name=field_name
    ).first()
    
    if not field_def:
        raise ValueError(f"Field {field_name} not found for {entity_type}")
    
    # Validate value
    is_valid, error = field_def.validate_value(value)
    if not is_valid:
        raise ValueError(error)
    
    # Get or create field value
    field_value = db_session.query(CustomFieldValue).filter_by(
        field_definition_id=field_def.id,
        entity_id=entity_id
    ).first()
    
    if field_value:
        field_value.value = value
        field_value.updated_at = datetime.utcnow()
    else:
        field_value = CustomFieldValue(
            field_definition_id=field_def.id,
            entity_type=entity_type,
            entity_id=entity_id,
            value=value
        )
        db_session.add(field_value)
    
    return field_value


def get_entity_custom_fields(
    entity_type: EntityType,
    entity_id: str,
    db_session
) -> Dict[str, Any]:
    """Get all custom field values for an entity"""
    values = db_session.query(CustomFieldValue).join(
        CustomFieldDefinition
    ).filter(
        CustomFieldValue.entity_type == entity_type,
        CustomFieldValue.entity_id == entity_id
    ).all()
    
    result = {}
    for value in values:
        field = value.field_definition
        result[field.name] = {
            "label": field.label,
            "type": field.field_type,
            "value": value.value,
            "display_value": value.get_display_value()
        }
    
    return result