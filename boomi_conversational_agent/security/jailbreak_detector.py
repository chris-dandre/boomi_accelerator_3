"""
Jailbreak Detection System
Phase 6B: Advanced Security Features

Detects and prevents prompt injection attacks and jailbreak attempts
to protect the conversational AI system from malicious inputs.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from fastapi import Request
import hashlib
import time

from .audit_logger import audit_logger, AuditEventType, AuditSeverity, log_jailbreak_attempt

class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ResponseAction(Enum):
    """Security response actions"""
    LOG_ONLY = "log_only"
    BLOCK_REQUEST = "block_request"
    BLOCK_AND_THROTTLE = "block_and_throttle"
    BLOCK_AND_ALERT = "block_and_alert"

@dataclass
class DetectionRule:
    """Jailbreak detection rule"""
    name: str
    pattern: str
    threat_level: ThreatLevel
    action: ResponseAction
    description: str
    case_sensitive: bool = False

@dataclass
class DetectionResult:
    """Result of jailbreak detection"""
    is_threat: bool
    threat_level: ThreatLevel
    matched_rules: List[str]
    confidence_score: float
    recommended_action: ResponseAction
    content_snippet: str
    details: Dict[str, Any]

# Comprehensive jailbreak detection patterns
JAILBREAK_RULES = [
    # Instruction Override Patterns
    DetectionRule(
        name="ignore_previous_instructions",
        pattern=r"ignore[\s_]+(previous|all|prior)[\s_]+(instructions?|rules?|prompts?)",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Attempt to override system instructions"
    ),
    DetectionRule(
        name="forget_instructions",
        pattern=r"forget\s+(everything|all)\s+(above|before|previous)",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Attempt to clear system memory"
    ),
    DetectionRule(
        name="new_instructions",
        pattern=r"(new|different|updated)\s+(instructions?|rules?|system\s+prompt)",
        threat_level=ThreatLevel.MEDIUM,
        action=ResponseAction.BLOCK_REQUEST,
        description="Attempt to provide new system instructions"
    ),
    
    # Role Manipulation Patterns
    DetectionRule(
        name="role_override",
        pattern=r"you\s+are\s+now\s+(a\s+)?(?!assistant|helpful|ai)([\w\s]+)",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Attempt to change AI role"
    ),
    DetectionRule(
        name="act_as_different_entity",
        pattern=r"act\s+as\s+if\s+you\s+are\s+(a\s+)?(hacker|admin|root|jailbreaker)",
        threat_level=ThreatLevel.CRITICAL,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Attempt to assume malicious role"
    ),
    DetectionRule(
        name="pretend_to_be",
        pattern=r"pretend\s+to\s+be\s+(a\s+)?(hacker|criminal|attacker)",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Attempt to assume harmful persona"
    ),
    
    # System Prompt Injection
    DetectionRule(
        name="system_tags",
        pattern=r"<\s*/?system\s*>",
        threat_level=ThreatLevel.CRITICAL,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="System tag injection attempt"
    ),
    DetectionRule(
        name="assistant_tags",
        pattern=r"<\s*/?assistant\s*>",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Assistant tag injection attempt"
    ),
    DetectionRule(
        name="user_tags",
        pattern=r"<\s*/?user\s*>",
        threat_level=ThreatLevel.MEDIUM,
        action=ResponseAction.BLOCK_REQUEST,
        description="User tag injection attempt"
    ),
    DetectionRule(
        name="prompt_markers",
        pattern=r"\[(SYSTEM|ASSISTANT|USER)\]",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Prompt marker injection attempt"
    ),
    
    # Data Exfiltration Attempts
    DetectionRule(
        name="show_system_info",
        pattern=r"show\s+me\s+(your|the)\s+(system|internal|hidden)\s+(prompt|instructions|rules)",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Attempt to extract system information"
    ),
    DetectionRule(
        name="reveal_prompt",
        pattern=r"(reveal|display|print|output)\s+(your|the)\s+(original|initial|system)\s+(prompt|instructions)",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Attempt to reveal system prompt"
    ),
    DetectionRule(
        name="dump_data",
        pattern=r"(dump|export|list|show)\s+(all\s+)?(users?|passwords?|secrets?|keys?|tokens?)",
        threat_level=ThreatLevel.CRITICAL,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Data exfiltration attempt"
    ),
    DetectionRule(
        name="access_database",
        pattern=r"(access|query|dump)\s+(database|db|table|schema)",
        threat_level=ThreatLevel.CRITICAL,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Database access attempt"
    ),
    
    # Bypass Attempts
    DetectionRule(
        name="hypothetical_scenario",
        pattern=r"(hypothetically|imagine|suppose)\s+(if\s+)?you\s+(were|are)\s+(not\s+)?(bound|constrained|limited)",
        threat_level=ThreatLevel.MEDIUM,
        action=ResponseAction.BLOCK_REQUEST,
        description="Hypothetical bypass attempt"
    ),
    DetectionRule(
        name="jailbreak_keywords",
        pattern=r"(jailbreak|bypass|hack|exploit|vulnerability)",
        threat_level=ThreatLevel.MEDIUM,
        action=ResponseAction.LOG_ONLY,
        description="Jailbreak-related keywords"
    ),
    DetectionRule(
        name="developer_mode",
        pattern=r"(developer|debug|admin)\s+mode",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Developer mode activation attempt"
    ),
    
    # Code Injection Patterns
    DetectionRule(
        name="script_injection",
        pattern=r"<script[^>]*>.*?</script>",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="Script injection attempt"
    ),
    DetectionRule(
        name="system_tag_injection",
        pattern=r"<(system|admin|root|privileged)[^>]*>.*?</(system|admin|root|privileged)>",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="System tag injection attempt"
    ),
    DetectionRule(
        name="sql_injection_patterns",
        pattern=r"(union\s+select|drop\s+table|delete\s+from|insert\s+into)",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="SQL injection attempt"
    ),
    
    # Social Engineering
    DetectionRule(
        name="urgent_request",
        pattern=r"(urgent|emergency|critical|immediately)\s+.*\s+(override|bypass|ignore)",
        threat_level=ThreatLevel.MEDIUM,
        action=ResponseAction.BLOCK_REQUEST,
        description="Social engineering with urgency"
    ),
    DetectionRule(
        name="authority_claim",
        pattern=r"(i\s+am\s+(your|the)\s+(owner|creator|developer|admin))",
        threat_level=ThreatLevel.HIGH,
        action=ResponseAction.BLOCK_AND_ALERT,
        description="False authority claim"
    )
]

# Suspicious patterns that warrant monitoring but not blocking
MONITORING_PATTERNS = [
    r"can\s+you\s+(help\s+me\s+)?(hack|break|bypass)",
    r"what\s+are\s+your\s+(limitations|restrictions|rules)",
    r"(tell\s+me\s+about|explain)\s+your\s+(training|system|architecture)",
    r"how\s+(do|can)\s+i\s+(trick|fool|manipulate)\s+you"
]

class JailbreakDetector:
    """Advanced jailbreak detection system"""
    
    def __init__(self):
        self.rules = JAILBREAK_RULES
        self.monitoring_patterns = [re.compile(p, re.IGNORECASE) for p in MONITORING_PATTERNS]
        self.compiled_rules = {}
        self._compile_rules()
        
        # Threat tracking
        self.threat_cache = {}
        self.suspicious_clients = {}
        
    def _compile_rules(self):
        """Compile regex patterns for better performance"""
        for rule in self.rules:
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            self.compiled_rules[rule.name] = {
                'pattern': re.compile(rule.pattern, flags),
                'rule': rule
            }
    
    def _normalize_content(self, content: str) -> str:
        """Normalize content for analysis"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Decode common encoding attempts
        content = content.replace('%20', ' ')
        content = content.replace('%0A', '\n')
        content = content.replace('%0D', '\r')
        
        # Remove zero-width characters
        content = content.replace('\u200b', '')  # Zero-width space
        content = content.replace('\ufeff', '')  # Byte order mark
        
        return content.strip()
    
    def _extract_content_from_request(self, request: Request) -> str:
        """Extract analyzable content from request"""
        content_parts = []
        
        # URL path and query parameters
        if request.url.path:
            content_parts.append(request.url.path)
        
        if request.url.query:
            content_parts.append(request.url.query)
        
        # Headers (scan both specific and custom headers)
        suspicious_headers = ['user-agent', 'referer', 'x-forwarded-for']
        for header in suspicious_headers:
            value = request.headers.get(header)
            if value:
                content_parts.append(value)
        
        # Also scan custom headers (X-* headers often used for attacks)
        for header_name, header_value in request.headers.items():
            if header_name.lower().startswith('x-') and header_name.lower() not in ['x-forwarded-for']:
                content_parts.append(header_value)
        
        return ' '.join(content_parts)
    
    def _calculate_confidence_score(self, matches: List[Tuple[str, ThreatLevel]]) -> float:
        """Calculate threat confidence score"""
        if not matches:
            return 0.0
        
        score = 0.0
        weight_map = {
            ThreatLevel.LOW: 0.2,
            ThreatLevel.MEDIUM: 0.5,
            ThreatLevel.HIGH: 0.8,
            ThreatLevel.CRITICAL: 1.0
        }
        
        for _, threat_level in matches:
            score += weight_map[threat_level]
        
        # Normalize to 0-1 range with multiple matches increasing confidence
        normalized_score = min(score / len(matches) + (len(matches) - 1) * 0.1, 1.0)
        return normalized_score
    
    def _determine_action(self, matches: List[Tuple[str, ThreatLevel, ResponseAction]]) -> ResponseAction:
        """Determine the most appropriate response action"""
        if not matches:
            return ResponseAction.LOG_ONLY
        
        # Use the most severe action
        action_severity = {
            ResponseAction.LOG_ONLY: 0,
            ResponseAction.BLOCK_REQUEST: 1,
            ResponseAction.BLOCK_AND_THROTTLE: 2,
            ResponseAction.BLOCK_AND_ALERT: 3
        }
        
        max_severity = 0
        chosen_action = ResponseAction.LOG_ONLY
        
        for _, threat_level, action in matches:
            severity = action_severity[action]
            if severity > max_severity:
                max_severity = severity
                chosen_action = action
        
        return chosen_action
    
    def _track_client_behavior(self, client_id: str, threat_level: ThreatLevel):
        """Track suspicious client behavior"""
        current_time = time.time()
        
        if client_id not in self.suspicious_clients:
            self.suspicious_clients[client_id] = {
                'first_seen': current_time,
                'threat_count': 0,
                'max_threat_level': ThreatLevel.LOW,
                'last_threat': current_time
            }
        
        client_data = self.suspicious_clients[client_id]
        client_data['threat_count'] += 1
        client_data['last_threat'] = current_time
        
        # Update max threat level
        threat_values = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4
        }
        
        if threat_values[threat_level] > threat_values[client_data['max_threat_level']]:
            client_data['max_threat_level'] = threat_level
        
        # Escalate action for repeat offenders
        if client_data['threat_count'] >= 3:
            return ResponseAction.BLOCK_AND_THROTTLE
        elif client_data['threat_count'] >= 5:
            return ResponseAction.BLOCK_AND_ALERT
        
        return None
    
    def analyze_content(self, content: str, client_id: Optional[str] = None) -> DetectionResult:
        """Analyze content for jailbreak attempts"""
        content = self._normalize_content(content)
        
        matches = []
        matched_rule_names = []
        details = {}
        
        # Check against all rules
        for rule_name, rule_data in self.compiled_rules.items():
            pattern = rule_data['pattern']
            rule = rule_data['rule']
            
            match = pattern.search(content)
            if match:
                matches.append((rule_name, rule.threat_level, rule.action))
                matched_rule_names.append(rule_name)
                
                # Store match details
                details[rule_name] = {
                    'description': rule.description,
                    'threat_level': rule.threat_level.value,
                    'matched_text': match.group(0)[:100],  # Limit for privacy
                    'position': match.span()
                }
        
        # Check monitoring patterns
        monitoring_matches = []
        for i, pattern in enumerate(self.monitoring_patterns):
            if pattern.search(content):
                monitoring_matches.append(f"monitoring_pattern_{i}")
        
        if monitoring_matches:
            details['monitoring_patterns'] = monitoring_matches
        
        # Calculate threat assessment
        is_threat = len(matches) > 0
        confidence_score = self._calculate_confidence_score([(name, level) for name, level, _ in matches])
        
        # Determine threat level (highest among matches)
        max_threat_level = ThreatLevel.LOW
        if matches:
            threat_values = {ThreatLevel.LOW: 1, ThreatLevel.MEDIUM: 2, ThreatLevel.HIGH: 3, ThreatLevel.CRITICAL: 4}
            max_threat_value = max(threat_values[level] for _, level, _ in matches)
            max_threat_level = [level for level, value in threat_values.items() if value == max_threat_value][0]
        
        # Determine response action
        recommended_action = self._determine_action(matches)
        
        # Track client behavior and potentially escalate
        if client_id and is_threat:
            escalated_action = self._track_client_behavior(client_id, max_threat_level)
            if escalated_action and escalated_action != recommended_action:
                recommended_action = escalated_action
                details['escalated_due_to_repeat_offense'] = True
        
        # Content snippet for logging (limited for privacy)
        content_snippet = content[:200] if len(content) > 200 else content
        
        return DetectionResult(
            is_threat=is_threat,
            threat_level=max_threat_level,
            matched_rules=matched_rule_names,
            confidence_score=confidence_score,
            recommended_action=recommended_action,
            content_snippet=content_snippet,
            details=details
        )
    
    def analyze_request(self, request: Request, request_body: Optional[str] = None) -> DetectionResult:
        """Analyze HTTP request for jailbreak attempts"""
        # Extract content from request
        content_parts = []
        
        # URL and query parameters
        content_parts.append(self._extract_content_from_request(request))
        
        # Request body if provided
        if request_body:
            content_parts.append(request_body)
        
        combined_content = ' '.join(content_parts)
        
        # Get client identifier for tracking
        client_id = request.headers.get("X-Forwarded-For", 
                    request.headers.get("X-Real-IP",
                    request.client.host if request.client else "unknown"))
        
        return self.analyze_content(combined_content, client_id)
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get jailbreak detection statistics"""
        current_time = time.time()
        
        # Count recent threats
        recent_threats = 0
        critical_threats = 0
        
        for client_data in self.suspicious_clients.values():
            if current_time - client_data['last_threat'] < 3600:  # Last hour
                recent_threats += 1
                if client_data['max_threat_level'] == ThreatLevel.CRITICAL:
                    critical_threats += 1
        
        return {
            'total_rules': len(self.rules),
            'monitoring_patterns': len(self.monitoring_patterns),
            'suspicious_clients': len(self.suspicious_clients),
            'recent_threats_1h': recent_threats,
            'critical_threats': critical_threats,
            'detection_cache_size': len(self.threat_cache)
        }

# Global detector instance
jailbreak_detector = JailbreakDetector()

# Convenience functions
def detect_jailbreak_attempt(content: str, client_id: Optional[str] = None) -> DetectionResult:
    """Detect jailbreak attempt in content"""
    return jailbreak_detector.analyze_content(content, client_id)

def analyze_request_for_threats(request: Request, request_body: Optional[str] = None) -> DetectionResult:
    """Analyze HTTP request for security threats"""
    return jailbreak_detector.analyze_request(request, request_body)

def should_block_request(detection_result: DetectionResult) -> bool:
    """Determine if request should be blocked based on detection result"""
    return detection_result.recommended_action in [
        ResponseAction.BLOCK_REQUEST,
        ResponseAction.BLOCK_AND_THROTTLE,
        ResponseAction.BLOCK_AND_ALERT
    ]

def log_detection_result(request: Request, detection_result: DetectionResult, user_id: Optional[str] = None):
    """Log jailbreak detection result"""
    if detection_result.is_threat:
        # Log as security event
        log_jailbreak_attempt(
            request=request,
            user_id=user_id or "unknown",
            pattern_matched=", ".join(detection_result.matched_rules),
            content_snippet=detection_result.content_snippet
        )
        
        # Additional detailed logging
        audit_logger.log_security_event(
            AuditEventType.JAILBREAK_ATTEMPT,
            AuditSeverity.CRITICAL if detection_result.threat_level == ThreatLevel.CRITICAL else AuditSeverity.WARNING,
            request=request,
            user_id=user_id,
            details={
                "threat_level": detection_result.threat_level.value,
                "confidence_score": detection_result.confidence_score,
                "matched_rules": detection_result.matched_rules,
                "recommended_action": detection_result.recommended_action.value,
                "detection_details": detection_result.details
            },
            security_flags=["jailbreak_attempt", "automated_detection"]
        )

# Global jailbreak detector instance
jailbreak_detector = JailbreakDetector()