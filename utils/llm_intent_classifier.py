#!/usr/bin/env python3

from typing import Tuple, Dict, Any, Optional, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
import json


class LLMIntentClassifier:
    """
    LLM-based intent classifier that uses GPT to analyze user intent
    directly instead of relying on pattern matching or rule-based classification.
    This approach is more reliable, flexible, and can handle natural language nuances better.
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        self.llm = llm
            
        self.intents = {
            "create_content": {
                "description": "User wants to create, add, make, or implement new content, articles, categories, or sections",
                "examples": ["create new article", "add content", "implement the recommended articles", "make new categories"]
            },
            "analyze_content_gaps": {
                "description": "User wants to find gaps, identify missing content, or analyze what's not covered",
                "examples": ["find gaps", "what's missing", "analyze content coverage", "identify deficiencies"]
            },
            "retrieve_content": {
                "description": "User wants to see, display, list, or browse existing content and structure",
                "examples": ["show articles", "list categories", "display content", "what articles do we have"]
            },
            "retrieve_filtered_content": {
                "description": "User wants to see content from a specific section, category, or filtered view",
                "examples": ["show articles under Finance", "list content in specific category", "articles from section X"]
            },
            "update_content": {
                "description": "User wants to edit, modify, update, or change existing content",
                "examples": ["edit article", "update content", "modify the text", "change existing article"]
            },
            "search_content": {
                "description": "User wants to search for specific content, articles, or information",
                "examples": ["search for X", "find article about Y", "look for content containing Z"]
            },
            "set_knowledge_base_context": {
                "description": "User wants to select, switch to, or use a different knowledge base",
                "examples": ["use KB 1", "switch to knowledge base 2", "select knowledge base"]
            },
            "set_article_context": {
                "description": "User wants to work on, focus on, or select a specific article or category",
                "examples": ["work on article X", "focus on category Y", "select article"]
            },
            "get_conversation_history": {
                "description": "User wants to see their recent commands, conversation history, or previous questions",
                "examples": ["show my last commands", "conversation history", "what did I ask before"]
            },
            "general_inquiry": {
                "description": "User has general questions, needs help, or wants explanations about the system",
                "examples": ["how does this work", "what can you do", "help me understand", "explain this"]
            }
        }
    
    def classify_intent(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, float]:
        """
        Classify user intent using LLM analysis
        Returns (intent_name, confidence_percentage)
        """
        if not user_message or not user_message.strip():
            return "general_inquiry", 0.0
        
        # Create system prompt with intent definitions
        system_prompt = self._create_system_prompt()
        
        # Create user prompt with context if available
        user_prompt = self._create_user_prompt(user_message, context)
        
        try:
            # Get LLM response
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse the JSON response
            result = self._parse_llm_response(response.content)
            
            return result.get("intent", "general_inquiry"), result.get("confidence", 50.0)
            
        except Exception as e:
            print(f"Error in LLM intent classification: {e}")
            # Fallback to general inquiry with low confidence
            return "general_inquiry", 10.0
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for intent classification"""
        
        intent_definitions = []
        for intent_name, info in self.intents.items():
            examples_str = ", ".join(f'"{ex}"' for ex in info["examples"][:3])  # Show first 3 examples
            intent_definitions.append(
                f"- **{intent_name}**: {info['description']}\n  Examples: {examples_str}"
            )
        
        return f"""You are an expert intent classifier for a knowledge base management system. Your job is to analyze user messages and determine their intent with high accuracy.

**Available Intents:**
{chr(10).join(intent_definitions)}

**Instructions:**
1. Read the user message carefully and understand what they want to accomplish
2. Consider any provided context about their current session or previous actions
3. Match the intent to one of the available categories above
4. Provide a confidence score (0-100) based on how certain you are
5. If the message contains multiple intents, choose the primary/main intent
6. If unsure between similar intents, choose the more specific one
7. Default to "general_inquiry" only if the message is truly ambiguous or doesn't fit other categories

**Response Format:**
Respond with valid JSON only:
{{
    "intent": "intent_name",
    "confidence": 85,
    "reasoning": "Brief explanation of why you chose this intent"
}}

**Important:** 
- Be confident in your classifications - most user messages have clear intent
- Consider context clues and natural language patterns
- Prioritize user's actual goal over specific words used"""
    
    def _create_user_prompt(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create the user prompt with message and context"""
        
        prompt = f"**User Message:** \"{user_message}\"\n"
        
        if context:
            context_parts = []
            
            if context.get("current_kb"):
                context_parts.append(f"Current Knowledge Base: {context['current_kb']}")
            
            if context.get("current_article"):
                context_parts.append(f"Current Article Context: {context['current_article']}")
            
            if context.get("recent_actions"):
                context_parts.append(f"Recent Actions: {', '.join(context['recent_actions'][-3:])}")
            
            if context.get("previous_intent"):
                context_parts.append(f"Previous Intent: {context['previous_intent']}")
            
            if context_parts:
                prompt += f"\n**Context:**\n{chr(10).join(context_parts)}\n"
        
        prompt += "\nClassify the intent and provide your response in JSON format:"
        
        return prompt
    
    def _parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the LLM response and extract intent information"""
        
        try:
            # Try to parse as JSON directly
            result = json.loads(response_content.strip())
            
            # Validate that we have required fields
            if "intent" not in result:
                raise ValueError("Missing 'intent' field in response")
            
            # Ensure intent is valid
            if result["intent"] not in self.intents:
                print(f"Warning: Unknown intent '{result['intent']}', defaulting to 'general_inquiry'")
                result["intent"] = "general_inquiry"
            
            # Ensure confidence is a valid number
            if "confidence" not in result or not isinstance(result["confidence"], (int, float)):
                result["confidence"] = 50.0
            
            # Clamp confidence to 0-100 range
            result["confidence"] = max(0.0, min(100.0, float(result["confidence"])))
            
            return result
            
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks or other formats
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                    return self._parse_llm_response(json.dumps(result))  # Recursive call with clean JSON
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON-like content without code blocks
            json_match = re.search(r'\{[^{}]*"intent"[^{}]*\}', response_content)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    return self._parse_llm_response(json.dumps(result))  # Recursive call with clean JSON
                except json.JSONDecodeError:
                    pass
            
            print(f"Warning: Could not parse LLM response as JSON: {response_content}")
            return {"intent": "general_inquiry", "confidence": 10.0, "reasoning": "Failed to parse response"}
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return {"intent": "general_inquiry", "confidence": 10.0, "reasoning": f"Parsing error: {e}"}
    
    def get_debug_info(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get detailed debug information about the intent classification"""
        
        intent, confidence = self.classify_intent(user_message, context)
        
        return {
            "user_message": user_message,
            "context": context,
            "classified_intent": intent,
            "confidence": confidence,
            "intent_description": self.intents.get(intent, {}).get("description", "Unknown intent"),
            "available_intents": list(self.intents.keys()),
            "system_prompt_length": len(self._create_system_prompt()),
            "user_prompt_length": len(self._create_user_prompt(user_message, context))
        }
    
    def get_supported_intents(self) -> List[str]:
        """Get list of all supported intent names"""
        return list(self.intents.keys())
    
    def get_intent_info(self, intent_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific intent"""
        return self.intents.get(intent_name, {})


def test_llm_intent_classifier():
    """Test the LLM intent classifier with various phrases"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv(override=True)
    
    # Initialize LLM and classifier
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv('OPENAI_API_ENDPOINT'),
        azure_deployment=os.getenv('OPENAI_API_MODEL_DEPLOYMENT_NAME'),
        api_version=os.getenv('OPENAI_API_VERSION')
        # Note: o1 model doesn't support temperature parameter
    )
    
    classifier = LLMIntentClassifier(llm)
    
    test_phrases = [
        # Content creation variations
        "ok, add the recommended articles",
        "create new content about family finance", 
        "please implement the suggested articles",
        "let's add some missing content",
        "build new categories for investment",
        "can you make the recommended additions",
        "I want you to create new articles",
        "go ahead and add those topics",
        
        # Gap analysis variations
        "find content gaps in the knowledge base",
        "what are the missing topics",
        "show me where there are holes in coverage",
        "analyze the content for deficiencies",
        "identify areas that need more articles",
        "where are the gaps in our content",
        
        # Retrieval variations
        "show me all the articles",
        "display the current content structure",
        "list all categories and articles",
        "I want to see the knowledge base hierarchy",
        "browse all available content",
        
        # Context setting variations
        "use knowledge base 1",
        "switch to kb 2", 
        "select the first database",
        "change to knowledge base number 3",
        
        # General inquiries
        "how does this system work",
        "what can you help me with",
        "explain the knowledge base features",
        "I don't understand how to use this"
    ]
    
    print("🧠 LLM-BASED INTENT CLASSIFIER TEST")
    print("=" * 70)
    
    for phrase in test_phrases:
        intent, confidence = classifier.classify_intent(phrase)
        print(f"'{phrase[:50]:<50}' → {intent:<25} ({confidence:5.1f}%)")
    
    print("\n" + "=" * 70)
    print("✅ LLM handles natural language understanding automatically!")
    print("✅ No need for manual pattern maintenance or rule updates!")
    print("✅ Better context awareness and nuanced understanding!")


if __name__ == "__main__":
    test_llm_intent_classifier()
