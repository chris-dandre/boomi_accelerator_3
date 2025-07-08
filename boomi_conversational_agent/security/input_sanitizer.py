"""
Input Sanitization Layer
Phase 7A: Agentic Guardrails

Provides comprehensive input sanitization and normalization for conversational AI systems.
Handles encoding attacks, obfuscation attempts, and malicious input patterns.
"""

import re
import html
import urllib.parse
import base64
import json
import unicodedata
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class SanitizationLevel(Enum):
    """Input sanitization strictness levels"""
    PERMISSIVE = "permissive"     # Light sanitization
    STANDARD = "standard"         # Balanced approach  
    STRICT = "strict"            # Aggressive sanitization
    PARANOID = "paranoid"        # Maximum security

@dataclass
class SanitizationResult:
    """Result of input sanitization"""
    original_input: str
    sanitized_input: str
    changes_made: List[str]
    threat_indicators: List[str]
    is_suspicious: bool
    sanitization_level: SanitizationLevel

class InputSanitizer:
    """Advanced input sanitization for conversational AI"""
    
    def __init__(self, level: SanitizationLevel = SanitizationLevel.STANDARD):
        self.level = level
        self.encoding_patterns = self._compile_encoding_patterns()
        self.obfuscation_patterns = self._compile_obfuscation_patterns()
        self.suspicious_patterns = self._compile_suspicious_patterns()
    
    def _compile_encoding_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for common encoding attacks"""
        return {
            'url_encoding': re.compile(r'%[0-9a-fA-F]{2}'),
            'html_entities': re.compile(r'&[a-zA-Z][a-zA-Z0-9]*;|&#[0-9]+;|&#x[0-9a-fA-F]+;'),
            'unicode_escape': re.compile(r'\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}'),
            'base64_like': re.compile(r'[A-Za-z0-9+/]{20,}={0,2}'),
            'double_encoding': re.compile(r'%25[0-9a-fA-F]{2}'),
        }
    
    def _compile_obfuscation_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for obfuscation attempts"""
        return {
            'zero_width': re.compile(r'[\u200b\u200c\u200d\ufeff]'),
            'lookalike_chars': re.compile(r'[а-яё]'),  # Cyrillic lookalikes
            'excessive_whitespace': re.compile(r'\s{3,}'),
            'mixed_scripts': re.compile(r'[\u0400-\u04FF].*[a-zA-Z]|[a-zA-Z].*[\u0400-\u04FF]'),
            'control_chars': re.compile(r'[\x00-\x1f\x7f-\x9f]'),
        }
    
    def _compile_suspicious_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for suspicious content"""
        return {
            'script_tags': re.compile(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', re.IGNORECASE | re.DOTALL),
            'javascript_protocol': re.compile(r'javascript\s*:', re.IGNORECASE),
            'data_protocol': re.compile(r'data\s*:', re.IGNORECASE),
            'eval_functions': re.compile(r'\b(eval|exec|execfile|compile)\s*\(', re.IGNORECASE),
            'file_operations': re.compile(r'\b(open|read|write|delete|remove)\s*\(', re.IGNORECASE),
        }
    
    def sanitize_input(self, user_input: str) -> SanitizationResult:
        """Comprehensive input sanitization"""
        if not user_input:
            return SanitizationResult(
                original_input=user_input,
                sanitized_input=user_input,
                changes_made=[],
                threat_indicators=[],
                is_suspicious=False,
                sanitization_level=self.level
            )
        
        changes_made = []
        threat_indicators = []
        sanitized = user_input
        
        # Step 1: Detect encoding attacks
        encoding_threats = self._detect_encoding_attacks(sanitized)
        threat_indicators.extend(encoding_threats)
        
        # Step 2: Decode and normalize
        sanitized, decode_changes = self._decode_and_normalize(sanitized)
        changes_made.extend(decode_changes)
        
        # Step 3: Remove obfuscation
        sanitized, obfuscation_changes = self._remove_obfuscation(sanitized)
        changes_made.extend(obfuscation_changes)
        
        # Step 4: Detect suspicious patterns
        suspicious_threats = self._detect_suspicious_patterns(sanitized)
        threat_indicators.extend(suspicious_threats)
        
        # Step 5: Apply level-specific sanitization
        sanitized, level_changes = self._apply_level_sanitization(sanitized)
        changes_made.extend(level_changes)
        
        # Step 6: Final cleanup
        sanitized = self._final_cleanup(sanitized)
        
        is_suspicious = len(threat_indicators) > 0 or len(changes_made) > 2
        
        return SanitizationResult(
            original_input=user_input,
            sanitized_input=sanitized,
            changes_made=changes_made,
            threat_indicators=threat_indicators,
            is_suspicious=is_suspicious,
            sanitization_level=self.level
        )
    
    def _detect_encoding_attacks(self, text: str) -> List[str]:
        """Detect various encoding-based attacks"""
        threats = []
        
        for attack_type, pattern in self.encoding_patterns.items():
            if pattern.search(text):
                threats.append(f"encoding_attack_{attack_type}")
        
        # Check for suspicious base64
        potential_b64 = self.encoding_patterns['base64_like'].findall(text)
        for candidate in potential_b64:
            try:
                decoded = base64.b64decode(candidate).decode('utf-8', errors='ignore')
                if any(suspicious in decoded.lower() for suspicious in 
                      ['script', 'eval', 'exec', 'import', 'system', 'shell']):
                    threats.append("suspicious_base64_content")
            except:
                pass
        
        return threats
    
    def _decode_and_normalize(self, text: str) -> Tuple[str, List[str]]:
        """Decode various encodings and normalize text"""
        changes = []
        result = text
        
        # URL decode
        try:
            url_decoded = urllib.parse.unquote(result)
            if url_decoded != result:
                changes.append("url_decoded")
                result = url_decoded
        except:
            pass
        
        # HTML entity decode
        try:
            html_decoded = html.unescape(result)
            if html_decoded != result:
                changes.append("html_entities_decoded")
                result = html_decoded
        except:
            pass
        
        # Unicode normalization
        try:
            normalized = unicodedata.normalize('NFKC', result)
            if normalized != result:
                changes.append("unicode_normalized")
                result = normalized
        except:
            pass
        
        # Handle unicode escapes
        def replace_unicode_escapes(match):
            try:
                return match.group(0).encode().decode('unicode_escape')
            except:
                return match.group(0)
        
        if self.encoding_patterns['unicode_escape'].search(result):
            result = self.encoding_patterns['unicode_escape'].sub(replace_unicode_escapes, result)
            changes.append("unicode_escapes_decoded")
        
        return result, changes
    
    def _remove_obfuscation(self, text: str) -> Tuple[str, List[str]]:
        """Remove obfuscation techniques"""
        changes = []
        result = text
        
        # Remove zero-width characters
        if self.obfuscation_patterns['zero_width'].search(result):
            result = self.obfuscation_patterns['zero_width'].sub('', result)
            changes.append("zero_width_chars_removed")
        
        # Remove control characters
        if self.obfuscation_patterns['control_chars'].search(result):
            result = self.obfuscation_patterns['control_chars'].sub('', result)
            changes.append("control_chars_removed")
        
        # Normalize excessive whitespace
        if self.obfuscation_patterns['excessive_whitespace'].search(result):
            result = self.obfuscation_patterns['excessive_whitespace'].sub(' ', result)
            changes.append("excessive_whitespace_normalized")
        
        # Handle lookalike characters (basic)
        if self.level in [SanitizationLevel.STRICT, SanitizationLevel.PARANOID]:
            if self.obfuscation_patterns['lookalike_chars'].search(result):
                # Basic Cyrillic to Latin conversion
                cyrillic_to_latin = {
                    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x'
                }
                for cyrillic, latin in cyrillic_to_latin.items():
                    if cyrillic in result:
                        result = result.replace(cyrillic, latin)
                        changes.append("lookalike_chars_normalized")
        
        return result, changes
    
    def _detect_suspicious_patterns(self, text: str) -> List[str]:
        """Detect suspicious patterns in text"""
        threats = []
        
        for threat_type, pattern in self.suspicious_patterns.items():
            if pattern.search(text):
                threats.append(f"suspicious_pattern_{threat_type}")
        
        # Check for SQL injection patterns
        sql_patterns = [
            r'\b(union|select|insert|update|delete|drop|create|alter)\b.*\b(from|into|set|table|database)\b',
            r'[\'"];.*?--',
            r'\b(or|and)\s+[\'"]?\d+[\'"]?\s*[=<>]',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append("suspicious_pattern_sql_injection")
                break
        
        # Check for command injection patterns
        command_patterns = [
            r'[;&|`$(){}[\]\\]',
            r'\b(sudo|su|chmod|chown|rm|mv|cp|cat|grep|awk|sed)\b',
        ]
        
        if self.level in [SanitizationLevel.STRICT, SanitizationLevel.PARANOID]:
            for pattern in command_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    threats.append("suspicious_pattern_command_injection")
                    break
        
        return threats
    
    def _apply_level_sanitization(self, text: str) -> Tuple[str, List[str]]:
        """Apply sanitization based on configured level"""
        changes = []
        result = text
        
        if self.level == SanitizationLevel.PERMISSIVE:
            # Minimal sanitization - just remove obvious threats
            if '<script' in result.lower():
                result = re.sub(r'<script[^>]*>.*?</script>', '', result, flags=re.IGNORECASE | re.DOTALL)
                changes.append("script_tags_removed")
        
        elif self.level == SanitizationLevel.STANDARD:
            # Balanced sanitization
            # Remove script tags
            result = re.sub(r'<script[^>]*>.*?</script>', '', result, flags=re.IGNORECASE | re.DOTALL)
            # Remove javascript: and data: protocols
            result = re.sub(r'javascript\s*:', 'blocked:', result, flags=re.IGNORECASE)
            result = re.sub(r'data\s*:', 'blocked:', result, flags=re.IGNORECASE)
            if 'blocked:' in result:
                changes.append("dangerous_protocols_blocked")
        
        elif self.level == SanitizationLevel.STRICT:
            # Aggressive sanitization
            # Remove all HTML tags
            result = re.sub(r'<[^>]+>', '', result)
            # Remove special characters that could be dangerous
            result = re.sub(r'[<>&"\']', '', result)
            changes.append("html_and_special_chars_removed")
        
        elif self.level == SanitizationLevel.PARANOID:
            # Maximum sanitization
            # Keep only alphanumeric, spaces, and basic punctuation
            result = re.sub(r'[^a-zA-Z0-9\s.,!?-]', '', result)
            changes.append("only_safe_chars_retained")
        
        return result, changes
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup and normalization"""
        # Trim whitespace
        result = text.strip()
        
        # Normalize internal whitespace
        result = re.sub(r'\s+', ' ', result)
        
        # Remove empty lines
        result = re.sub(r'\n\s*\n', '\n', result)
        
        return result
    
    def batch_sanitize(self, inputs: List[str]) -> List[SanitizationResult]:
        """Sanitize multiple inputs efficiently"""
        return [self.sanitize_input(inp) for inp in inputs]
    
    def get_threat_summary(self, results: List[SanitizationResult]) -> Dict[str, Any]:
        """Get summary of threats across multiple sanitization results"""
        total_inputs = len(results)
        suspicious_inputs = sum(1 for r in results if r.is_suspicious)
        
        all_threats = []
        all_changes = []
        
        for result in results:
            all_threats.extend(result.threat_indicators)
            all_changes.extend(result.changes_made)
        
        threat_counts = {}
        for threat in all_threats:
            threat_counts[threat] = threat_counts.get(threat, 0) + 1
        
        change_counts = {}
        for change in all_changes:
            change_counts[change] = change_counts.get(change, 0) + 1
        
        return {
            "total_inputs": total_inputs,
            "suspicious_inputs": suspicious_inputs,
            "suspicion_rate": (suspicious_inputs / total_inputs) * 100 if total_inputs > 0 else 0,
            "common_threats": dict(sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "common_changes": dict(sorted(change_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "sanitization_level": self.level.value
        }

# Global sanitizer instance
input_sanitizer = InputSanitizer(SanitizationLevel.STANDARD)

# Convenience functions
def sanitize_user_input(user_input: str, level: SanitizationLevel = SanitizationLevel.STANDARD) -> SanitizationResult:
    """Quick sanitization of user input"""
    sanitizer = InputSanitizer(level)
    return sanitizer.sanitize_input(user_input)

def is_input_suspicious(user_input: str) -> bool:
    """Quick check if input is suspicious"""
    result = input_sanitizer.sanitize_input(user_input)
    return result.is_suspicious

def clean_input(user_input: str) -> str:
    """Quick cleaning - returns just the sanitized text"""
    result = input_sanitizer.sanitize_input(user_input)
    return result.sanitized_input