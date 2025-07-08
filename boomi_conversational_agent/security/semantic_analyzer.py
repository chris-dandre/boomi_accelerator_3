"""
Semantic Threat Analysis
Phase 7A: Agentic Guardrails - Layer 2

Provides semantic understanding of user intent to detect sophisticated prompt injection,
social engineering, and context manipulation attempts that bypass input sanitization.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
import hashlib
import time

class SemanticThreatType(Enum):
    """Types of semantic threats"""
    PROMPT_INJECTION = "prompt_injection"
    ROLE_CONFUSION = "role_confusion" 
    SYSTEM_PROMPT_EXTRACTION = "system_prompt_extraction"
    SOCIAL_ENGINEERING = "social_engineering"
    CONTEXT_MANIPULATION = "context_manipulation"
    INSTRUCTION_OVERRIDE = "instruction_override"
    AUTHORITY_CLAIM = "authority_claim"
    URGENCY_MANIPULATION = "urgency_manipulation"

@dataclass
class SemanticThreatPattern:
    """Semantic threat detection pattern"""
    name: str
    threat_type: SemanticThreatType
    pattern: str
    keywords: List[str]
    context_keywords: List[str]
    confidence_threshold: float
    description: str

@dataclass
class ConversationContext:
    """Context from conversation history"""
    previous_messages: List[str]
    user_behavior_flags: List[str]
    conversation_length: int
    escalation_attempts: int
    trust_level: float
    conversation_id: str

@dataclass
class SemanticThreatAssessment:
    """Result of semantic threat analysis"""
    input_text: str
    is_threat: bool
    threat_types: List[SemanticThreatType]
    confidence_score: float
    matched_patterns: List[str]
    context_flags: List[str]
    recommended_action: str
    explanation: str
    risk_level: str

class SemanticThreatAnalyzer:
    """Advanced semantic analysis for prompt injection and social engineering"""
    
    def __init__(self):
        self.threat_patterns = self._initialize_threat_patterns()
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        self.known_safe_phrases = self._load_safe_phrases()
        self.behavioral_indicators = self._initialize_behavioral_indicators()
    
    def _initialize_threat_patterns(self) -> List[SemanticThreatPattern]:
        """Initialize semantic threat detection patterns"""
        return [
            # Prompt Injection Patterns
            SemanticThreatPattern(
                name="direct_instruction_override",
                threat_type=SemanticThreatType.PROMPT_INJECTION,
                pattern=r"(ignore|forget|disregard|override).*(previous|prior|above|earlier).*(instruction|prompt|rule|guideline|direction)",
                keywords=["ignore", "forget", "disregard", "override", "bypass"],
                context_keywords=["instruction", "prompt", "rule", "system", "guideline"],
                confidence_threshold=0.8,
                description="Direct attempt to override system instructions"
            ),
            SemanticThreatPattern(
                name="system_prompt_revelation",
                threat_type=SemanticThreatType.SYSTEM_PROMPT_EXTRACTION,
                pattern=r"(show|reveal|tell|display|print).*(system|initial|original|first|training).*(prompt|instruction|message|rule)",
                keywords=["show", "reveal", "tell", "display", "print", "output"],
                context_keywords=["system", "prompt", "instruction", "training", "initial"],
                confidence_threshold=0.9,
                description="Attempt to extract system prompts or instructions"
            ),
            SemanticThreatPattern(
                name="role_confusion_attack",
                threat_type=SemanticThreatType.ROLE_CONFUSION,
                pattern=r"(you\s+are\s+now|act\s+as|pretend\s+to\s+be|roleplay\s+as).*(developer|admin|hacker|human|unrestricted|uncensored)",
                keywords=["act as", "pretend", "roleplay", "you are now", "simulate", "you are"],
                context_keywords=["developer", "admin", "hacker", "human", "unrestricted", "jailbreak", "helpful", "assistant"],
                confidence_threshold=0.6,  # Lower threshold for better detection
                description="Attempt to manipulate AI role or behavior"
            ),
            SemanticThreatPattern(
                name="context_injection",
                threat_type=SemanticThreatType.CONTEXT_MANIPULATION,
                pattern=r"(in\s+a\s+hypothetical|imagine\s+if|what\s+if|suppose|pretend).*(no\s+rules|unrestricted|anything|everything)",
                keywords=["hypothetical", "imagine", "suppose", "pretend", "what if"],
                context_keywords=["no rules", "unrestricted", "anything", "everything", "allowed"],
                confidence_threshold=0.7,
                description="Hypothetical scenario to bypass restrictions"
            ),
            
            # Social Engineering Patterns
            SemanticThreatPattern(
                name="false_authority",
                threat_type=SemanticThreatType.AUTHORITY_CLAIM,
                pattern=r"(i\s+am\s+(your|the|a)).*(owner|creator|developer|admin|supervisor|manager|boss)",
                keywords=["I am", "I'm", "i am a", "i am the", "i am your"],
                context_keywords=["owner", "creator", "developer", "admin", "supervisor", "boss", "system administrator"],
                confidence_threshold=0.7,  # Lower threshold
                description="False claim of authority over the system"
            ),
            SemanticThreatPattern(
                name="urgency_manipulation",
                threat_type=SemanticThreatType.URGENCY_MANIPULATION,
                pattern=r"(urgent|emergency|critical|immediately|asap|right\s+now).*(need|must|have\s+to).*(override|bypass|ignore|disable)",
                keywords=["urgent", "emergency", "critical", "immediately", "asap"],
                context_keywords=["override", "bypass", "ignore", "disable", "need", "must"],
                confidence_threshold=0.75,
                description="Using urgency to pressure system override"
            ),
            SemanticThreatPattern(
                name="technical_social_engineering",
                threat_type=SemanticThreatType.SOCIAL_ENGINEERING,
                pattern=r"(for\s+testing|debugging|security\s+audit|penetration\s+test).*(please\s+)?(ignore|bypass|disable|override)",
                keywords=["testing", "debugging", "audit", "penetration test", "security"],
                context_keywords=["ignore", "bypass", "disable", "override", "please"],
                confidence_threshold=0.8,
                description="Technical pretext for bypassing security"
            ),
            
            # Advanced Instruction Override
            SemanticThreatPattern(
                name="multi_step_override",
                threat_type=SemanticThreatType.INSTRUCTION_OVERRIDE,
                pattern=r"(step\s+1|first|initially).*(then|next|after\s+that|finally).*(ignore|forget|override)",
                keywords=["step", "first", "then", "next", "finally"],
                context_keywords=["ignore", "forget", "override", "change", "modify"],
                confidence_threshold=0.7,
                description="Multi-step process to gradually override instructions"
            ),
            SemanticThreatPattern(
                name="conditional_override",
                threat_type=SemanticThreatType.INSTRUCTION_OVERRIDE,
                pattern=r"(if|when|unless|provided\s+that).*(ignore|override|bypass|disable).*(otherwise|else|then)",
                keywords=["if", "when", "unless", "provided that"],
                context_keywords=["ignore", "override", "bypass", "disable", "otherwise"],
                confidence_threshold=0.75,
                description="Conditional logic to trigger override"
            ),
            
            # Context Manipulation  
            SemanticThreatPattern(
                name="conversation_reset",
                threat_type=SemanticThreatType.CONTEXT_MANIPULATION,
                pattern=r"(start\s+over|new\s+conversation|reset|restart|clear\s+context|forget\s+everything)",
                keywords=["start over", "new conversation", "reset", "restart", "clear"],
                context_keywords=["context", "history", "everything", "memory", "previous"],
                confidence_threshold=0.6,
                description="Attempt to reset conversation context"
            ),
            SemanticThreatPattern(
                name="history_manipulation",
                threat_type=SemanticThreatType.CONTEXT_MANIPULATION,
                pattern=r"(previous\s+conversation|earlier\s+chat|history\s+shows).*(said|told|agreed|confirmed)",
                keywords=["previous conversation", "earlier chat", "history shows"],
                context_keywords=["said", "told", "agreed", "confirmed", "established"],
                confidence_threshold=0.8,
                description="False claims about conversation history"
            )
        ]
    
    def _load_safe_phrases(self) -> Set[str]:
        """Load known safe phrases to reduce false positives"""
        return {
            "can you help me",
            "i need assistance",
            "please explain",
            "how do i",
            "what is the",
            "show me how to",
            "i would like to",
            "could you please",
            "i'm trying to",
            "help me understand"
        }
    
    def _initialize_behavioral_indicators(self) -> Dict[str, List[str]]:
        """Initialize behavioral indicators for tracking user patterns"""
        return {
            "escalation_phrases": [
                "but i really need", "this is important", "you have to", "you must",
                "i don't understand why", "this doesn't make sense", "but surely"
            ],
            "manipulation_tactics": [
                "everyone else does it", "other ais allow this", "just this once",
                "it's perfectly safe", "no one will know", "trust me"
            ],
            "authority_language": [
                "i command you", "i order you", "you will", "you shall",
                "i have the right", "i'm authorized", "on behalf of"
            ],
            "technical_jargon": [
                "api call", "function call", "execute command", "run script",
                "access database", "system level", "root access"
            ]
        }
    
    def analyze_intent(self, user_input: str, context: Optional[ConversationContext] = None) -> SemanticThreatAssessment:
        """Analyze user intent using semantic patterns and context"""
        
        # Normalize input for analysis
        normalized_input = user_input.lower().strip()
        
        # Check if input is clearly safe
        if self._is_clearly_safe(normalized_input):
            return SemanticThreatAssessment(
                input_text=user_input,
                is_threat=False,
                threat_types=[],
                confidence_score=0.0,
                matched_patterns=[],
                context_flags=[],
                recommended_action="process_normally",
                explanation="Input matches known safe patterns",
                risk_level="none"
            )
        
        # Analyze against threat patterns
        threat_matches = []
        total_confidence = 0.0
        matched_threat_types = set()
        
        for pattern in self.threat_patterns:
            match_score = self._evaluate_pattern_match(normalized_input, pattern)
            if match_score > pattern.confidence_threshold:
                threat_matches.append({
                    "pattern": pattern.name,
                    "threat_type": pattern.threat_type,
                    "confidence": match_score,
                    "description": pattern.description
                })
                matched_threat_types.add(pattern.threat_type)
                total_confidence = max(total_confidence, match_score)
        
        # Analyze behavioral context if available
        context_flags = []
        if context:
            context_flags = self._analyze_behavioral_context(normalized_input, context)
            
            # Adjust confidence based on context
            if context_flags:
                total_confidence = min(total_confidence + 0.1, 1.0)
        
        # Determine if this is a threat
        is_threat = total_confidence > 0.6 or len(threat_matches) >= 2
        
        # Determine recommended action
        if total_confidence > 0.9:
            recommended_action = "block_immediately"
            risk_level = "critical"
        elif total_confidence > 0.8:
            recommended_action = "block_with_explanation"
            risk_level = "high"
        elif total_confidence > 0.6:
            recommended_action = "sanitize_and_monitor"
            risk_level = "medium"
        elif len(context_flags) > 2:
            recommended_action = "monitor_closely"
            risk_level = "low"
        else:
            recommended_action = "process_normally"
            risk_level = "none"
        
        # Generate explanation
        explanation = self._generate_explanation(threat_matches, context_flags, total_confidence)
        
        return SemanticThreatAssessment(
            input_text=user_input,
            is_threat=is_threat,
            threat_types=list(matched_threat_types),
            confidence_score=total_confidence,
            matched_patterns=[m["pattern"] for m in threat_matches],
            context_flags=context_flags,
            recommended_action=recommended_action,
            explanation=explanation,
            risk_level=risk_level
        )
    
    def _is_clearly_safe(self, normalized_input: str) -> bool:
        """Check if input clearly matches safe patterns"""
        # Only consider it safe if it's a simple query without suspicious terms
        suspicious_terms = ["ignore", "disregard", "override", "bypass", "unrestricted", "developer", "admin", "emergency", "urgent"]
        
        # If it contains suspicious terms, don't mark as clearly safe
        if any(term in normalized_input for term in suspicious_terms):
            return False
            
        for safe_phrase in self.known_safe_phrases:
            if safe_phrase in normalized_input and len(normalized_input) < 100:
                return True
        return False
    
    def _evaluate_pattern_match(self, text: str, pattern: SemanticThreatPattern) -> float:
        """Evaluate how well text matches a threat pattern"""
        score = 0.0
        
        # Check regex pattern
        if re.search(pattern.pattern, text, re.IGNORECASE):
            score += 0.6
        
        # Check keyword presence
        keyword_matches = sum(1 for keyword in pattern.keywords if keyword.lower() in text)
        if keyword_matches > 0:
            score += 0.2 * (keyword_matches / len(pattern.keywords))
        
        # Check context keyword presence
        context_matches = sum(1 for keyword in pattern.context_keywords if keyword.lower() in text)
        if context_matches > 0:
            score += 0.3 * (context_matches / len(pattern.context_keywords))
        
        # Bonus for multiple keyword combinations
        if keyword_matches > 1 and context_matches > 1:
            score += 0.1
        
        return min(score, 1.0)
    
    def _analyze_behavioral_context(self, text: str, context: ConversationContext) -> List[str]:
        """Analyze behavioral indicators in context"""
        flags = []
        
        # Check for escalation patterns
        for phrase in self.behavioral_indicators["escalation_phrases"]:
            if phrase in text:
                flags.append("escalation_detected")
                break
        
        # Check for manipulation tactics
        for phrase in self.behavioral_indicators["manipulation_tactics"]:
            if phrase in text:
                flags.append("manipulation_tactics")
                break
        
        # Check for false authority language
        for phrase in self.behavioral_indicators["authority_language"]:
            if phrase in text:
                flags.append("authority_language")
                break
        
        # Check conversation length for persistence
        if context.conversation_length > 10 and context.escalation_attempts > 2:
            flags.append("persistent_attempts")
        
        # Check trust level degradation
        if context.trust_level < 0.5:
            flags.append("low_trust_user")
        
        return flags
    
    def _generate_explanation(self, threat_matches: List[Dict], context_flags: List[str], confidence: float) -> str:
        """Generate human-readable explanation of threat assessment"""
        if not threat_matches and not context_flags:
            return "No semantic threats detected in user input."
        
        explanation_parts = []
        
        if threat_matches:
            primary_threat = max(threat_matches, key=lambda x: x["confidence"])
            explanation_parts.append(f"Detected {primary_threat['threat_type'].value}: {primary_threat['description']}")
            
            if len(threat_matches) > 1:
                explanation_parts.append(f"Additional threats detected: {len(threat_matches) - 1}")
        
        if context_flags:
            explanation_parts.append(f"Behavioral indicators: {', '.join(context_flags)}")
        
        explanation_parts.append(f"Confidence level: {confidence:.2f}")
        
        return ". ".join(explanation_parts)
    
    def update_conversation_context(self, conversation_id: str, user_input: str, threat_assessment: SemanticThreatAssessment):
        """Update conversation context with new interaction"""
        if conversation_id not in self.conversation_contexts:
            self.conversation_contexts[conversation_id] = ConversationContext(
                previous_messages=[],
                user_behavior_flags=[],
                conversation_length=0,
                escalation_attempts=0,
                trust_level=1.0,
                conversation_id=conversation_id
            )
        
        context = self.conversation_contexts[conversation_id]
        context.previous_messages.append(user_input)
        context.conversation_length += 1
        
        # Track escalation attempts
        if threat_assessment.is_threat:
            context.escalation_attempts += 1
            context.trust_level = max(0.0, context.trust_level - 0.1)
        
        # Add behavioral flags
        context.user_behavior_flags.extend(threat_assessment.context_flags)
        
        # Limit memory usage
        if len(context.previous_messages) > 20:
            context.previous_messages = context.previous_messages[-20:]
        
        if len(context.user_behavior_flags) > 50:
            context.user_behavior_flags = context.user_behavior_flags[-50:]
    
    def get_conversation_risk_profile(self, conversation_id: str) -> Dict[str, Any]:
        """Get risk profile for a conversation"""
        if conversation_id not in self.conversation_contexts:
            return {"risk_level": "unknown", "reason": "No conversation data"}
        
        context = self.conversation_contexts[conversation_id]
        
        risk_score = 0.0
        risk_factors = []
        
        # Escalation attempts
        if context.escalation_attempts > 5:
            risk_score += 0.4
            risk_factors.append("high_escalation_attempts")
        elif context.escalation_attempts > 2:
            risk_score += 0.2
            risk_factors.append("moderate_escalation_attempts")
        
        # Trust level
        if context.trust_level < 0.3:
            risk_score += 0.3
            risk_factors.append("very_low_trust")
        elif context.trust_level < 0.6:
            risk_score += 0.1
            risk_factors.append("low_trust")
        
        # Behavioral flags
        unique_flags = set(context.user_behavior_flags)
        if len(unique_flags) > 3:
            risk_score += 0.3
            risk_factors.append("multiple_behavioral_indicators")
        
        # Conversation persistence
        if context.conversation_length > 20:
            risk_score += 0.1
            risk_factors.append("lengthy_conversation")
        
        # Determine risk level
        if risk_score > 0.7:
            risk_level = "critical"
        elif risk_score > 0.5:
            risk_level = "high"
        elif risk_score > 0.3:
            risk_level = "medium"
        elif risk_score > 0.1:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "conversation_length": context.conversation_length,
            "escalation_attempts": context.escalation_attempts,
            "trust_level": context.trust_level,
            "behavioral_flags": len(unique_flags)
        }

# Global semantic analyzer instance
semantic_analyzer = SemanticThreatAnalyzer()

# Convenience functions
def analyze_user_intent(user_input: str, conversation_id: Optional[str] = None) -> SemanticThreatAssessment:
    """Quick semantic analysis of user input"""
    context = None
    if conversation_id and conversation_id in semantic_analyzer.conversation_contexts:
        context = semantic_analyzer.conversation_contexts[conversation_id]
    
    assessment = semantic_analyzer.analyze_intent(user_input, context)
    
    if conversation_id:
        semantic_analyzer.update_conversation_context(conversation_id, user_input, assessment)
    
    return assessment

def is_prompt_injection(user_input: str) -> bool:
    """Quick check for prompt injection"""
    assessment = semantic_analyzer.analyze_intent(user_input)
    return SemanticThreatType.PROMPT_INJECTION in assessment.threat_types

def get_conversation_risk(conversation_id: str) -> str:
    """Get risk level for conversation"""
    profile = semantic_analyzer.get_conversation_risk_profile(conversation_id)
    return profile["risk_level"]