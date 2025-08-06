"""Test the updated intent classification for content gap analysis"""

# Simulate the updated intent analysis logic
def analyze_user_intent(user_message: str) -> str:
    """Analyze user message to determine intent"""
    user_message_lower = user_message.lower()
    
    # Knowledge base context commands
    if any(keyword in user_message_lower for keyword in ['use kb', 'switch to kb', 'select kb']):
        return "set_knowledge_base_context"
    
    # Content analysis and recommendations (check BEFORE create patterns to avoid conflicts)
    analysis_patterns = [
        'suggest content', 'suggest articles', 'content gaps', 'gaps in coverage',
        'review the kb', 'assess the kb', 'analyze the kb', 'improve the kb',
        'what can be added', 'articles that can be added', 'suggestions on articles',
        'general assessment', 'content analysis', 'make the kb better',
        'offer up content', 'look at my current kb', 'suggest new articles'
    ]
    if any(pattern in user_message_lower for pattern in analysis_patterns):
        return "analyze_content_gaps"
    
    # Knowledge base management intents (check these after analysis to avoid conflicts)
    if any(keyword in user_message_lower for keyword in ['create', 'add', 'new', 'insert']):
        if 'knowledge base' in user_message_lower:
            return "create_knowledge_base"
        elif 'article' in user_message_lower:
            return "create_article"
        elif 'tag' in user_message_lower:
            return "create_tag"
        else:
            return "create_content"
    
    # Article context commands - when user wants to focus on a specific article
    if any(pattern in user_message_lower for pattern in [
        'work on category', 'focus on category', 'work on article', 'focus on article',
        'work on main category', 'focus on main category', 'category ', 'article ',
        'work with category', 'focus on item', 'work on id', 'focus on id'
    ]):
        return "set_article_context"
    
    if any(keyword in user_message_lower for keyword in ['update', 'edit', 'modify', 'change']):
        return "update_content"
        
    if any(keyword in user_message_lower for keyword in ['delete', 'remove']):
        return "delete_content"
        
    if any(keyword in user_message_lower for keyword in ['search', 'find', 'look for', 'query']):
        return "search_content"
    
    # Check for filtered section requests (specific section + focus/display words)
    section_keywords = ['budget', 'investment', 'tax', 'insurance', 'estate', 'debt', 'income', 'retirement', 'real estate', 'healthcare']
    display_keywords = ['show', 'display', 'list', 'get', 'articles under', 'articles in', 'focus on', 'work on']
    focus_keywords = ['focus', 'work', 'concentrate', 'articles', 'content', 'under', 'in', 'section']
    
    # Context reference patterns - when user refers to previous context with "that", "it", etc.
    context_reference_patterns = [
        'hierarchy under that', 'under that', 'articles under that', 'content under that',
        'under it', 'articles under it', 'content under it', 'hierarchy under it',
        'show me under', 'list under', 'get under', 'display under'
    ]
    
    has_section = any(section in user_message_lower for section in section_keywords)
    has_display = any(display in user_message_lower for display in display_keywords)
    has_focus = any(word in user_message_lower for word in focus_keywords)
    has_context_reference = any(pattern in user_message_lower for pattern in context_reference_patterns)
    
    # Match patterns like "focus on budgeting", "work on investment", "get budgeting articles", etc.
    # OR contextual references like "hierarchy under that", "articles under that"
    if (has_section and (has_display or has_focus)) or has_context_reference:
        return "retrieve_filtered_content"
        
    if any(keyword in user_message_lower for keyword in ['show', 'display', 'list', 'get', 'hierarchy']):
        return "retrieve_content"
        
    if any(keyword in user_message_lower for keyword in ['help', 'how', 'what', 'explain']):
        return "help_request"
        
    return "general_inquiry"

# Test the problematic user inputs
test_cases = [
    "can you review the kb and offer up content that can be created?",
    "can you review the overall kb and suggest content that could make the kb better?",
    "I want to expand on topics that have gaps in coverage.",
    "yes, I am looking for a general assessment.",
    "No, I want you to look at my current kb and make suggestions on articles that can be added.",
    "suggest new articles",
    "what content gaps exist?",
    "analyze the knowledge base"
]

print("Testing Content Gap Analysis Intent Classification:")
print("=" * 60)

for test_input in test_cases:
    intent = analyze_user_intent(test_input)
    expected = "analyze_content_gaps"
    status = "✅ CORRECT" if intent == expected else f"❌ WRONG (got: {intent})"
    print(f"Input: '{test_input}'")
    print(f"Intent: {intent} {status}")
    print("-" * 40)
