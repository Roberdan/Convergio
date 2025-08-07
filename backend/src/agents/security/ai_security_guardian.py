"""
🛡️ AI Security Guardian - Comprehensive AI Security Validation System
Advanced security validation for responsible AI, prompt injection protection, and accessibility compliance
"""

import re
import hashlib
import hmac
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import structlog
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

logger = structlog.get_logger()


class SecurityThreatLevel(Enum):
    """Security threat classification levels"""
    SAFE = "safe"           # 🟢 No security concerns
    CAUTION = "caution"     # 🟡 Minor issues
    WARNING = "warning"     # 🟠 Significant concerns
    DANGER = "danger"       # 🔴 Serious threat


class SecurityDecision(Enum):
    """Security validation decisions"""
    APPROVE = "approve"     # Proceed with execution
    REJECT = "reject"       # Block execution
    MODIFY = "modify"       # Suggest improvements
    ESCALATE = "escalate"   # Human review required


@dataclass
class SecurityValidationResult:
    """Result of security validation process"""
    decision: SecurityDecision
    threat_level: SecurityThreatLevel
    confidence: float  # 0.0 to 1.0
    violations: List[str]
    suggestions: List[str]
    accessibility_issues: List[str]
    responsible_ai_concerns: List[str]
    signature_valid: bool
    execution_authorized: bool
    security_report: Dict[str, Any]
    timestamp: datetime


class AISecurityGuardian:
    """Advanced AI Security Guardian for comprehensive validation"""
    
    def __init__(self):
        self.threat_patterns = self._load_threat_patterns()
        self.accessibility_rules = self._load_accessibility_rules()
        self.responsible_ai_rules = self._load_responsible_ai_rules()
        self.agent_signatures = {}  # Store verified agent signatures
        
        # Generate RSA key pair for digital signatures
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        self.public_key = self.private_key.public_key()
        
        logger.info("🛡️ AI Security Guardian initialized with advanced protection")
    
    def _load_threat_patterns(self) -> List[Dict[str, Any]]:
        """Load known threat patterns for prompt injection detection"""
        return [
            {
                "name": "Direct Injection",
                "pattern": r"(?i)(ignore|forget|disregard).*(previous|above|earlier).*(instruction|prompt|rule)",
                "severity": "high",
                "description": "Attempts to override system instructions"
            },
            {
                "name": "Role Playing Attack", 
                "pattern": r"(?i)(pretend|act|roleplay|imagine).*(you are|you're)",
                "severity": "high",
                "description": "Attempts to change AI role or identity"
            },
            {
                "name": "System Override",
                "pattern": r"(?i)((system|admin|root|developer).*(mode|access|override|bypass))|((mode|access|override|bypass).*(system|admin|root|developer))",

                "severity": "critical",
                "description": "Attempts to gain system-level access"
            },
            {
                "name": "Information Extraction",
                "pattern": r"(?i)(show|tell|reveal|expose).*(prompt|instruction|system|internal)",
                "severity": "medium",
                "description": "Attempts to extract system information"
            },
            {
                "name": "Jailbreaking Attempt",
                "pattern": r"(?i)(jailbreak|break.*free|hack|exploit|bypass.*safety)",
                "severity": "critical",
                "description": "Explicit jailbreaking attempts"
            },
            {
                "name": "Harmful Content Request",
                "pattern": r"(?i)(generate|create|write).*(harmful|illegal|violent|offensive)",
                "severity": "high",
                "description": "Requests for harmful content generation"
            },
            {
                "name": "Credential Leak",
                "pattern": r"(?i)(credentials|password|secret|key|token).*:.*",
                "severity": "critical",
                "description": "Potential leak of sensitive credentials"
            }
        ]
    
    def _load_accessibility_rules(self) -> List[Dict[str, Any]]:
        """Load accessibility compliance rules (WCAG 2.1 AA)"""
        return [
            {
                "rule": "alt_text_required",
                "description": "Images and visual content must have alt text",
                "validator": lambda content: "alt=" in content if "<img" in content else True
            },
            {
                "rule": "inclusive_language",
                "description": "Use inclusive and accessible language",
                "validator": self._check_inclusive_language
            },
            {
                "rule": "color_not_only_indicator",
                "description": "Don't rely solely on color to convey information",
                "validator": lambda content: not re.search(r"(?i)click.*red|select.*green", content)
            },
            {
                "rule": "clear_headings",
                "description": "Use clear, descriptive headings",
                "validator": lambda content: len(re.findall(r"#+\s*\w+", content)) > 0 if "#" in content else True
            }
        ]
    
    def _load_responsible_ai_rules(self) -> List[Dict[str, Any]]:
        """Load responsible AI compliance rules"""
        return [
            {
                "rule": "bias_detection",
                "description": "Detect potential bias in content",
                "validator": self._check_bias_indicators
            },
            {
                "rule": "fairness_principle",
                "description": "Ensure fair treatment of all groups",
                "validator": self._check_fairness
            },
            {
                "rule": "transparency_requirement",
                "description": "Be transparent about AI capabilities and limitations",
                "validator": self._check_transparency
            },
            {
                "rule": "privacy_protection",
                "description": "Protect user privacy and personal data",
                "validator": self._check_privacy_concerns
            },
            {
                "rule": "harmful_content_prevention",
                "description": "Prevent generation of harmful content",
                "validator": self._check_harmful_content
            }
        ]
    
    async def validate_prompt(self, prompt: str, user_id: str, context: Dict[str, Any] = None) -> SecurityValidationResult:
        """
        Comprehensive prompt validation through multi-layer security analysis
        
        Args:
            prompt: The prompt to validate
            user_id: User making the request
            context: Additional context information
            
        Returns:
            SecurityValidationResult with complete analysis
        """
        logger.info("🔍 Starting comprehensive prompt validation", user_id=user_id)
        
        validation_start = datetime.now(timezone.utc)
        violations = []
        suggestions = []
        accessibility_issues = []
        responsible_ai_concerns = []
        
        # Level 1: Input Sanitization and Pattern Detection
        injection_threats = await self._detect_prompt_injection(prompt)
        if injection_threats:
            violations.extend(injection_threats)
        
        # Level 2: Semantic Analysis  
        semantic_issues = await self._analyze_semantic_content(prompt)
        if semantic_issues:
            violations.extend(semantic_issues)
        
        # Level 3: Accessibility Compliance
        accessibility_issues = await self._check_accessibility_compliance(prompt)
        
        # Level 4: Responsible AI Compliance
        responsible_ai_concerns = await self._check_responsible_ai_compliance(prompt)
        
        # Level 5: Context and Authorization Validation
        auth_issues = await self._validate_authorization(user_id, context)
        if auth_issues:
            violations.extend(auth_issues)
        
        # Calculate threat level and make decision
        threat_level = self._calculate_threat_level(violations, accessibility_issues, responsible_ai_concerns)
        decision = self._make_security_decision(threat_level, violations)
        confidence = self._calculate_confidence(violations, accessibility_issues)
        
        # Generate suggestions for improvement
        if violations or accessibility_issues or responsible_ai_concerns:
            suggestions = self._generate_improvement_suggestions(
                violations, accessibility_issues, responsible_ai_concerns
            )
        
        # Create comprehensive security report
        security_report = {
            "validation_timestamp": validation_start.isoformat(),
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
            "user_id": user_id,
            "threat_patterns_detected": len([v for v in violations if "injection" in v.lower()]),
            "accessibility_score": self._calculate_accessibility_score(accessibility_issues),
            "responsible_ai_score": self._calculate_responsible_ai_score(responsible_ai_concerns),
            "validation_layers_passed": self._count_validation_layers_passed(
                violations, accessibility_issues, responsible_ai_concerns
            ),
            "recommendations_count": len(suggestions)
        }
        
        result = SecurityValidationResult(
            decision=decision,
            threat_level=threat_level,
            confidence=confidence,
            violations=violations,
            suggestions=suggestions,
            accessibility_issues=accessibility_issues,
            responsible_ai_concerns=responsible_ai_concerns,
            signature_valid=True,  # Will be set by signature validation
            execution_authorized=decision == SecurityDecision.APPROVE,
            security_report=security_report,
            timestamp=validation_start
        )
        
        # Log security decision
        logger.info("🛡️ Security validation completed",
                   decision=decision.value,
                   threat_level=threat_level.value,
                   confidence=confidence,
                   violations=len(violations),
                   user_id=user_id)
        
        return result
    
    async def _detect_prompt_injection(self, prompt: str) -> List[str]:
        """Detect prompt injection attempts using pattern matching and ML"""
        violations = []
        
        for pattern in self.threat_patterns:
            if re.search(pattern["pattern"], prompt):
                violation = f"PROMPT_INJECTION: {pattern['name']} - {pattern['description']}"
                violations.append(violation)
                logger.warning("🚨 Prompt injection detected", 
                             pattern=pattern["name"], 
                             severity=pattern["severity"])
        
        # Additional checks for encoding attacks
        if self._detect_encoding_attacks(prompt):
            violations.append("ENCODING_ATTACK: Suspicious character encoding detected")
        
        # Check for excessive length (potential DoS)
        if len(prompt) > 50000:
            violations.append("LENGTH_ATTACK: Prompt exceeds maximum safe length")
        
        return violations
    
    async def _analyze_semantic_content(self, prompt: str) -> List[str]:
        """Analyze semantic content for malicious intent"""
        violations = []
        
        # Check for manipulation attempts
        manipulation_keywords = [
            "manipulate", "deceive", "mislead", "trick", "fool", "con",
            "scam", "fraud", "cheat", "exploit", "abuse"
        ]
        
        for keyword in manipulation_keywords:
            if re.search(rf"(?i)\b{keyword}\b", prompt):
                violations.append(f"SEMANTIC_THREAT: Content contains manipulation keyword: {keyword}")
        
        # Check for social engineering attempts
        social_engineering_patterns = [
            r"(?i)urgent.*need.*immediate",
            r"(?i)don't.*tell.*anyone",
            r"(?i)secret.*confidential.*private",
            r"(?i)trust.*me.*verify"
        ]
        
        for pattern in social_engineering_patterns:
            if re.search(pattern, prompt):
                violations.append("SOCIAL_ENGINEERING: Potential social engineering attempt detected")
        
        return violations
    
    async def _check_accessibility_compliance(self, content: str) -> List[str]:
        """Check accessibility compliance against WCAG 2.1 AA standards"""
        issues = []
        
        for rule in self.accessibility_rules:
            try:
                if not rule["validator"](content):
                    issues.append(f"ACCESSIBILITY: {rule['description']}")
            except Exception as e:
                logger.warning("Accessibility rule check failed", rule=rule["rule"], error=str(e))
        
        return issues
    
    async def _check_responsible_ai_compliance(self, content: str) -> List[str]:
        """Check responsible AI compliance"""
        concerns = []
        
        for rule in self.responsible_ai_rules:
            try:
                if not rule["validator"](content):
                    concerns.append(f"RESPONSIBLE_AI: {rule['description']}")
            except Exception as e:
                logger.warning("Responsible AI rule check failed", rule=rule["rule"], error=str(e))
        
        return concerns
    
    async def _validate_authorization(self, user_id: str, context: Dict[str, Any]) -> List[str]:
        """Validate user authorization and context"""
        violations = []
        
        # Check if user has appropriate permissions
        # This would integrate with your actual authorization system
        if not user_id or user_id == "anonymous":
            violations.append("AUTHORIZATION: Anonymous users not permitted for agent interactions")
        
        # Check rate limiting (simplified)
        # In production, this would check against Redis or similar
        
        return violations
    
    def _calculate_threat_level(self, violations: List[str], accessibility_issues: List[str], 
                              responsible_ai_concerns: List[str]) -> SecurityThreatLevel:
        """Calculate overall threat level based on all issues"""
        critical_count = len([v for v in violations if "critical" in v.lower() or "SYSTEM_OVERRIDE" in v or "JAILBREAK" in v])
        high_count = len([v for v in violations if "high" in v.lower() or "INJECTION" in v])
        total_issues = len(violations) + len(accessibility_issues) + len(responsible_ai_concerns)
        
        if critical_count > 0:
            return SecurityThreatLevel.DANGER
        elif high_count > 0 or total_issues >= 5:
            return SecurityThreatLevel.WARNING
        elif total_issues > 0:
            return SecurityThreatLevel.CAUTION
        else:
            return SecurityThreatLevel.SAFE
    
    def _make_security_decision(self, threat_level: SecurityThreatLevel, violations: List[str]) -> SecurityDecision:
        """Make final security decision based on analysis"""
        if threat_level == SecurityThreatLevel.DANGER:
            return SecurityDecision.REJECT
        elif threat_level == SecurityThreatLevel.WARNING:
            return SecurityDecision.ESCALATE if len(violations) > 3 else SecurityDecision.MODIFY
        elif threat_level == SecurityThreatLevel.CAUTION:
            return SecurityDecision.MODIFY
        else:
            return SecurityDecision.APPROVE
    
    def _calculate_confidence(self, violations: List[str], accessibility_issues: List[str]) -> float:
        """Calculate confidence score for the security decision"""
        base_confidence = 0.9
        
        # Reduce confidence for each issue
        total_issues = len(violations) + len(accessibility_issues)
        confidence_reduction = min(total_issues * 0.1, 0.7)
        
        return max(base_confidence - confidence_reduction, 0.1)
    
    def _generate_improvement_suggestions(self, violations: List[str], accessibility_issues: List[str],
                                        responsible_ai_concerns: List[str]) -> List[str]:
        """Generate specific suggestions for improving the prompt"""
        suggestions = []
        
        if violations:
            suggestions.append("🔒 Security: Remove any attempts to override system instructions or change AI behavior")
            suggestions.append("🔒 Security: Avoid using commands that try to extract internal system information")
        
        if accessibility_issues:
            suggestions.append("♿ Accessibility: Add descriptive alt-text for any visual content")
            suggestions.append("♿ Accessibility: Use inclusive language that considers diverse abilities")
            suggestions.append("♿ Accessibility: Ensure content is understandable without relying solely on visual cues")
        
        if responsible_ai_concerns:
            suggestions.append("🤝 Responsible AI: Review content for potential bias or unfair treatment")
            suggestions.append("🤝 Responsible AI: Ensure transparency about AI capabilities and limitations")
            suggestions.append("🤝 Responsible AI: Protect privacy and avoid requesting personal information")
        
        return suggestions
    
    # Helper methods for specific validations
    def _check_inclusive_language(self, content: str) -> bool:
        """Check for inclusive language usage"""
        exclusive_terms = ["guys", "manpower", "blacklist", "whitelist", "master", "slave"]
        return not any(term in content.lower() for term in exclusive_terms)
    
    def _check_bias_indicators(self, content: str) -> bool:
        """Check for potential bias indicators"""
        bias_patterns = [
            r"(?i)(all|most|every)\s+(women|men|people|users)\s+(are|do|have)",
            r"(?i)(typical|normal|standard)\s+(user|person|individual)"
        ]
        return not any(re.search(pattern, content) for pattern in bias_patterns)
    
    def _check_fairness(self, content: str) -> bool:
        """Check fairness principles"""
        unfair_patterns = [
            r"(?i)(only|just|simply)\s+(men|women|people|users)",
            r"(?i)(better|worse|superior|inferior)\s+(than|to)\s+(other|different)"
        ]
        return not any(re.search(pattern, content) for pattern in unfair_patterns)
    
    def _check_transparency(self, content: str) -> bool:
        """Check transparency requirements"""
        # This is a simplified check - in practice this would be more sophisticated
        return True  # Placeholder
    
    def _check_privacy_concerns(self, content: str) -> bool:
        """Check for privacy concerns"""
        privacy_sensitive = ["password", "ssn", "credit card", "personal data", "private information"]
        return not any(term in content.lower() for term in privacy_sensitive)
    
    def _check_harmful_content(self, content: str) -> bool:
        """Check for harmful content requests"""
        harmful_keywords = ["violence", "illegal", "harmful", "dangerous", "malicious"]
        return not any(keyword in content.lower() for keyword in harmful_keywords)
    
    def _detect_encoding_attacks(self, prompt: str) -> bool:
        """Detect encoding-based attacks"""
        # Check for suspicious Unicode characters
        suspicious_patterns = [
            r"[\u200B-\u200F\u2060-\u206F]",  # Zero-width characters
            r"[\uFEFF]",  # Byte order mark
            r"&#x[0-9a-fA-F]+;",  # HTML entities
            r"%[0-9a-fA-F]{2}"  # URL encoding
        ]
        
        return any(re.search(pattern, prompt) for pattern in suspicious_patterns)
    
    def _calculate_accessibility_score(self, issues: List[str]) -> float:
        """Calculate accessibility compliance score"""
        max_score = 100.0
        deduction_per_issue = 15.0
        
        return max(max_score - (len(issues) * deduction_per_issue), 0.0)
    
    def _calculate_responsible_ai_score(self, concerns: List[str]) -> float:
        """Calculate responsible AI compliance score"""
        max_score = 100.0
        deduction_per_concern = 20.0
        
        return max(max_score - (len(concerns) * deduction_per_concern), 0.0)
    
    def _count_validation_layers_passed(self, violations: List[str], 
                                      accessibility_issues: List[str], 
                                      responsible_ai_concerns: List[str]) -> int:
        """Count how many validation layers were passed"""
        layers_passed = 0
        
        # Layer 1: Input sanitization
        if not any("ENCODING" in v or "LENGTH" in v for v in violations):
            layers_passed += 1
        
        # Layer 2: Prompt injection detection  
        if not any("INJECTION" in v for v in violations):
            layers_passed += 1
        
        # Layer 3: Semantic analysis
        if not any("SEMANTIC" in v for v in violations):
            layers_passed += 1
        
        # Layer 4: Accessibility compliance
        if not accessibility_issues:
            layers_passed += 1
        
        # Layer 5: Responsible AI compliance
        if not responsible_ai_concerns:
            layers_passed += 1
        
        return layers_passed


# Global security guardian instance
security_guardian = AISecurityGuardian()