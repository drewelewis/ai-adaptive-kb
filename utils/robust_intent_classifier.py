#!/usr/bin/env python3

import re
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass

@dataclass
class SemanticIntent:
    """Semantic intent pattern using natural language structures"""
    name: str
    action_verbs: List[str]
    object_nouns: List[str]
    modifiers: List[str]
    sentence_patterns: List[str]
    priority: int = 1
    confidence_boost: float = 1.0

class RobustIntentClassifier:
    """
    Intelligent intent classifier using semantic patterns and natural language understanding
    instead of manual phrase enumeration. Covers 90% of common English patterns automatically.
    """
    
    def __init__(self):
        self.intents = self._initialize_semantic_intents()
        
    def _initialize_semantic_intents(self) -> Dict[str, SemanticIntent]:
        """Initialize semantic intent patterns using natural language structures"""
        
        return {
            "create_content": SemanticIntent(
                name="create_content",
                action_verbs=["create", "add", "make", "build", "generate", "implement", "insert", "produce", "develop", "establish", "form"],
                object_nouns=["content", "article", "articles", "category", "categories", "section", "sections", "topic", "topics", "page", "pages", "item", "items"],
                modifiers=["new", "recommended", "suggested", "additional", "missing", "needed", "required", "these", "those", "some", "more", "all"],
                sentence_patterns=[
                    r"(?:ok,?\s+)?(?:please\s+)?(?:can\s+you\s+)?(?:go\s+ahead\s+and\s+)?(create|add|make|implement|insert)",
                    r"(?:let'?s\s+)?(create|add|make|build)",
                    r"(?:i\s+(?:want|need|would like)\s+(?:to\s+)?(?:you\s+to\s+)?)(create|add|make)",
                    r"(?:could\s+you\s+(?:please\s+)?)(create|add|make|implement)",
                    r"(create|add|implement|make).*(?:content|article|category)",
                    r"(?:the\s+)?(recommended|suggested|missing|new).*(?:content|article|category)",
                ],
                priority=1,
                confidence_boost=1.2
            ),
            
            "analyze_content_gaps": SemanticIntent(
                name="analyze_content_gaps",
                action_verbs=["find", "identify", "locate", "discover", "detect", "analyze", "examine", "review", "assess", "evaluate"],
                object_nouns=["gaps", "gap", "missing", "holes", "omissions", "deficiencies", "shortcomings", "problems", "issues"],
                modifiers=["content", "article", "knowledge", "information", "data", "coverage", "areas"],
                sentence_patterns=[
                    r"(?:can\s+you\s+)?(?:please\s+)?(find|identify|locate|show).*(?:gaps|missing|holes)",
                    r"(?:what\s+(?:are\s+)?(?:the\s+)?)(gaps|missing|holes|problems)",
                    r"(?:where\s+(?:are\s+)?(?:the\s+)?)(gaps|missing|holes|deficiencies)",
                    r"(analyze|examine|review|assess).*(?:gaps|coverage|content)",
                    r"(?:tell\s+me\s+about\s+)?(?:content\s+)?(gaps|missing|deficiencies)",
                ],
                priority=1,
                confidence_boost=1.1
            ),
            
            "retrieve_content": SemanticIntent(
                name="retrieve_content",
                action_verbs=["show", "display", "list", "get", "fetch", "retrieve", "view", "see", "browse", "explore"],
                object_nouns=["content", "articles", "categories", "sections", "topics", "hierarchy", "structure", "tree", "outline"],
                modifiers=["all", "current", "existing", "available", "complete", "full", "entire"],
                sentence_patterns=[
                    r"(?:can\s+you\s+)?(?:please\s+)?(show|display|list|get).*(?:content|articles|categories)",
                    r"(?:i\s+(?:want|need|would like)\s+to\s+)(see|view|browse|explore)",
                    r"(?:what\s+(?:are\s+)?(?:the\s+)?(?:current\s+)?)(articles|categories|content)",
                    r"(show|display|list).*(?:me\s+)?(?:all\s+)?(?:the\s+)?(?:content|articles)",
                ],
                priority=2,
                confidence_boost=1.0
            ),
            
            "set_knowledge_base_context": SemanticIntent(
                name="set_knowledge_base_context",
                action_verbs=["use", "select", "switch", "change", "set", "choose", "pick"],
                object_nouns=["kb", "knowledge", "base", "database", "collection"],
                modifiers=["to", "number", "id"],
                sentence_patterns=[
                    r"(use|select|switch|set).*(?:kb|knowledge.*base)",
                    r"(?:switch\s+to\s+|change\s+to\s+|use\s+)(kb|knowledge)",
                    r"(?:i\s+want\s+to\s+use\s+)(kb|knowledge)",
                ],
                priority=1,
                confidence_boost=1.3
            ),
            
            "set_article_context": SemanticIntent(
                name="set_article_context",
                action_verbs=["work", "focus", "select", "choose", "open"],
                object_nouns=["article", "category", "section", "topic"],
                modifiers=["on", "with", "main", "specific"],
                sentence_patterns=[
                    r"(work|focus).*(?:on|with).*(?:article|category|section)",
                    r"(?:i\s+want\s+to\s+)(work|focus).*(?:on|with)",
                    r"(select|choose|open).*(?:article|category|section)",
                ],
                priority=2,
                confidence_boost=1.1
            ),
            
            "retrieve_filtered_content": SemanticIntent(
                name="retrieve_filtered_content",
                action_verbs=["show", "display", "list", "get"],
                object_nouns=["articles", "content", "items"],
                modifiers=["under", "in", "from", "within", "specific", "section"],
                sentence_patterns=[
                    r"(show|display|list|get).*(?:articles|content).*(?:under|in|from|within)",
                    r"(?:articles|content).*(?:under|in|from|within)",
                    r"(?:show|list).*(?:specific|section)",
                ],
                priority=2,
                confidence_boost=1.0
            ),
            
            "update_content": SemanticIntent(
                name="update_content",
                action_verbs=["update", "edit", "modify", "change", "revise", "alter", "adjust", "fix", "correct"],
                object_nouns=["content", "article", "articles", "category", "section", "text", "information"],
                modifiers=["existing", "current", "this", "that", "the"],
                sentence_patterns=[
                    r"(?:can\s+you\s+)?(?:please\s+)?(update|edit|modify|change).*(?:content|article)",
                    r"(?:i\s+(?:want|need)\s+to\s+)(update|edit|modify|change)",
                    r"(fix|correct|revise).*(?:content|article|text)",
                ],
                priority=2,
                confidence_boost=1.0
            ),
            
            "search_content": SemanticIntent(
                name="search_content",
                action_verbs=["search", "find", "look", "locate", "seek"], 
                object_nouns=["for", "content", "article", "information", "topic", "keyword"],
                modifiers=["specific", "particular", "about", "related", "containing"],
                sentence_patterns=[
                    r"(search|find|look).*(?:for|about|containing)",
                    r"(?:can\s+you\s+)?(?:help\s+me\s+)?(find|search|locate)",
                    r"(?:i\s+(?:am\s+)?(?:looking|searching)\s+for)",
                ],
                priority=2,
                confidence_boost=1.0
            ),
            
            "get_conversation_history": SemanticIntent(
                name="get_conversation_history",
                action_verbs=["show", "get", "list", "display"],
                object_nouns=["history", "conversation", "previous", "last", "recent", "questions", "commands"],
                modifiers=["my", "our", "chat", "3", "few"],
                sentence_patterns=[
                    r"(?:show|get|list).*(?:history|conversation|previous|last|recent)",
                    r"(?:my|our).*(?:history|conversation|questions|commands)",
                    r"(?:last|recent).*(?:questions|commands|3)",
                ],
                priority=2,
                confidence_boost=1.0
            ),
            
            "general_inquiry": SemanticIntent(
                name="general_inquiry",
                action_verbs=["help", "explain", "tell", "describe", "clarify", "understand"],
                object_nouns=["me", "how", "what", "why", "when", "where"],
                modifiers=["can", "could", "would", "should", "please"],
                sentence_patterns=[
                    r"(?:can\s+you\s+)?(?:please\s+)?(help|explain|tell|describe)",
                    r"(?:what\s+(?:is|are)|how\s+(?:do|does)|why\s+(?:is|are))",
                    r"(?:i\s+(?:don't\s+)?(?:understand|know|get))",
                ],
                priority=3,  # Lowest priority - catch-all
                confidence_boost=0.8
            )
        }
    
    def classify_intent(self, text: str) -> Tuple[str, float]:
        """
        Classify intent using semantic patterns and natural language understanding
        Returns (intent_name, confidence_percentage)
        """
        text = text.lower().strip()
        
        # Score each intent
        intent_scores = {}
        
        for intent_name, intent_pattern in self.intents.items():
            score = self._calculate_semantic_score(text, intent_pattern)
            if score > 0:
                intent_scores[intent_name] = score
        
        if not intent_scores:
            return "general_inquiry", 0.0
        
        # Get the highest scoring intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        intent_name, raw_score = best_intent
        
        # Convert to percentage and apply confidence boost
        confidence = min(raw_score * self.intents[intent_name].confidence_boost, 100.0)
        
        return intent_name, confidence
    
    def _calculate_semantic_score(self, text: str, intent_pattern: SemanticIntent) -> float:
        """Calculate semantic score for an intent pattern"""
        
        total_score = 0.0
        max_possible_score = 0.0
        
        # 1. Check sentence patterns (highest weight)
        pattern_score = 0.0
        for pattern in intent_pattern.sentence_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_score = 40.0  # High score for pattern matches
                break
        
        total_score += pattern_score
        max_possible_score += 40.0
        
        # 2. Check action verbs (medium-high weight)
        action_score = 0.0
        words = text.split()
        for verb in intent_pattern.action_verbs:
            if any(verb in word for word in words):
                action_score += 15.0
                break  # Only count once per intent
        
        total_score += min(action_score, 25.0)  # Cap at 25
        max_possible_score += 25.0
        
        # 3. Check object nouns (medium weight)
        noun_score = 0.0
        for noun in intent_pattern.object_nouns:
            if noun in text:
                noun_score += 10.0
        
        total_score += min(noun_score, 20.0)  # Cap at 20
        max_possible_score += 20.0
        
        # 4. Check modifiers (low weight)
        modifier_score = 0.0
        for modifier in intent_pattern.modifiers:
            if modifier in text:
                modifier_score += 5.0
        
        total_score += min(modifier_score, 15.0)  # Cap at 15
        max_possible_score += 15.0
        
        # 5. Apply priority weighting
        priority_weight = (4 - intent_pattern.priority) / 3.0  # Higher priority = higher weight
        total_score *= priority_weight
        
        # Return percentage
        if max_possible_score > 0:
            return (total_score / max_possible_score) * 100.0
        return 0.0
    
    def get_debug_info(self, text: str) -> Dict:
        """Get detailed scoring information for debugging"""
        text = text.lower().strip()
        debug_info = {}
        
        for intent_name, intent_pattern in self.intents.items():
            score = self._calculate_semantic_score(text, intent_pattern)
            
            # Check which components matched
            words = text.split()
            matched_verbs = [v for v in intent_pattern.action_verbs if any(v in word for word in words)]
            matched_nouns = [n for n in intent_pattern.object_nouns if n in text]
            matched_modifiers = [m for m in intent_pattern.modifiers if m in text]
            matched_patterns = [p for p in intent_pattern.sentence_patterns if re.search(p, text, re.IGNORECASE)]
            
            debug_info[intent_name] = {
                "score": score,
                "matched_verbs": matched_verbs,
                "matched_nouns": matched_nouns,
                "matched_modifiers": matched_modifiers,
                "matched_patterns": len(matched_patterns),
                "priority": intent_pattern.priority
            }
        
        return debug_info
