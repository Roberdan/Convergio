"""
Template Library - Pre-defined templates for custom fields across different domains
Supports IT, Marketing, Legal, Finance, HR, and custom templates
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json


class FieldDefinition(BaseModel):
    """Definition of a custom field"""
    name: str
    type: str  # text, number, date, select, multiselect, boolean, url, email
    label: str
    required: bool = False
    default_value: Any = None
    options: Optional[List[str]] = None  # For select/multiselect
    validation: Optional[Dict[str, Any]] = None  # min, max, pattern, etc.
    help_text: Optional[str] = None
    display_order: int = 0


class TemplateDefinition(BaseModel):
    """Template definition for a domain"""
    id: str
    name: str
    domain: str  # IT, Marketing, Legal, Finance, HR, Custom
    description: str
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Custom fields for different entities
    project_fields: List[FieldDefinition] = []
    task_fields: List[FieldDefinition] = []
    resource_fields: List[FieldDefinition] = []
    epic_fields: List[FieldDefinition] = []
    
    # Template configuration
    workflows: List[Dict[str, Any]] = []  # Pre-defined workflows
    views: List[Dict[str, Any]] = []  # Pre-configured views
    automation_rules: List[Dict[str, Any]] = []  # Automation rules
    
    # Metadata
    tags: List[str] = []
    icon: str = "template"
    color: str = "#6B7280"


class TemplateLibrary:
    """Service for managing field templates"""
    
    def __init__(self):
        self.templates: Dict[str, TemplateDefinition] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default templates for common domains"""
        
        # IT Project Template
        self.templates["it_project"] = TemplateDefinition(
            id="it_project",
            name="IT Project Management",
            domain="IT",
            description="Template for managing IT projects with sprints, technical debt, and deployments",
            project_fields=[
                FieldDefinition(
                    name="project_type",
                    type="select",
                    label="Project Type",
                    required=True,
                    options=["Infrastructure", "Application", "Security", "Data", "Integration"],
                    display_order=1
                ),
                FieldDefinition(
                    name="tech_stack",
                    type="multiselect",
                    label="Technology Stack",
                    options=["Python", "JavaScript", "Java", "Go", "React", "Vue", "Docker", "Kubernetes"],
                    display_order=2
                ),
                FieldDefinition(
                    name="environment",
                    type="multiselect",
                    label="Environments",
                    options=["Development", "Staging", "UAT", "Production"],
                    display_order=3
                ),
                FieldDefinition(
                    name="repository_url",
                    type="url",
                    label="Repository URL",
                    help_text="Git repository URL",
                    display_order=4
                ),
                FieldDefinition(
                    name="ci_cd_pipeline",
                    type="url",
                    label="CI/CD Pipeline URL",
                    display_order=5
                )
            ],
            task_fields=[
                FieldDefinition(
                    name="story_points",
                    type="number",
                    label="Story Points",
                    validation={"min": 1, "max": 21},
                    display_order=1
                ),
                FieldDefinition(
                    name="sprint",
                    type="text",
                    label="Sprint",
                    display_order=2
                ),
                FieldDefinition(
                    name="technical_debt",
                    type="boolean",
                    label="Technical Debt",
                    default_value=False,
                    display_order=3
                ),
                FieldDefinition(
                    name="code_review_url",
                    type="url",
                    label="Code Review URL",
                    display_order=4
                ),
                FieldDefinition(
                    name="test_coverage",
                    type="number",
                    label="Test Coverage %",
                    validation={"min": 0, "max": 100},
                    display_order=5
                )
            ],
            icon="code",
            color="#3B82F6"
        )
        
        # Marketing Campaign Template
        self.templates["marketing_campaign"] = TemplateDefinition(
            id="marketing_campaign",
            name="Marketing Campaign Management",
            domain="Marketing",
            description="Template for managing marketing campaigns with channels, budgets, and KPIs",
            project_fields=[
                FieldDefinition(
                    name="campaign_type",
                    type="select",
                    label="Campaign Type",
                    required=True,
                    options=["Brand Awareness", "Lead Generation", "Product Launch", "Event", "Content"],
                    display_order=1
                ),
                FieldDefinition(
                    name="target_audience",
                    type="multiselect",
                    label="Target Audience",
                    options=["B2B", "B2C", "Enterprise", "SMB", "Startups", "Developers"],
                    display_order=2
                ),
                FieldDefinition(
                    name="channels",
                    type="multiselect",
                    label="Marketing Channels",
                    options=["Email", "Social Media", "PPC", "SEO", "Content", "Events", "Webinars"],
                    display_order=3
                ),
                FieldDefinition(
                    name="campaign_budget",
                    type="number",
                    label="Campaign Budget ($)",
                    required=True,
                    validation={"min": 0},
                    display_order=4
                ),
                FieldDefinition(
                    name="target_roi",
                    type="number",
                    label="Target ROI (%)",
                    validation={"min": 0},
                    display_order=5
                )
            ],
            task_fields=[
                FieldDefinition(
                    name="content_type",
                    type="select",
                    label="Content Type",
                    options=["Blog Post", "Video", "Infographic", "Whitepaper", "Case Study", "Social Post"],
                    display_order=1
                ),
                FieldDefinition(
                    name="target_metrics",
                    type="multiselect",
                    label="Target Metrics",
                    options=["Impressions", "Clicks", "Conversions", "Engagement", "Leads", "Sales"],
                    display_order=2
                ),
                FieldDefinition(
                    name="a_b_test",
                    type="boolean",
                    label="A/B Testing",
                    default_value=False,
                    display_order=3
                ),
                FieldDefinition(
                    name="creative_url",
                    type="url",
                    label="Creative Assets URL",
                    display_order=4
                )
            ],
            icon="megaphone",
            color="#8B5CF6"
        )
        
        # Legal Contract Template
        self.templates["legal_contract"] = TemplateDefinition(
            id="legal_contract",
            name="Legal Contract Management",
            domain="Legal",
            description="Template for managing legal contracts and compliance",
            project_fields=[
                FieldDefinition(
                    name="contract_type",
                    type="select",
                    label="Contract Type",
                    required=True,
                    options=["NDA", "MSA", "SLA", "Employment", "Vendor", "Customer", "Partnership"],
                    display_order=1
                ),
                FieldDefinition(
                    name="jurisdiction",
                    type="select",
                    label="Jurisdiction",
                    required=True,
                    options=["US", "EU", "UK", "Canada", "Australia", "Other"],
                    display_order=2
                ),
                FieldDefinition(
                    name="contract_value",
                    type="number",
                    label="Contract Value ($)",
                    validation={"min": 0},
                    display_order=3
                ),
                FieldDefinition(
                    name="expiry_date",
                    type="date",
                    label="Contract Expiry Date",
                    required=True,
                    display_order=4
                ),
                FieldDefinition(
                    name="auto_renewal",
                    type="boolean",
                    label="Auto-Renewal",
                    default_value=False,
                    display_order=5
                )
            ],
            task_fields=[
                FieldDefinition(
                    name="review_type",
                    type="select",
                    label="Review Type",
                    options=["Initial Review", "Negotiation", "Amendment", "Renewal", "Termination"],
                    display_order=1
                ),
                FieldDefinition(
                    name="risk_level",
                    type="select",
                    label="Risk Level",
                    options=["Low", "Medium", "High", "Critical"],
                    display_order=2
                ),
                FieldDefinition(
                    name="compliance_check",
                    type="multiselect",
                    label="Compliance Requirements",
                    options=["GDPR", "CCPA", "HIPAA", "SOC2", "ISO27001", "PCI-DSS"],
                    display_order=3
                ),
                FieldDefinition(
                    name="approval_required",
                    type="multiselect",
                    label="Approval Required From",
                    options=["Legal", "Finance", "Executive", "Board", "Compliance"],
                    display_order=4
                )
            ],
            icon="scale",
            color="#EF4444"
        )
        
        # Finance Budget Template
        self.templates["finance_budget"] = TemplateDefinition(
            id="finance_budget",
            name="Finance & Budget Management",
            domain="Finance",
            description="Template for financial planning and budget management",
            project_fields=[
                FieldDefinition(
                    name="budget_category",
                    type="select",
                    label="Budget Category",
                    required=True,
                    options=["Operating", "Capital", "R&D", "Marketing", "HR", "IT"],
                    display_order=1
                ),
                FieldDefinition(
                    name="fiscal_year",
                    type="text",
                    label="Fiscal Year",
                    required=True,
                    display_order=2
                ),
                FieldDefinition(
                    name="total_budget",
                    type="number",
                    label="Total Budget ($)",
                    required=True,
                    validation={"min": 0},
                    display_order=3
                ),
                FieldDefinition(
                    name="cost_center",
                    type="text",
                    label="Cost Center",
                    required=True,
                    display_order=4
                ),
                FieldDefinition(
                    name="approval_status",
                    type="select",
                    label="Approval Status",
                    options=["Draft", "Pending", "Approved", "Rejected"],
                    default_value="Draft",
                    display_order=5
                )
            ],
            task_fields=[
                FieldDefinition(
                    name="expense_type",
                    type="select",
                    label="Expense Type",
                    options=["Personnel", "Software", "Hardware", "Services", "Travel", "Training"],
                    display_order=1
                ),
                FieldDefinition(
                    name="amount",
                    type="number",
                    label="Amount ($)",
                    required=True,
                    validation={"min": 0},
                    display_order=2
                ),
                FieldDefinition(
                    name="invoice_number",
                    type="text",
                    label="Invoice Number",
                    display_order=3
                ),
                FieldDefinition(
                    name="payment_terms",
                    type="select",
                    label="Payment Terms",
                    options=["Net 15", "Net 30", "Net 60", "Due on Receipt"],
                    display_order=4
                ),
                FieldDefinition(
                    name="tax_deductible",
                    type="boolean",
                    label="Tax Deductible",
                    default_value=False,
                    display_order=5
                )
            ],
            icon="currency-dollar",
            color="#10B981"
        )
        
        # HR Recruitment Template
        self.templates["hr_recruitment"] = TemplateDefinition(
            id="hr_recruitment",
            name="HR Recruitment & Onboarding",
            domain="HR",
            description="Template for managing recruitment and employee onboarding",
            project_fields=[
                FieldDefinition(
                    name="position_title",
                    type="text",
                    label="Position Title",
                    required=True,
                    display_order=1
                ),
                FieldDefinition(
                    name="department",
                    type="select",
                    label="Department",
                    required=True,
                    options=["Engineering", "Sales", "Marketing", "Finance", "HR", "Operations", "Legal"],
                    display_order=2
                ),
                FieldDefinition(
                    name="employment_type",
                    type="select",
                    label="Employment Type",
                    options=["Full-time", "Part-time", "Contract", "Intern"],
                    default_value="Full-time",
                    display_order=3
                ),
                FieldDefinition(
                    name="salary_range",
                    type="text",
                    label="Salary Range",
                    display_order=4
                ),
                FieldDefinition(
                    name="hiring_manager",
                    type="text",
                    label="Hiring Manager",
                    required=True,
                    display_order=5
                )
            ],
            task_fields=[
                FieldDefinition(
                    name="candidate_name",
                    type="text",
                    label="Candidate Name",
                    display_order=1
                ),
                FieldDefinition(
                    name="interview_stage",
                    type="select",
                    label="Interview Stage",
                    options=["Screening", "Phone", "Technical", "Behavioral", "Final", "Reference Check"],
                    display_order=2
                ),
                FieldDefinition(
                    name="interview_score",
                    type="number",
                    label="Interview Score (1-10)",
                    validation={"min": 1, "max": 10},
                    display_order=3
                ),
                FieldDefinition(
                    name="resume_url",
                    type="url",
                    label="Resume URL",
                    display_order=4
                ),
                FieldDefinition(
                    name="background_check",
                    type="boolean",
                    label="Background Check Complete",
                    default_value=False,
                    display_order=5
                )
            ],
            icon="users",
            color="#F59E0B"
        )
    
    def get_template(self, template_id: str) -> Optional[TemplateDefinition]:
        """Get a specific template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self, domain: Optional[str] = None) -> List[TemplateDefinition]:
        """List all templates, optionally filtered by domain"""
        templates = list(self.templates.values())
        
        if domain:
            templates = [t for t in templates if t.domain == domain]
        
        return sorted(templates, key=lambda x: (x.domain, x.name))
    
    def create_template(self, template: TemplateDefinition) -> TemplateDefinition:
        """Create a new custom template"""
        if template.id in self.templates:
            raise ValueError(f"Template with ID {template.id} already exists")
        
        template.created_at = datetime.utcnow()
        template.updated_at = datetime.utcnow()
        self.templates[template.id] = template
        
        return template
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> TemplateDefinition:
        """Update an existing template"""
        if template_id not in self.templates:
            raise ValueError(f"Template with ID {template_id} not found")
        
        template = self.templates[template_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.utcnow()
        template.version = self._increment_version(template.version)
        
        return template
    
    def clone_template(self, template_id: str, new_id: str, new_name: str) -> TemplateDefinition:
        """Clone an existing template"""
        if template_id not in self.templates:
            raise ValueError(f"Template with ID {template_id} not found")
        
        if new_id in self.templates:
            raise ValueError(f"Template with ID {new_id} already exists")
        
        # Deep copy the template
        original = self.templates[template_id]
        cloned = TemplateDefinition(
            **{
                **original.dict(),
                "id": new_id,
                "name": new_name,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "version": "1.0.0"
            }
        )
        
        self.templates[new_id] = cloned
        return cloned
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a custom template"""
        # Don't allow deletion of default templates
        default_templates = [
            "it_project", "marketing_campaign", "legal_contract",
            "finance_budget", "hr_recruitment"
        ]
        
        if template_id in default_templates:
            raise ValueError(f"Cannot delete default template {template_id}")
        
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        
        return False
    
    def apply_template(self, template_id: str, entity_type: str) -> List[FieldDefinition]:
        """Get fields for a specific entity type from a template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        field_map = {
            "project": template.project_fields,
            "task": template.task_fields,
            "resource": template.resource_fields,
            "epic": template.epic_fields
        }
        
        return field_map.get(entity_type, [])
    
    def export_template(self, template_id: str) -> str:
        """Export template as JSON"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        return json.dumps(template.dict(), indent=2, default=str)
    
    def import_template(self, template_json: str) -> TemplateDefinition:
        """Import template from JSON"""
        data = json.loads(template_json)
        template = TemplateDefinition(**data)
        
        # Ensure unique ID
        if template.id in self.templates:
            template.id = f"{template.id}_{datetime.utcnow().timestamp()}"
        
        self.templates[template.id] = template
        return template
    
    def validate_field_value(self, field: FieldDefinition, value: Any) -> bool:
        """Validate a value against field definition"""
        if field.required and value is None:
            return False
        
        if value is None:
            return True
        
        # Type validation
        if field.type == "number":
            if not isinstance(value, (int, float)):
                return False
            
            if field.validation:
                if "min" in field.validation and value < field.validation["min"]:
                    return False
                if "max" in field.validation and value > field.validation["max"]:
                    return False
        
        elif field.type == "select":
            if field.options and value not in field.options:
                return False
        
        elif field.type == "multiselect":
            if field.options:
                if not isinstance(value, list):
                    return False
                if not all(v in field.options for v in value):
                    return False
        
        elif field.type == "boolean":
            if not isinstance(value, bool):
                return False
        
        elif field.type == "date":
            # Should be ISO format string or datetime
            if not isinstance(value, (str, datetime)):
                return False
        
        elif field.type in ["text", "url", "email"]:
            if not isinstance(value, str):
                return False
        
        return True
    
    def _increment_version(self, version: str) -> str:
        """Increment version number (patch level)"""
        parts = version.split(".")
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
        return ".".join(parts)
    
    def get_field_schema(self, template_id: str, entity_type: str) -> Dict[str, Any]:
        """Get JSON schema for custom fields validation"""
        fields = self.apply_template(template_id, entity_type)
        
        properties = {}
        required = []
        
        for field in fields:
            field_schema = {
                "title": field.label,
                "description": field.help_text
            }
            
            # Map field types to JSON schema types
            if field.type == "number":
                field_schema["type"] = "number"
                if field.validation:
                    if "min" in field.validation:
                        field_schema["minimum"] = field.validation["min"]
                    if "max" in field.validation:
                        field_schema["maximum"] = field.validation["max"]
            
            elif field.type == "boolean":
                field_schema["type"] = "boolean"
            
            elif field.type == "date":
                field_schema["type"] = "string"
                field_schema["format"] = "date-time"
            
            elif field.type == "select":
                field_schema["type"] = "string"
                if field.options:
                    field_schema["enum"] = field.options
            
            elif field.type == "multiselect":
                field_schema["type"] = "array"
                field_schema["items"] = {"type": "string"}
                if field.options:
                    field_schema["items"]["enum"] = field.options
            
            else:  # text, url, email
                field_schema["type"] = "string"
                if field.type == "url":
                    field_schema["format"] = "uri"
                elif field.type == "email":
                    field_schema["format"] = "email"
            
            properties[field.name] = field_schema
            
            if field.required:
                required.append(field.name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }


# Singleton instance
template_library = TemplateLibrary()