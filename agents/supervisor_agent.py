from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from agents.base_agent import BaseAgent
from agents.agent_types import AgentState, AgentMessage
from prompts.multi_agent_prompts import prompts


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent - Orchestrates workflows between agents and manages task coordination.
    This agent serves as the central coordinator for complex multi-step operations.
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        system_prompt = prompts.supervisor_prompt()
        super().__init__("Supervisor", llm, system_prompt)
    
    def process(self, state: AgentState) -> AgentState:
        """Process coordination requests and manage workflows"""
        self.log("Processing supervision request")
        
        # Check for messages from other agents
        agent_messages = state.get("agent_messages", [])
        
        # Find messages for this agent
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        if not my_messages:
            self.log("No messages found for Supervisor")
            return state
        
        # Get the latest message
        latest_message = my_messages[-1]
        
        # Analyze the request and determine workflow
        workflow_plan = self._analyze_and_plan(latest_message)
        
        # Update task context
        state["task_context"] = {
            "workflow_plan": workflow_plan,
            "current_step": 0,
            "total_steps": len(workflow_plan["steps"]),
            "original_request": latest_message.content
        }
        
        # Execute the workflow
        state = self._execute_workflow(state, workflow_plan)
        
        return state
    
    def _analyze_and_plan(self, request_message: AgentMessage) -> Dict[str, Any]:
        """Analyze the request and create a workflow plan"""
        user_intent = request_message.metadata.get("intent", "general_inquiry")
        content = request_message.content
        
        self.log(f"Analyzing request with intent: {user_intent}")
        
        # Use LLM to analyze and create workflow plan
        analysis_prompt = f"""
Analyze this user request and create a detailed workflow plan:

User Intent: {user_intent}
User Request: {content}

Create a workflow plan that includes:
1. Required operations in logical sequence
2. Knowledge base validation steps
3. Error handling considerations
4. Expected outcomes

Respond with a clear plan for the Content Management Agent.
        """
        
        messages = [
            self.get_system_message(),
            HumanMessage(content=analysis_prompt)
        ]
        
        response = self.llm.invoke(messages)
        plan_content = response.content
        
        # Create structured workflow plan
        workflow_plan = {
            "intent": user_intent,
            "description": plan_content,
            "steps": self._extract_workflow_steps(user_intent, content),
            "validation_required": self._requires_validation(user_intent),
            "risk_level": self._assess_risk_level(user_intent)
        }
        
        return workflow_plan
    
    def _extract_workflow_steps(self, intent: str, content: str) -> List[Dict[str, Any]]:
        """Extract specific workflow steps based on intent"""
        steps = []
        
        if intent == "set_knowledge_base_context":
            steps = [
                {"action": "extract_kb_id", "description": "Extract knowledge base ID from user request"},
                {"action": "validate_kb_exists", "description": "Validate knowledge base exists"},
                {"action": "set_context", "description": "Set knowledge base context"},
                {"action": "confirm_context", "description": "Confirm context change to user"}
            ]
        elif intent == "set_article_context":
            steps = [
                {"action": "extract_article_id", "description": "Extract article ID from user request"},
                {"action": "validate_article_exists", "description": "Validate article exists in current KB"},
                {"action": "set_article_context", "description": "Set article working context"},
                {"action": "confirm_article_context", "description": "Confirm article context to user"}
            ]
        elif intent == "create_knowledge_base":
            steps = [
                {"action": "validate_kb_creation", "description": "Validate knowledge base creation request"},
                {"action": "create_kb", "description": "Create new knowledge base"},
                {"action": "confirm_creation", "description": "Confirm successful creation"}
            ]
        elif intent == "create_article":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "get_kb_structure", "description": "Retrieve current knowledge base structure"},
                {"action": "validate_article_placement", "description": "Determine appropriate article placement"},
                {"action": "create_article", "description": "Create the new article"},
                {"action": "update_hierarchy", "description": "Display updated hierarchy"}
            ]
        elif intent == "update_content":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "locate_content", "description": "Find the content to update"},
                {"action": "update_content", "description": "Perform the update operation"},
                {"action": "validate_update", "description": "Confirm update was successful"}
            ]
        elif intent == "retrieve_content":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "retrieve_content", "description": "Retrieve requested content"},
                {"action": "format_response", "description": "Format response for user"}
            ]
        elif intent == "retrieve_filtered_content":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "identify_section", "description": "Identify the specific section to filter by"},
                {"action": "retrieve_hierarchy", "description": "Retrieve full article hierarchy"},
                {"action": "filter_section_content", "description": "Filter to show only the requested section and its children"},
                {"action": "format_filtered_response", "description": "Format filtered response showing only the requested section"}
            ]
        elif intent == "search_content":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "search_content", "description": "Perform search operation"},
                {"action": "format_results", "description": "Format search results"}
            ]
        elif intent == "analyze_content_gaps":
            steps = [
                {"action": "validate_kb_context", "description": "Ensure knowledge base context is established"},
                {"action": "retrieve_full_hierarchy", "description": "Get complete knowledge base structure"},
                {"action": "analyze_content_coverage", "description": "Analyze existing content for gaps and opportunities"},
                {"action": "identify_missing_topics", "description": "Identify potential topics that could enhance the knowledge base"},
                {"action": "generate_content_recommendations", "description": "Generate specific article recommendations with rationale"}
            ]
        else:
            steps = [
                {"action": "analyze_request", "description": "Analyze the request"},
                {"action": "execute_operation", "description": "Execute appropriate operation"},
                {"action": "format_response", "description": "Format response"}
            ]
        
        return steps
    
    def _requires_validation(self, intent: str) -> bool:
        """Determine if the operation requires user validation"""
        high_risk_operations = ["create_knowledge_base", "delete_content", "update_content"]
        return intent in high_risk_operations
    
    def _assess_risk_level(self, intent: str) -> str:
        """Assess the risk level of the operation"""
        if intent in ["delete_content"]:
            return "high"
        elif intent in ["create_knowledge_base", "update_content"]:
            return "medium"
        else:
            return "low"
    
    def _execute_workflow(self, state: AgentState, workflow_plan: Dict[str, Any]) -> AgentState:
        """Execute the planned workflow"""
        self.log(f"Executing workflow: {workflow_plan['intent']}")
        
        # Create message for Content Management Agent
        cm_message = self.create_message(
            recipient="ContentManagement",
            message_type="workflow_request",
            content=f"Execute workflow for: {workflow_plan['intent']}",
            metadata={
                "workflow_plan": workflow_plan,
                "original_request": state.get("task_context", {}).get("original_request", "")
            }
        )
        
        # Add to agent messages
        if "agent_messages" not in state:
            state["agent_messages"] = []
        state["agent_messages"].append(cm_message)
        
        # Set Content Management Agent as next active agent
        state["current_agent"] = "ContentManagement"
        
        self.log("Workflow delegated to Content Management Agent")
        
        return state
    
    def process_cm_response(self, state: AgentState, cm_response: AgentMessage) -> AgentState:
        """Process response from Content Management Agent"""
        self.log("Processing response from Content Management Agent")
        
        # Extract results from CM response
        results = cm_response.metadata.get("results", {})
        success = cm_response.metadata.get("success", False)
        
        # Create response for User Proxy Agent
        if success:
            user_response = self.create_message(
                recipient="UserProxy",
                message_type="workflow_complete",
                content=f"Operation completed successfully: {cm_response.content}",
                metadata={"results": results, "success": True}
            )
        else:
            user_response = self.create_message(
                recipient="UserProxy", 
                message_type="workflow_error",
                content=f"Operation encountered an issue: {cm_response.content}",
                metadata={"error": results, "success": False}
            )
        
        # Add to agent messages
        state["agent_messages"].append(user_response)
        
        # Set User Proxy as next agent to respond to user
        state["current_agent"] = "UserProxy"
        
        self.log("Response prepared for User Proxy Agent")
        
        return state
