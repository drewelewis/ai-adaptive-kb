"""
Robust Intent Classification System
Replaces brittle string-matching with confidence-based scoring
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class IntentPattern:
    keywords: List[str]
    phrases: List[str]
    required_combinations: List[Tuple[List[str], List[str]]]
    priority: int  # 1=high, 2=medium, 3=low
    confidence_threshold: float = 30.0

class RobustIntentClassifier:
    """Robust intent classification with confidence scoring and priority handling"""
    
    def __init__(self):
        self.intent_patterns = {
            "analyze_content_gaps": IntentPattern(
                keywords=["gap", "gaps", "find", "content", "missing", "analyze", "suggest", "create", "add", "where", "exist", "doing", "isnt"],
                phrases=[
                    "find gaps", "can you find gaps", "find gaps in", "gaps in", 
                    "content gaps", "gaps in content", "analyze content", "gap analysis",
                    "suggest content", "missing content", "what's missing", "content analysis",
                    "suggest where content", "where content can be", "content added where", "gaps exist",
                    "where gaps exist", "content can be created", "suggest where", "doing a gap analysis",
                    "isnt doing a gap", "want content added", "content added where gaps", "gap analysis",
                    "doing a gap", "isnt doing", "can you suggest where", "where content can",
                    "content can be", "can be created"
                ],
                required_combinations=[
                    (["gap", "gaps"], ["find", "content", "exist", "where", "doing", "analysis"]),
                    (["find", "suggest"], ["gaps", "content", "where"]),
                    (["analyze"], ["content", "gaps"]),
                    (["content"], ["added", "create", "gaps", "where", "can", "be"]),
                    (["where"], ["gaps", "content", "exist", "can"]),
                    (["doing"], ["gap", "analysis"]),
                    (["isnt"], ["doing", "gap"])
                ],
                priority=1,  # High priority - changed from 2
                confidence_threshold=25.0  # Lower threshold for gap analysis
            ),
            
            "get_conversation_history": IntentPattern(
                keywords=["last", "recent", "history", "previous", "questions", "commands", "asked"],
                phrases=[
                    "last 3 questions", "last 3 commands", "recent questions", "conversation history",
                    "my last", "get my", "show my", "previous commands", "what did i ask",
                    "my questions", "recent commands", "chat history", "last few questions",
                    "previous questions", "last questions", "my recent", "show me my last"
                ],
                required_combinations=[
                    (["last", "recent"], ["questions", "commands", "3", "few"]),
                    (["get", "show"], ["my", "history", "last"]),
                    (["conversation", "chat"], ["history"]),
                    (["what", "previous"], ["asked", "questions"])
                ],
                priority=1  # High priority
            ),
            
            "set_knowledge_base_context": IntentPattern(
                keywords=["use", "select", "switch", "kb", "knowledge", "base"],
                phrases=[
                    "use kb", "select kb", "switch to kb", "knowledge base", "use knowledge base",
                    "select knowledge base", "switch knowledge base", "change kb", "set kb"
                ],
                required_combinations=[
                    (["use", "select", "switch", "change"], ["kb", "knowledge"]),
                    (["knowledge"], ["base"])
                ],
                priority=1  # High priority
            ),
            
            "set_article_context": IntentPattern(
                keywords=["work", "focus", "article", "category", "section"],
                phrases=[
                    "work on article", "focus on article", "work on category", "focus on category",
                    "work with category", "focus on section", "article", "category"
                ],
                required_combinations=[
                    (["work", "focus"], ["article", "category", "section"]),
                    (["article", "category"], ["id", "number"])
                ],
                priority=1  # High priority
            ),
            
            "create_content": IntentPattern(
                keywords=["create", "add", "new", "insert", "make", "implement", "additions", "go", "ahead", "articles", "these", "coordinate", "supervisor", "changes", "content", "ideas", "get", "proceed", "through", "list", "category", "categories", "family", "finance", "recommended", "ok"],
                phrases=[
                    "create article", "add article", "new article", "create content",
                    "add content", "insert article", "create new", "add new",
                    "make these additions", "go ahead and make", "implement additions",
                    "implement all", "make the additions", "add these", "create these",
                    "can you go ahead", "go ahead and", "implement all the additions",
                    "add these articles", "these articles", "add articles",
                    "make the needed changes", "coordinate with the supervisor", 
                    "get these content ideas implemented", "content ideas implemented",
                    "go through this list", "make the needed", "coordinate with supervisor",
                    "get these ideas implemented", "implement content ideas", "proceed with changes",
                    "lets proceed", "please coordinate", "supervisor to get", "ideas implemented",
                    "create a new", "create new category", "create category", "new category",
                    "family finance category", "family finance", "create articles about",
                    "add the recommended", "recommended articles", "add recommended", 
                    "ok add", "add the", "the recommended", "ok, add", "add some content",
                    "add content where", "content where gaps", "where gaps exist",
                    "ok add the", "add all the", "implement the recommended", "ok implement"
                ],
                required_combinations=[
                    (["create", "add", "new", "make"], ["article", "content", "additions", "category"]),
                    (["insert"], ["article", "content"]),
                    (["implement"], ["additions", "all", "ideas", "content", "recommended"]),
                    (["go", "ahead"], ["make", "add", "implement"]),
                    (["these"], ["additions", "articles", "ideas", "changes"]),
                    (["coordinate"], ["supervisor", "with"]),
                    (["make"], ["changes", "needed", "additions"]),
                    (["get"], ["implemented", "ideas", "content"]),
                    (["proceed"], ["with", "changes", "additions"]),
                    (["create"], ["new", "category", "article", "content"]),
                    (["family"], ["finance", "category"]),
                    (["new"], ["category", "articles", "content"]),
                    (["add"], ["recommended", "the", "articles", "content"]),
                    (["recommended"], ["articles", "content"]),
                    (["ok"], ["add", "implement", "create"]),
                    (["where"], ["gaps", "exist"])
                ],
                priority=1,  # Changed to high priority to ensure content creation is prioritized
                confidence_threshold=15.0  # Further lowered threshold for content creation
            ),
            
            "update_content": IntentPattern(
                keywords=["update", "edit", "modify", "change"],
                phrases=[
                    "update article", "edit article", "modify article", "change article",
                    "update content", "edit content", "modify content"
                ],
                required_combinations=[
                    (["update", "edit", "modify", "change"], ["article", "content"])
                ],
                priority=2  # Medium priority
            ),
            
            "search_content": IntentPattern(
                keywords=["search", "find", "look", "query"],
                phrases=[
                    "search for", "find article", "look for", "search articles",
                    "find content", "search content", "query articles"
                ],
                required_combinations=[
                    (["search", "find", "look"], ["article", "content", "for"])
                ],
                priority=2  # Medium priority
            ),
            
            "retrieve_content": IntentPattern(
                keywords=["show", "display", "list", "get", "hierarchy"],
                phrases=[
                    "show articles", "display articles", "list articles", "get articles",
                    "show content", "display content", "list content", "article hierarchy"
                ],
                required_combinations=[
                    (["show", "display", "list", "get"], ["articles", "content", "hierarchy"])
                ],
                priority=3  # Low priority
            )
        }
    
    def classify_intent(self, user_message: str) -> Tuple[str, float]:
        """
        Classify user intent with confidence score
        
        Returns:
            Tuple of (intent, confidence_score)
        """
        if not user_message or not user_message.strip():
            return "general_inquiry", 0.0
            
        message_lower = user_message.lower().strip()
        scores = {}
        
        # Calculate scores for each intent
        for intent, pattern in self.intent_patterns.items():
            score = self._calculate_intent_score(message_lower, pattern)
            if score >= pattern.confidence_threshold:
                scores[intent] = (score, pattern.priority)
        
        if not scores:
            return "general_inquiry", 0.0
        
        # Sort by priority first (lower number = higher priority), then by score
        sorted_intents = sorted(scores.items(), key=lambda x: (x[1][1], -x[1][0]))
        
        best_intent = sorted_intents[0][0]
        confidence = sorted_intents[0][1][0]
        
        return best_intent, confidence
    
    def _calculate_intent_score(self, message: str, pattern: IntentPattern) -> float:
        """Calculate confidence score for a specific intent"""
        score = 0.0
        
        # Keyword matching (base score)
        keyword_matches = sum(1 for keyword in pattern.keywords if keyword in message)
        keyword_score = (keyword_matches / len(pattern.keywords)) * 25
        score += keyword_score
        
        # Phrase matching (higher weight for exact phrases)
        phrase_matches = sum(1 for phrase in pattern.phrases if phrase in message)
        phrase_score = (phrase_matches / len(pattern.phrases)) * 35
        score += phrase_score
        
        # Required combination matching (highest weight)
        combination_score = 0
        for req_combo in pattern.required_combinations:
            group1, group2 = req_combo
            has_group1 = any(word in message for word in group1)
            has_group2 = any(word in message for word in group2)
            if has_group1 and has_group2:
                combination_score += 40 / len(pattern.required_combinations)
        
        score += combination_score
        
        # Bonus for multiple matches
        if keyword_matches > 1 and phrase_matches > 0:
            score += 10  # Bonus for multiple types of matches
        
        return min(100, score)
    
    def get_debug_info(self, user_message: str) -> Dict:
        """Get detailed debug information about intent classification"""
        message_lower = user_message.lower().strip()
        debug_info = {}
        
        for intent, pattern in self.intent_patterns.items():
            keyword_matches = [k for k in pattern.keywords if k in message_lower]
            phrase_matches = [p for p in pattern.phrases if p in message_lower]
            
            combination_matches = []
            for req_combo in pattern.required_combinations:
                group1, group2 = req_combo
                has_group1 = [word for word in group1 if word in message_lower]
                has_group2 = [word for word in group2 if word in message_lower]
                if has_group1 and has_group2:
                    combination_matches.append((has_group1, has_group2))
            
            score = self._calculate_intent_score(message_lower, pattern)
            
            debug_info[intent] = {
                'score': score,
                'priority': pattern.priority,
                'threshold': pattern.confidence_threshold,
                'passes_threshold': score >= pattern.confidence_threshold,
                'keyword_matches': keyword_matches,
                'phrase_matches': phrase_matches,
                'combination_matches': combination_matches
            }
        
        return debug_info

def test_classifier():
    """Test function to verify classifier works correctly"""
    classifier = RobustIntentClassifier()
    
    test_cases = [
        "can you find gaps in the current kb content?",
        "analyze my content and suggest new ideas",
        "what did I ask in my last 3 questions?",
        "get my recent conversation history",
        "use knowledge base 1",
        "switch to kb 2", 
        "work on article 5",
        "focus on budgeting category",
        "create a new article about investing",
        "show me all articles",
        "search for retirement articles"
    ]
    
    print("🧪 Testing Robust Intent Classifier")
    print("=" * 50)
    
    for test_msg in test_cases:
        intent, confidence = classifier.classify_intent(test_msg)
        print(f"'{test_msg}'")
        print(f"  → Intent: {intent} (confidence: {confidence:.1f}%)")
        print()

if __name__ == "__main__":
    test_classifier()
