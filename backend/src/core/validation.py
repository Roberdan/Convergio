"""
🔧 Convergio - Configuration Validation at Startup
Comprehensive validation of environment and system configuration
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Tuple
import structlog
import asyncpg
import redis.asyncio as redis
from openai import OpenAI
from anthropic import Anthropic

from .config import get_settings

logger = structlog.get_logger()

class ConfigurationValidator:
    """Validates system configuration and dependencies at startup"""
    
    def __init__(self):
        self.settings = get_settings()
        self.validation_results = {}
        self.critical_failures = []
        self.warnings = []
    
    async def validate_all(self) -> Tuple[bool, Dict[str, any]]:
        """Run all validation checks"""
        logger.info("🔍 Starting configuration validation...")
        
        # Environment validation
        await self.validate_environment_variables()
        await self.validate_file_paths()
        
        # Service validation
        await self.validate_database_connection()
        await self.validate_redis_connection()
        await self.validate_ai_services()
        
        # Security validation
        await self.validate_jwt_configuration()
        await self.validate_cors_configuration()
        
        # System validation
        await self.validate_directory_structure()
        await self.validate_agent_definitions()
        
        # Compile results
        has_critical_failures = len(self.critical_failures) > 0
        
        results = {
            "success": not has_critical_failures,
            "critical_failures": self.critical_failures,
            "warnings": self.warnings,
            "details": self.validation_results
        }
        
        # Log summary
        if has_critical_failures:
            logger.error(f"❌ Configuration validation failed: {len(self.critical_failures)} critical issues")
            for failure in self.critical_failures:
                logger.error(f"  • {failure}")
        else:
            logger.info(f"✅ Configuration validation passed with {len(self.warnings)} warnings")
        
        return not has_critical_failures, results
    
    async def validate_environment_variables(self):
        """Validate required environment variables"""
        logger.info("🔧 Validating environment variables...")
        
        required_vars = {
            "OPENAI_API_KEY": "OpenAI API access",
            "ANTHROPIC_API_KEY": "Anthropic API access", 
            "POSTGRES_USER": "Database authentication",
            "POSTGRES_PASSWORD": "Database authentication",
            "POSTGRES_DB": "Database name",
            "JWT_PRIVATE_KEY_PATH": "JWT authentication"
        }
        
        missing_vars = []
        empty_vars = []
        
        for var_name, description in required_vars.items():
            value = getattr(self.settings, var_name, None)
            
            if not value:
                if var_name not in os.environ:
                    missing_vars.append(f"{var_name} ({description})")
                else:
                    empty_vars.append(f"{var_name} ({description})")
        
        if missing_vars:
            self.critical_failures.extend([f"Missing environment variable: {var}" for var in missing_vars])
        
        if empty_vars:
            self.critical_failures.extend([f"Empty environment variable: {var}" for var in empty_vars])
        
        # Validate API key formats
        if hasattr(self.settings, 'OPENAI_API_KEY') and self.settings.OPENAI_API_KEY:
            if not self.settings.OPENAI_API_KEY.startswith('sk-'):
                self.warnings.append("OpenAI API key format may be invalid (should start with 'sk-')")
        
        self.validation_results["environment_variables"] = {
            "status": "passed" if not missing_vars and not empty_vars else "failed",
            "missing": missing_vars,
            "empty": empty_vars
        }
    
    async def validate_file_paths(self):
        """Validate required file paths exist"""
        logger.info("📁 Validating file paths...")
        
        required_paths = {
            "JWT_PRIVATE_KEY_PATH": "JWT private key for authentication",
            "JWT_PUBLIC_KEY_PATH": "JWT public key for verification"
        }
        
        missing_files = []
        
        for path_setting, description in required_paths.items():
            if hasattr(self.settings, path_setting):
                path_value = getattr(self.settings, path_setting)
                if path_value:
                    full_path = Path(path_value)
                    if not full_path.is_absolute():
                        full_path = self.settings.BASE_DIR / path_value
                    
                    if not full_path.exists():
                        missing_files.append(f"{path_value} ({description})")
        
        if missing_files:
            self.critical_failures.extend([f"Missing required file: {file}" for file in missing_files])
        
        self.validation_results["file_paths"] = {
            "status": "passed" if not missing_files else "failed",
            "missing": missing_files
        }
    
    async def validate_database_connection(self):
        """Validate PostgreSQL database connection"""
        logger.info("🗄️ Validating database connection...")
        
        try:
            # Test connection
            conn = await asyncpg.connect(self.settings.DATABASE_URL)
            
            # Test basic query
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            
            # Check for pgvector extension
            conn = await asyncpg.connect(self.settings.DATABASE_URL)
            extensions = await conn.fetch("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            await conn.close()
            
            has_vector = len(extensions) > 0
            if not has_vector:
                self.warnings.append("pgvector extension not installed - vector search will be limited")
            
            self.validation_results["database"] = {
                "status": "passed",
                "version": version,
                "pgvector_available": has_vector
            }
            
        except Exception as e:
            self.critical_failures.append(f"Database connection failed: {str(e)}")
            self.validation_results["database"] = {
                "status": "failed",
                "error": str(e)
            }
    
    async def validate_redis_connection(self):
        """Validate Redis connection"""
        logger.info("🚀 Validating Redis connection...")
        
        try:
            client = redis.from_url(self.settings.REDIS_URL)
            
            # Test connection
            await client.ping()
            
            # Test basic operations
            await client.set("test_key", "test_value", ex=60)
            await client.get("test_key")
            await client.delete("test_key")
            
            await client.aclose()
            
            self.validation_results["redis"] = {
                "status": "passed",
                "operations": "read/write successful"
            }
            
        except Exception as e:
            self.critical_failures.append(f"Redis connection failed: {str(e)}")
            self.validation_results["redis"] = {
                "status": "failed", 
                "error": str(e)
            }
    
    async def validate_ai_services(self):
        """Validate AI service connections"""
        logger.info("🤖 Validating AI services...")
        
        # Test OpenAI
        try:
            if hasattr(self.settings, 'OPENAI_API_KEY') and self.settings.OPENAI_API_KEY:
                client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
                # Test with a minimal request
                response = client.models.list()
                models = [model.id for model in response.data]
                
                self.validation_results["openai"] = {
                    "status": "passed",
                    "models_available": len(models)
                }
            else:
                self.validation_results["openai"] = {
                    "status": "skipped",
                    "reason": "No API key provided"
                }
        except Exception as e:
            self.warnings.append(f"OpenAI API validation failed: {str(e)}")
            self.validation_results["openai"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # Test Anthropic
        try:
            if hasattr(self.settings, 'ANTHROPIC_API_KEY') and self.settings.ANTHROPIC_API_KEY:
                client = Anthropic(api_key=self.settings.ANTHROPIC_API_KEY)
                # For Anthropic, we can't easily test without making a request
                # So we just validate the key format
                if self.settings.ANTHROPIC_API_KEY.startswith('ant-'):
                    self.validation_results["anthropic"] = {
                        "status": "passed",
                        "note": "API key format valid"
                    }
                else:
                    self.warnings.append("Anthropic API key format may be invalid")
            else:
                self.validation_results["anthropic"] = {
                    "status": "skipped",
                    "reason": "No API key provided"
                }
        except Exception as e:
            self.warnings.append(f"Anthropic API validation failed: {str(e)}")
            self.validation_results["anthropic"] = {
                "status": "failed",
                "error": str(e)
            }
    
    async def validate_jwt_configuration(self):
        """Validate JWT security configuration"""
        logger.info("🔐 Validating JWT configuration...")
        
        issues = []
        
        # Check algorithm
        if self.settings.JWT_ALGORITHM != "RS256":
            issues.append(f"JWT algorithm should be RS256, found: {self.settings.JWT_ALGORITHM}")
        
        # Check token expiry times
        if self.settings.JWT_TOKEN_EXPIRY < 3600:  # Less than 1 hour
            self.warnings.append("JWT token expiry is very short (< 1 hour)")
        elif self.settings.JWT_TOKEN_EXPIRY > 86400 * 7:  # More than 1 week
            self.warnings.append("JWT token expiry is very long (> 1 week)")
        
        # Check issuer/audience
        if not self.settings.JWT_ISSUER or not self.settings.JWT_AUDIENCE:
            issues.append("JWT issuer and audience should be configured")
        
        if issues:
            self.critical_failures.extend(issues)
        
        self.validation_results["jwt"] = {
            "status": "passed" if not issues else "failed",
            "algorithm": self.settings.JWT_ALGORITHM,
            "token_expiry_hours": self.settings.JWT_TOKEN_EXPIRY / 3600,
            "issues": issues
        }
    
    async def validate_cors_configuration(self):
        """Validate CORS configuration"""
        logger.info("🌐 Validating CORS configuration...")
        
        cors_origins = self.settings.cors_origins_list
        warnings = []
        
        if "*" in cors_origins and self.settings.ENVIRONMENT == "production":
            warnings.append("CORS allows all origins (*) in production - security risk")
        
        # Check for localhost in production
        localhost_patterns = ["localhost", "127.0.0.1"]
        if self.settings.ENVIRONMENT == "production":
            for origin in cors_origins:
                if any(pattern in origin for pattern in localhost_patterns):
                    warnings.append(f"CORS allows localhost in production: {origin}")
        
        if warnings:
            self.warnings.extend(warnings)
        
        self.validation_results["cors"] = {
            "status": "passed",
            "origins_count": len(cors_origins),
            "warnings": warnings
        }
    
    async def validate_directory_structure(self):
        """Validate required directory structure"""
        logger.info("📂 Validating directory structure...")
        
        required_dirs = [
            "src/agents/definitions",
            "src/api", 
            "src/core",
            "src/models",
            "tests"
        ]
        
        missing_dirs = []
        
        for dir_path in required_dirs:
            full_path = self.settings.BASE_DIR / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            self.critical_failures.extend([f"Missing directory: {dir}" for dir in missing_dirs])
        
        self.validation_results["directory_structure"] = {
            "status": "passed" if not missing_dirs else "failed",
            "missing": missing_dirs
        }
    
    async def validate_agent_definitions(self):
        """Validate AI agent definition files"""
        logger.info("🤖 Validating agent definitions...")
        
        agents_dir = self.settings.BASE_DIR / "src" / "agents" / "definitions"
        
        if not agents_dir.exists():
            self.critical_failures.append("Agent definitions directory not found")
            return
        
        agent_files = list(agents_dir.glob("*.md"))
        excluded_files = {"CommonValuesAndPrinciples.md"}
        valid_agents = [f for f in agent_files if f.name not in excluded_files]
        
        if len(valid_agents) < 40:
            self.warnings.append(f"Expected at least 40 agents, found {len(valid_agents)}")
        
        # Check for empty or invalid files
        invalid_files = []
        for agent_file in valid_agents:
            try:
                content = agent_file.read_text()
                if len(content.strip()) < 100:  # Minimum content check
                    invalid_files.append(agent_file.name)
            except Exception:
                invalid_files.append(agent_file.name)
        
        if invalid_files:
            self.warnings.extend([f"Invalid agent file: {file}" for file in invalid_files])
        
        self.validation_results["agent_definitions"] = {
            "status": "passed",
            "total_agents": len(valid_agents),
            "invalid_files": invalid_files
        }


async def validate_configuration_at_startup() -> Tuple[bool, Dict]:
    """
    Main validation function to be called at application startup
    Returns (success, detailed_results)
    """
    validator = ConfigurationValidator()
    return await validator.validate_all()


def print_validation_report(results: Dict):
    """Print a human-readable validation report"""
    print("\n" + "="*60)
    print("🔍 CONVERGIO CONFIGURATION VALIDATION REPORT")
    print("="*60)
    
    if results["success"]:
        print("✅ STATUS: CONFIGURATION VALID")
    else:
        print("❌ STATUS: CONFIGURATION ISSUES FOUND")
    
    if results["critical_failures"]:
        print(f"\n🚨 CRITICAL FAILURES ({len(results['critical_failures'])}):")
        for failure in results["critical_failures"]:
            print(f"  • {failure}")
    
    if results["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
        for warning in results["warnings"]:
            print(f"  • {warning}")
    
    print("\n📊 COMPONENT STATUS:")
    for component, details in results["details"].items():
        status_emoji = "✅" if details["status"] == "passed" else "❌" if details["status"] == "failed" else "⚠️"
        print(f"  {status_emoji} {component.replace('_', ' ').title()}: {details['status']}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    async def main():
        success, results = await validate_configuration_at_startup()
        print_validation_report(results)
        return 0 if success else 1
    
    import sys
    sys.exit(asyncio.run(main()))