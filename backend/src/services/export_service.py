"""
Export Service - CSV and JSON export functionality
For analytics, reports, and data portability
"""

import csv
import json
import io
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from fastapi import HTTPException, APIRouter, Query
from fastapi.responses import StreamingResponse

class ExportService:
    """Service for exporting data in various formats"""
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], filename: str = "export.csv") -> StreamingResponse:
        """Export data to CSV format"""
        if not data:
            raise HTTPException(status_code=400, detail="No data to export")
        
        output = io.StringIO()
        
        # Get all unique keys from data
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        fieldnames = sorted(list(fieldnames))
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in data:
            # Flatten nested objects
            flat_item = ExportService._flatten_dict(item)
            writer.writerow(flat_item)
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    @staticmethod
    def export_to_json(data: Any, filename: str = "export.json") -> StreamingResponse:
        """Export data to JSON format"""
        json_str = json.dumps(data, indent=2, default=str)
        
        return StreamingResponse(
            io.BytesIO(json_str.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    @staticmethod
    def export_to_excel(data: List[Dict[str, Any]], filename: str = "export.xlsx") -> StreamingResponse:
        """Export data to Excel format"""
        if not data:
            raise HTTPException(status_code=400, detail="No data to export")
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            
            # Auto-adjust column width
            worksheet = writer.sheets['Data']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 50)
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    @staticmethod
    def export_project_analytics(project_data: Dict[str, Any], format: str = "json") -> StreamingResponse:
        """Export project analytics in specified format"""
        # Prepare analytics data
        analytics_data = {
            "project": project_data.get("name", "Unknown"),
            "export_date": datetime.utcnow().isoformat(),
            "metrics": {
                "total_tasks": project_data.get("total_tasks", 0),
                "completed_tasks": project_data.get("completed_tasks", 0),
                "completion_rate": project_data.get("completion_rate", 0),
                "budget": project_data.get("budget", 0),
                "actual_cost": project_data.get("actual_cost", 0),
                "cost_variance": project_data.get("cost_variance", 0),
                "velocity": project_data.get("velocity", 0),
                "health_score": project_data.get("health_score", 0)
            },
            "tasks": project_data.get("tasks", []),
            "resources": project_data.get("resources", []),
            "timeline": {
                "start_date": project_data.get("start_date"),
                "end_date": project_data.get("end_date"),
                "duration_days": project_data.get("duration_days", 0)
            }
        }
        
        filename_base = f"project_analytics_{project_data.get('id', 'export')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        if format == "csv":
            # Flatten for CSV export
            flat_data = []
            
            # Add metrics as rows
            for key, value in analytics_data["metrics"].items():
                flat_data.append({
                    "category": "metric",
                    "name": key,
                    "value": value
                })
            
            # Add tasks
            for task in analytics_data["tasks"]:
                flat_data.append({
                    "category": "task",
                    "name": task.get("title"),
                    "value": task.get("status"),
                    "progress": task.get("progress", 0)
                })
            
            return ExportService.export_to_csv(flat_data, f"{filename_base}.csv")
        
        elif format == "excel":
            # Create multi-sheet Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Metrics sheet
                metrics_df = pd.DataFrame([analytics_data["metrics"]])
                metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
                
                # Tasks sheet
                if analytics_data["tasks"]:
                    tasks_df = pd.DataFrame(analytics_data["tasks"])
                    tasks_df.to_excel(writer, sheet_name='Tasks', index=False)
                
                # Resources sheet
                if analytics_data["resources"]:
                    resources_df = pd.DataFrame(analytics_data["resources"])
                    resources_df.to_excel(writer, sheet_name='Resources', index=False)
            
            output.seek(0)
            
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.xlsx"
                }
            )
        
        else:  # JSON
            return ExportService.export_to_json(analytics_data, f"{filename_base}.json")
    
    @staticmethod
    def export_tenant_usage(tenant_data: Dict[str, Any], format: str = "json") -> StreamingResponse:
        """Export tenant usage data"""
        usage_data = {
            "tenant": tenant_data.get("name"),
            "export_date": datetime.utcnow().isoformat(),
            "subscription": {
                "plan": tenant_data.get("subscription_plan"),
                "billing_period": tenant_data.get("billing_period"),
                "status": tenant_data.get("status")
            },
            "usage": {
                "users": f"{tenant_data.get('current_users', 0)}/{tenant_data.get('max_users', 0)}",
                "projects": f"{tenant_data.get('current_projects', 0)}/{tenant_data.get('max_projects', 0)}",
                "workflows": f"{tenant_data.get('current_workflows', 0)}/{tenant_data.get('max_workflows', 0)}",
                "api_calls": f"{tenant_data.get('current_api_calls', 0)}/{tenant_data.get('max_api_calls', 0)}",
                "storage_gb": f"{tenant_data.get('current_storage_gb', 0)}/{tenant_data.get('max_storage_gb', 0)}",
                "ai_tokens": f"{tenant_data.get('current_ai_tokens', 0)}/{tenant_data.get('max_ai_tokens', 0)}"
            },
            "costs": {
                "monthly_cost": tenant_data.get("monthly_cost", 0),
                "usage_charges": tenant_data.get("usage_charges", 0),
                "total_cost": tenant_data.get("total_cost", 0)
            }
        }
        
        filename_base = f"tenant_usage_{tenant_data.get('id', 'export')}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        if format == "csv":
            flat_data = []
            for category, items in usage_data.items():
                if isinstance(items, dict):
                    for key, value in items.items():
                        flat_data.append({
                            "category": category,
                            "metric": key,
                            "value": value
                        })
                else:
                    flat_data.append({
                        "category": "info",
                        "metric": category,
                        "value": items
                    })
            
            return ExportService.export_to_csv(flat_data, f"{filename_base}.csv")
        else:
            return ExportService.export_to_json(usage_data, f"{filename_base}.json")
    
    @staticmethod
    def _flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(ExportService._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)


# Export API endpoints to be added to routers

export_router = APIRouter(prefix="/api/v1/export", tags=["Export"])

@export_router.get("/projects/{project_id}/analytics")
async def export_project_analytics(
    project_id: str,
    format: str = Query("json", enum=["json", "csv", "excel"])
):
    """Export project analytics in specified format"""
    # Get project data (mock for now)
    project_data = {
        "id": project_id,
        "name": "Sample Project",
        "total_tasks": 100,
        "completed_tasks": 75,
        "completion_rate": 0.75,
        "budget": 100000,
        "actual_cost": 85000,
        "cost_variance": -15000,
        "velocity": 12.5,
        "health_score": 85
    }
    
    return ExportService.export_project_analytics(project_data, format)


@export_router.get("/tenants/{tenant_id}/usage")
async def export_tenant_usage(
    tenant_id: str,
    format: str = Query("json", enum=["json", "csv"])
):
    """Export tenant usage data"""
    # Get tenant data (mock for now)
    tenant_data = {
        "id": tenant_id,
        "name": "Sample Tenant",
        "subscription_plan": "professional",
        "billing_period": "monthly",
        "status": "active",
        "current_users": 15,
        "max_users": 50,
        "current_projects": 8,
        "max_projects": 20,
        "current_workflows": 45,
        "max_workflows": 100,
        "current_api_calls": 5000,
        "max_api_calls": 10000,
        "current_storage_gb": 12.5,
        "max_storage_gb": 100,
        "current_ai_tokens": 45000,
        "max_ai_tokens": 100000,
        "monthly_cost": 299,
        "usage_charges": 45.50,
        "total_cost": 344.50
    }
    
    return ExportService.export_tenant_usage(tenant_data, format)