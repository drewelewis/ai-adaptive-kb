"""Test conversation memory and context retention"""

# Test the conversation history function
def test_conversation_history():
    from agents.agent_types import AgentState
    from langchain_core.messages import HumanMessage, AIMessage
    from agents.user_proxy_agent import UserProxyAgent
    
    # Create a mock agent
    agent = UserProxyAgent(agent_id="test")
    
    # Create a state with some conversation history
    state = AgentState(
        messages=[
            HumanMessage(content="can you analyze the current kb, and suggest areas where content can be added to make it more comprehensive?"),
            AIMessage(content="Here's the analysis..."),
            HumanMessage(content="can you analyze any gaps in the current content?"),
            AIMessage(content="Sure! I can analyze gaps..."),
            HumanMessage(content="I am referring to kb 1"),
            AIMessage(content="We're now set to use Knowledge Base #1..."),
            HumanMessage(content="I just explained what I wanted")
        ],
        current_agent="UserProxy",
        user_intent=None,
        knowledge_base_id="1", 
        article_id=None,
        agent_messages=[],
        recursions=0
    )
    
    # Test getting conversation history
    history = agent._get_recent_conversation_history(state, 3)
    print("Recent Conversation History:")
    print("=" * 50)
    print(history)
    print("=" * 50)
    
    # Test intent classification for gap analysis
    test_inputs = [
        "can you analyze any gaps in the current content?",
        "analyze gaps in kb 1", 
        "what's missing from the knowledge base?",
        "I just explained what I wanted"
    ]
    
    print("\nIntent Classification Test:")
    print("=" * 50)
    for test_input in test_inputs:
        intent = agent._analyze_user_intent(test_input)
        print(f"Input: '{test_input}'")
        print(f"Intent: {intent}")
        print("-" * 30)

if __name__ == "__main__":
    test_conversation_history()
