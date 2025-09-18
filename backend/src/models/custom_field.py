"""
Custom Field Model - Dynamic fields for projects, tasks, and resources
Supports JSONB storage for flexible schema
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from src.core.database import Base


class FieldType(enum.Enum):
    """Supported custom field types"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    SELECT = "select"
    MULTISELECT = "multiselect"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    FILE = "file"
    USER = "user"
    RICH_TEXT = "rich_text"


class EntityType(enum.Enum):
    """Entities that can have custom fields"""
    PROJECT = "project"
    TASK = "task"
    RESOURCE = "resource"
    EPIC = "epic"
    WORKFLOW = "workflow"
    AGENT = "agent"


class CustomFieldDefinition(Base):
    """Definition of a custom field"""
    __tablename__ = "custom_field_definitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Field metadata
    name = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(String(500))
    field_type = Column(Enum(FieldType), nullable=False)
    entity_type = Column(Enum(EntityType), nullable=False)
    
    # Field configuration
    required = Column(Boolean, default=False)
    unique = Column(Boolean, default=False)
    searchable = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    
    # Field options (for select, multiselect, etc.)
    options = Column(JSONB)  # List of {value, label, color} objects
    
    # Validation rules
    validation = Column(JSONB)  # {min, max, pattern, min_length, max_length, etc.}
    
    # Default value
    default_value = Column(JSONB)
    
    # UI configuration
    ui_config = Column(JSONB)  # {width, placeholder, help_text, icon, etc.}
    
    # Template association
    template_id = Column(String(100))  # Reference to template library
    
    # Permissions
    permissions = Column(JSONB)  # {read: [roles], write: [roles], etc.}
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System fields can't be deleted
    
    # Relationships
    tenant = relationship("Tenant", back_populates="custom_fields")
    field_values = relationship("CustomFieldValue", back_populates="field_definition", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_custom_field_tenant_entity", "tenant_id", "entity_type"),
        Index("idx_custom_field_name", "tenant_id", "name"),
        Index("idx_custom_field_template", "template_id"),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "field_type": self.field_type.value,
            "entity_type": self.entity_type.value,
            "required": self.required,
            "unique": self.unique,
            "searchable": self.searchable,
            "display_order": self.display_order,
            "options": self.options,
            "validation": self.validation,
            "default_value": self.default_value,
            "ui_config": self.ui_config,
            "template_id": self.template_id,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CustomFieldValue(Base):
    """Actual values for custom fields"""
    __tablename__ = "custom_field_values"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    field_id = Column(UUID(as_uuid=True), ForeignKey("custom_field_definitions.id"), nullable=False)
    
    # Entity reference (polymorphic)
    entity_type = Column(Enum(EntityType), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # The actual value (stored as JSONB for flexibility)
    value = Column(JSONB, nullable=True)
    
    # Value metadata
    value_text = Column(String)  # Searchable text representation
    value_number = Column(Integer)  # For numeric searches/sorting
    value_date = Column(DateTime)  # For date searches/sorting
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    
    # Relationships
    field_definition = relationship("CustomFieldDefinition", back_populates="field_values")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_field_value_entity", "entity_type", "entity_id"),
        Index("idx_field_value_field", "field_id", "entity_id"),
        Index("idx_field_value_search", "tenant_id", "field_id", "value_text"),
        Index("idx_field_value_number", "tenant_id", "field_id", "value_number"),
        Index("idx_field_value_date", "tenant_id", "field_id", "value_date"),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "field_id": str(self.field_id),
            "entity_type": self.entity_type.value,
            "entity_id": str(self.entity_id),
            "value": self.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CustomFieldTemplate(Base):
    """Templates for custom field sets"""
    __tablename__ = "custom_field_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    
    # Template metadata
    template_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String(500))
    domain = Column(String(50))  # IT, Marketing, Legal, Finance, HR, Custom
    entity_type = Column(Enum(EntityType), nullable=False)
    
    # Template definition (list of field definitions)
    fields = Column(JSONB, nullable=False)
    
    # Template configuration
    is_global = Column(Boolean, default=False)  # Available to all tenants
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0.0")
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    
    # Indexes
    __table_args__ = (
        Index("idx_template_domain", "domain", "entity_type"),
        Index("idx_template_tenant", "tenant_id", "is_active"),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "entity_type": self.entity_type.value,
            "fields": self.fields,
            "is_global": self.is_global,
            "is_active": self.is_active,
            "version": self.version,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CustomFieldHistory(Base):
    """Audit trail for custom field value changes"""
    __tablename__ = "custom_field_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    field_value_id = Column(UUID(as_uuid=True), ForeignKey("custom_field_values.id"), nullable=False)
    
    # Change details
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    change_type = Column(String(20))  # create, update, delete
    change_reason = Column(String(500))
    
    # Metadata
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(UUID(as_uuid=True))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Indexes
    __table_args__ = (
        Index("idx_field_history_value", "field_value_id", "changed_at"),
        Index("idx_field_history_tenant", "tenant_id", "changed_at"),
    )