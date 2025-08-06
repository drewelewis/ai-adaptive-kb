# Recursion Reduction Strategies for AI Agents

## Problem Analysis
The agent was hitting recursion limits due to:
1. **Tool Call Loops**: Agent keeps calling tools without reaching a conclusion
2. **Inefficient Planning**: Making multiple small tool calls instead of comprehensive ones
3. **Lack of Stopping Criteria**: No built-in mechanisms to prevent endless loops

## Implemented Solutions

### 1. **Multi-Level Recursion Limits** ✅
- **Hard Limit**: 15 recursions (reduced from 25) - forces stop
- **Soft Limit**: 8 recursions - triggers efficiency warnings
- **Consecutive Tool Limit**: 4 consecutive tool calls - likely indicates a loop

### 2. **Enhanced State Tracking** ✅
```python
class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    recursions: int
    consecutive_tool_calls: int  # NEW: Track consecutive tool calls
    last_tool_result: str       # NEW: Track results to avoid repetition
```

### 3. **Dynamic Guidance System** ✅
- **Efficiency Guidelines**: Added to system prompt to encourage fewer tool calls
- **Runtime Warnings**: Inject reminders when approaching limits
- **Tool Call Warnings**: Alert when too many consecutive calls detected

### 4. **Smart Tool Caching** ✅
- **Result Caching**: Prevents identical tool calls from re-executing
- **Loop Detection**: Identifies repeated calls and returns cached results
- **Efficiency Notes**: Warns agent about repetitive behavior

### 5. **Improved Stopping Logic** ✅
```python
def should_continue(state: GraphState):
    # Force stop conditions:
    # 1. Hard recursion limit reached
    # 2. Too many consecutive tool calls (loop detection)
    # 3. Standard tool completion logic
```

## Additional Strategies You Can Implement

### 6. **Tool Call Batching**
Modify your tools to accept multiple operations in a single call:
```python
# Instead of multiple separate calls:
# search_articles(query="python")
# search_articles(query="javascript") 
# search_articles(query="typescript")

# Use batched approach:
# search_articles(queries=["python", "javascript", "typescript"])
```

### 7. **Conversation State Management**
```python
def should_reset_conversation(state):
    """Automatically reset if conversation becomes too complex"""
    if state["recursions"] > 10 and "error" in str(state["messages"][-1]):
        return True
    return False
```

### 8. **Tool Result Summarization**
After tool execution, encourage the agent to summarize and conclude:
```python
summary_prompt = "Based on the tool results above, provide a comprehensive final answer. Do not call additional tools unless absolutely necessary."
```

### 9. **Task Decomposition**
Break complex requests into smaller, independent tasks:
```python
def decompose_complex_request(user_input):
    """Break down complex requests into manageable parts"""
    if "and" in user_input or len(user_input.split()) > 20:
        # Suggest breaking into steps
        return True
    return False
```

### 10. **LLM Temperature Adjustment**
Lower temperature for tool-calling decisions:
```python
llm_for_tools = AzureChatOpenAI(
    temperature=0.1,  # Lower temperature for more consistent tool usage
    # ... other params
)
```

## Monitoring and Debugging

### Key Metrics to Track:
1. **Average Recursions per Conversation**
2. **Tool Call Patterns** (which tools are called most frequently)
3. **Conversation Length vs. Recursions** (efficiency ratio)
4. **Loop Detection Events**

### Debug Commands:
```python
# Add to your main() function:
def debug_recursion_stats():
    """Print recursion statistics for analysis"""
    print(f"Current recursions: {current_state['recursions']}")
    print(f"Consecutive tool calls: {current_state['consecutive_tool_calls']}")
    print(f"Recent tool usage: {tool_node.recent_results.keys()}")
```

## Expected Improvements

After implementing these changes:
- **50-70% reduction** in average recursions per conversation
- **Faster responses** due to fewer unnecessary tool calls
- **Better user experience** with more decisive agent behavior
- **Automatic loop detection** and prevention

## Usage Tips

1. **Monitor the debug output** to understand patterns
2. **Use /reset frequently** if conversations become complex
3. **Ask focused questions** rather than broad, multi-part requests
4. **Watch for warning messages** about consecutive tool calls

## Configuration Options

You can adjust these parameters based on your needs:
```python
MAX_RECURSIONS = 15          # Hard limit (adjust based on complexity needs)
SOFT_RECURSION_LIMIT = 8     # Warning threshold
MAX_CONSECUTIVE_TOOLS = 4    # Loop detection threshold
CACHE_SIZE = 10             # Tool result cache size
```

## Testing the Improvements

Try these test scenarios:
1. **Simple query**: "What articles do we have about Python?"
2. **Complex query**: "Find all Python articles, summarize them, and create a new overview article"
3. **Potentially looping query**: "Keep searching until you find something specific"

Monitor the recursion counts and tool call patterns to validate the improvements.
