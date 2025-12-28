"""
Enhanced Configuration Validator
Validates all environment variables and configuration settings for production readiness
"""

import os
import re
import logging
from typing import List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]

class ConfigValidator:
    """Comprehensive configuration validator"""
    
    def __init__(self):
        self.logger = logger
        
    def validate_all(self) -> ValidationResult:
        """Validate all configuration aspects"""
        errors = []
        warnings = []
        recommendations = []
        
        # Validate required environment variables
        env_errors, env_warnings, env_recs = self._validate_environment_variables()
        errors.extend(env_errors)
        warnings.extend(env_warnings)
        recommendations.extend(env_recs)
        
        # Validate security configuration
        sec_errors, sec_warnings, sec_recs = self._validate_security_config()
        errors.extend(sec_errors)
        warnings.extend(sec_warnings)
        recommendations.extend(sec_recs)
        
        # Validate database configuration
        db_errors, db_warnings, db_recs = self._validate_database_config()
        errors.extend(db_errors)
        warnings.extend(db_warnings)
        recommendations.extend(db_recs)
        
        # Validate service endpoints
        endpoint_errors, endpoint_warnings, endpoint_recs = self._validate_service_endpoints()
        errors.extend(endpoint_errors)
        warnings.extend(endpoint_warnings)
        recommendations.extend(endpoint_recs)
        
        # Validate production readiness
        prod_errors, prod_warnings, prod_recs = self._validate_production_readiness()
        errors.extend(prod_errors)
        warnings.extend(prod_warnings)
        recommendations.extend(prod_recs)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _validate_environment_variables(self) -> Tuple[List[str], List[str], List[str]]:
        """Validate required environment variables"""
        errors = []
        warnings = []
        recommendations = []
        
        # Critical required variables
        required_vars = {
            "JWT_SECRET": "JWT secret for authentication",
            "POSTGRES_HOST": "PostgreSQL database host",
            "POSTGRES_DB": "PostgreSQL database name",
            "POSTGRES_USER": "PostgreSQL username",
            "POSTGRES_PASSWORD": "PostgreSQL password",
            "REDIS_HOST": "Redis cache host"
        }
        
        for var_name, description in required_vars.items():
            value = os.getenv(var_name)
            if not value:
                errors.append(f"Missing required environment variable: {var_name} ({description})")
            elif len(value.strip()) == 0:
                errors.append(f"Environment variable {var_name} is empty")
        
        # Optional but recommended variables
        recommended_vars = {
            "DEFAULT_HOST": "Configurable host for development environments",
            "FRONTEND_PORT": "Frontend service port",
            "BACKEND_PORT": "Backend service port",
            "API_PORT": "API service port",
            "ADMIN_PORT": "Admin interface port",
            "DEFAULT_USER_ID": "Default user ID for system operations",
            "DEFAULT_ANONYMOUS_USER": "Default anonymous user identifier",
            "DEFAULT_TEST_USER": "Default test user identifier",
            "REFERENCE_AGENT_TRUNCATE_LENGTH": "Reference agent content truncation length"
        }
        
        for var_name, description in recommended_vars.items():
            value = os.getenv(var_name)
            if not value:
                recommendations.append(f"Consider setting {var_name}: {description}")
        
        return errors, warnings, recommendations
    
    def _validate_security_config(self) -> Tuple[List[str], List[str], List[str]]:
        """Validate security configuration"""
        errors = []
        warnings = []
        recommendations = []
        
        # JWT Secret validation
        jwt_secret = os.getenv("JWT_SECRET")
        if jwt_secret:
            if len(jwt_secret) < 32:
                errors.append("JWT_SECRET should be at least 32 characters long")
            if jwt_secret in ["secret", "dev", "development", "test"]:
                errors.append("JWT_SECRET appears to be a weak default value")
        
        # Environment detection
        environment = os.getenv("ENVIRONMENT", "development").lower()
        debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        
        if environment == "production" and debug_mode:
            errors.append("DEBUG mode should be disabled in production")
        
        # CORS validation
        cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
        if cors_origins:
            origins = [origin.strip() for origin in cors_origins.split(",")]
            for origin in origins:
                if origin.startswith("http://") and environment == "production":
                    warnings.append(f"HTTP origin '{origin}' in production - consider HTTPS")
                if "localhost" in origin and environment == "production":
                    warnings.append(f"Localhost origin '{origin}' in production environment")
        
        return errors, warnings, recommendations
    
    def _validate_database_config(self) -> Tuple[List[str], List[str], List[str]]:
        """Validate database configuration"""
        errors = []
        warnings = []
        recommendations = []
        
        postgres_host = os.getenv("POSTGRES_HOST")
        postgres_port = os.getenv("POSTGRES_PORT", "5432")
        postgres_db = os.getenv("POSTGRES_DB")
        postgres_user = os.getenv("POSTGRES_USER")
        postgres_password = os.getenv("POSTGRES_PASSWORD")
        
        # Validate database URL construction
        if postgres_host and postgres_db and postgres_user and postgres_password:
            try:
                port = int(postgres_port)
                if port < 1 or port > 65535:
                    errors.append(f"Invalid PostgreSQL port: {postgres_port}")
            except ValueError:
                errors.append(f"PostgreSQL port must be a number: {postgres_port}")
        
        # Password strength check
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if postgres_password:
            if len(postgres_password) < 12:
                warnings.append("PostgreSQL password should be at least 12 characters")
            if postgres_password.lower() in ["password", "postgres", "admin", "root"]:
                if environment == "production":
                    errors.append("PostgreSQL password appears to be a weak default")
                else:
                    warnings.append("PostgreSQL password is weak default (consider changing for security)")
        
        # Redis configuration
        os.getenv("REDIS_HOST")
        redis_port = os.getenv("REDIS_PORT", "6379")
        
        if redis_port:
            try:
                port = int(redis_port)
                if port < 1 or port > 65535:
                    errors.append(f"Invalid Redis port: {redis_port}")
            except ValueError:
                errors.append(f"Redis port must be a number: {redis_port}")
        
        return errors, warnings, recommendations
    
    def _validate_service_endpoints(self) -> Tuple[List[str], List[str], List[str]]:
        """Validate service endpoint configurations"""
        errors = []
        warnings = []
        recommendations = []
        
        # Port validation
        os.getenv("ENVIRONMENT", "development").lower()
        ports = {
            "FRONTEND_PORT": os.getenv("FRONTEND_PORT", "4000"),
            "BACKEND_PORT": os.getenv("BACKEND_PORT", "9000"),
            "API_PORT": os.getenv("API_PORT", "9000"),
            "ADMIN_PORT": os.getenv("ADMIN_PORT", "9001")
        }
        
        used_ports = set()
        for port_name, port_value in ports.items():
            try:
                port = int(port_value)
                if port < 1000 or port > 65535:
                    warnings.append(f"{port_name} ({port}) should be in range 1000-65535")
                if port in used_ports:
                    # API_PORT and BACKEND_PORT can be the same since they're the same service
                    backend_port = int(os.getenv("BACKEND_PORT", "9000"))
                    api_port = int(os.getenv("API_PORT", "9000"))
                    
                    # Allow API_PORT and BACKEND_PORT to share the same port
                    if port == backend_port and port == api_port and port_name in ["API_PORT", "BACKEND_PORT"]:
                        pass  # This is expected - same service
                    else:
                        errors.append(f"Port conflict: {port} is used by multiple services")
                used_ports.add(port)
            except ValueError:
                errors.append(f"{port_name} must be a valid port number: {port_value}")
        
        # Host validation
        default_host = os.getenv("DEFAULT_HOST", "localhost")
        if not self._is_valid_hostname(default_host):
            errors.append(f"Invalid DEFAULT_HOST format: {default_host}")
        
        return errors, warnings, recommendations
    
    def _validate_production_readiness(self) -> Tuple[List[str], List[str], List[str]]:
        """Validate production readiness"""
        errors = []
        warnings = []
        recommendations = []
        
        environment = os.getenv("ENVIRONMENT", "development").lower()
        
        if environment == "production":
            # Production-specific validations
            
            # Check for development values
            dev_indicators = ["localhost", "127.0.0.1", "dev", "test", "local"]
            
            postgres_host = os.getenv("POSTGRES_HOST", "").lower()
            redis_host = os.getenv("REDIS_HOST", "").lower()
            
            for indicator in dev_indicators:
                if indicator in postgres_host:
                    warnings.append(f"Production database host contains '{indicator}': {postgres_host}")
                if indicator in redis_host:
                    warnings.append(f"Production Redis host contains '{indicator}': {redis_host}")
            
            # Check CORS origins
            cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
            if any(indicator in cors_origins.lower() for indicator in dev_indicators):
                warnings.append("CORS origins contain development values in production")
            
            # SSL/TLS recommendations
            if "http://" in cors_origins and environment == "production":
                recommendations.append("Consider using HTTPS for all CORS origins in production")
            
            # Resource limits
            recommendations.append("Ensure proper resource limits are configured for production deployment")
            recommendations.append("Configure proper monitoring and alerting for production environment")
            
        return errors, warnings, recommendations
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        """Check if hostname is valid"""
        if not hostname or len(hostname) > 253:
            return False
        
        # Allow localhost and IP addresses
        if hostname in ["localhost", "127.0.0.1"] or hostname.startswith("127."):
            return True
        
        # Basic hostname validation
        hostname_pattern = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$')
        return bool(hostname_pattern.match(hostname))
    
    def print_validation_report(self, result: ValidationResult) -> None:
        """Print a formatted validation report"""
        print("\n" + "="*60)
        print("🔍 CONFIGURATION VALIDATION REPORT")
        print("="*60)
        
        if result.is_valid:
            print("✅ Configuration validation PASSED")
        else:
            print("❌ Configuration validation FAILED")
        
        if result.errors:
            print(f"\n🚨 ERRORS ({len(result.errors)}):")
            for i, error in enumerate(result.errors, 1):
                print(f"  {i}. {error}")
        
        if result.warnings:
            print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
            for i, warning in enumerate(result.warnings, 1):
                print(f"  {i}. {warning}")
        
        if result.recommendations:
            print(f"\n💡 RECOMMENDATIONS ({len(result.recommendations)}):")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*60)
        
    def validate_startup(self) -> bool:
        """Validate configuration for application startup"""
        result = self.validate_all()
        
        if not result.is_valid:
            self.logger.error("Configuration validation failed - cannot start application")
            self.print_validation_report(result)
            return False
        
        if result.warnings:
            self.logger.warning(f"Configuration validation passed with {len(result.warnings)} warnings")
            for warning in result.warnings:
                self.logger.warning(f"Config warning: {warning}")
        
        self.logger.info("✅ Configuration validation successful")
        return True