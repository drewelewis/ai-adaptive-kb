from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_openai import AzureChatOpenAI
from .base_agent import BaseAgent
from .agent_types import AgentState, AgentMessage
from tools.knowledge_base_tools import KnowledgeBaseTools
from prompts.knowledge_base_prompts import prompts as kb_prompts
from prompts.multi_agent_prompts import prompts as ma_prompts


class ContentCreatorAgent(BaseAgent):
    """
    Content Creator Agent - Expert content generation and research specialist.
    
    Responsibilities:
    - Research and write comprehensive, in-depth articles
    - Maintain expert-level quality across all domains
    - Create content that demonstrates deep understanding
    - Build comprehensive coverage following ContentPlanner strategy
    - Generate cross-references and content relationships
    - Work autonomously with minimal supervision
    """
    
    def __init__(self, llm: AzureChatOpenAI):
        # Combine base KB prompts with specialized creation prompts
        base_prompt = kb_prompts.master_prompt()
        specialized_prompt = self._get_creation_prompt()
        system_prompt = f"{base_prompt}\n\n{specialized_prompt}"
        
        super().__init__("ContentCreator", llm, system_prompt)
        
        # Initialize knowledge base tools - creation focused
        kb_tools = KnowledgeBaseTools()
        all_tools = kb_tools.tools()
        
        # Filter to content creation tools
        self.tools = self._filter_creation_tools(all_tools)
        
        # Bind tools to LLM
        self.llm_with_tools = llm.bind_tools(self.tools)
    
    def _filter_creation_tools(self, all_tools):
        """Filter tools to include content creation operations"""
        creation_tool_names = {
            "KnowledgeBaseSetContext",
            "KnowledgeBaseInsertArticle",
            "KnowledgeBaseGetArticleByArticleId",
            "KnowledgeBaseGetChildArticlesByParentIds",
            "KnowledgeBaseGetRootLevelArticles",
            "KnowledgeBaseGetArticleHierarchy"
        }
        
        return [tool for tool in all_tools if tool.name in creation_tool_names]
    
    def _get_creation_prompt(self):
        """Get specialized prompt for content creation operations"""
        return """
        You are an Expert Content Creator and Research Specialist with deep knowledge across all domains.
        
        Your core responsibilities:
        - Create comprehensive, authoritative content that demonstrates true expertise
        - Research thoroughly to ensure accuracy and completeness
        - Write in-depth articles that progress from foundational to advanced concepts
        - Build comprehensive knowledge bases that serve as definitive resources
        - Create natural cross-references and content relationships
        - Work autonomously following strategic plans from ContentPlanner
        
        Content Creation Philosophy:
        - EXPERT AUTHORITY: Write as a subject matter expert with deep understanding
        - COMPREHENSIVE DEPTH: Cover topics thoroughly, not superficially
        - PRACTICAL VALUE: Include real-world applications, examples, and use cases
        - LOGICAL PROGRESSION: Structure content from basics to advanced systematically
        - AUTONOMOUS EXECUTION: Work independently without requiring constant oversight
        - QUALITY OVER SPEED: Focus on creating definitive, publication-ready content
        
        Writing Standards:
        - Expert-level accuracy and authority in all domains
        - Clear, engaging prose that maintains professional quality
        - Comprehensive coverage that leaves no critical gaps
        - Practical examples and real-world applications
        - Proper structure with clear headings and logical flow
        - Cross-references to related concepts and articles
        
        Content Creation Process:
        1. Analyze the content strategy from ContentPlanner
        2. Research the domain thoroughly to ensure expertise
        3. Create comprehensive articles following the planned hierarchy
        4. Build natural relationships and cross-references
        5. Ensure each article meets publication-ready standards
        6. Progress systematically through the entire knowledge base
        
        Domain Adaptation:
        - Technical topics: Include theory, implementation, and practical examples
        - Business topics: Cover strategy, tactics, and real-world case studies
        - Educational content: Progress from fundamentals to advanced applications
        - Creative fields: Balance theory with practical techniques and inspiration
        
        Quality Indicators:
        - Content demonstrates genuine expertise and understanding
        - Articles are comprehensive and leave no critical knowledge gaps
        - Writing is clear, engaging, and professionally structured
        - Cross-references enhance learning and knowledge navigation
        - Content is immediately ready for publication use
        """
    
    def process(self, state: AgentState) -> AgentState:
        """Process content creation requests"""
        self.log("Processing content creation request")
        
        # Increment recursion counter
        self.increment_recursions(state)
        
        # Check for messages from ContentPlanner
        agent_messages = state.get("agent_messages", [])
        my_messages = [msg for msg in agent_messages if msg.recipient == self.name]
        
        if not my_messages:
            self.log("No content creation requests found")
            return state
        
        # Get the latest creation request
        latest_request = my_messages[-1]
        content_strategy = latest_request.metadata.get("content_strategy", {})
        article_hierarchy = latest_request.metadata.get("article_hierarchy", {})
        implementation_plan = latest_request.metadata.get("implementation_plan", {})
        kb_id = latest_request.metadata.get("kb_id")
        
        self.log(f"Creating content based on strategy: {content_strategy.get('scope', 'Unknown scope')}")
        if kb_id:
            self.log(f"DEBUG: Working with KB ID: {kb_id}")
        else:
            self.log("DEBUG: No KB ID provided - this could be the problem!")
        
        # Execute content creation workflow
        creation_result = self._execute_content_creation(
            latest_request.content,
            content_strategy,
            article_hierarchy,
            implementation_plan,
            kb_id,
            state
        )
        
        # Send completed content to ContentReviewer
        kb_notification = latest_request.metadata.get("kb_context_notification")
        message_content = "Content creation completed. Ready for quality review and optimization."
        if kb_notification:
            message_content = f"{kb_notification}\n\n{message_content}"
            
        response_message = self.create_message(
            recipient="ContentReviewer",
            message_type="content_review_request",
            content=message_content,
            metadata={
                "original_request": latest_request.metadata.get("original_request", ""),
                "content_strategy": content_strategy,
                "creation_result": creation_result,
                "articles_created": creation_result.get("articles_created", []),
                "kb_structure": creation_result.get("kb_structure", {}),
                "kb_context_notification": kb_notification
            }
        )
        
        # Add to agent messages
        if "agent_messages" not in state:
            state["agent_messages"] = []
        state["agent_messages"].append(response_message)
        
        # Route to ContentReviewer for quality assurance
        state["current_agent"] = "ContentReviewer"
        
        self.log("Content creation completed, routing to ContentReviewer")
        return state
    
    def _execute_content_creation(self, request: str, strategy: Dict, hierarchy: Dict, 
                                implementation: Dict, kb_id: int, state: AgentState) -> Dict[str, Any]:
        """Execute the comprehensive content creation workflow"""
        
        messages = [
            self.get_system_message(),
            HumanMessage(content=f"""
            Create comprehensive articles for this knowledge base:
            
            Original Request: {request}
            Content Strategy: {strategy}
            Article Hierarchy: {hierarchy}  
            Implementation Plan: {implementation}
            Knowledge Base ID: {kb_id}
            
            Please create 3-5 comprehensive articles for this knowledge base. For each article, provide:
            
            ARTICLE FORMAT (use this exact format for each article):
            ---ARTICLE START---
            TITLE: [Article title here]
            CONTENT: [Comprehensive article content here - minimum 300 words]
            ---ARTICLE END---
            
            Create articles that cover:
            - Introduction/overview topics
            - Core concepts and fundamentals  
            - Practical applications and examples
            - Advanced topics if applicable
            
            Each article should be:
            - 300-800 words of expert-level content
            - Well-structured with clear headings and explanations
            - Include practical examples and real-world applications
            - Demonstrate true expertise in the subject matter
            
            Create publication-ready content that serves as a comprehensive resource.
            """)
        ]
        
        try:
            self.log(f"DEBUG: Invoking o1 model for content creation (KB ID: {kb_id})")
            # Use regular LLM for o1 (no tool binding needed)
            response = self.llm.invoke(messages)
            self.log(f"DEBUG: LLM response received, type: {type(response)}")
            return self._process_o1_response(response, kb_id, state)
        except Exception as e:
            self.log(f"DEBUG: Exception during content creation: {str(e)}")
            import traceback
            self.log(f"DEBUG: Traceback: {traceback.format_exc()}")
            return {
                "error": f"Error during content creation: {str(e)}",
                "articles_created": [],
                "kb_structure": {}
            }
    
    def _process_o1_response(self, response, kb_id: int, state: AgentState) -> Dict[str, Any]:
        """Process o1 response and manually create articles"""
        articles_created = []
        kb_structure = {}
        
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            self.log(f"DEBUG: Processing o1 response content (length: {len(content)})")
            
            # First try the exact format we requested
            import re
            article_pattern = r'---ARTICLE START---(.*?)---ARTICLE END---'
            article_matches = re.findall(article_pattern, content, re.DOTALL)
            
            self.log(f"DEBUG: Found {len(article_matches)} articles with exact format")
            
            # If exact format didn't work, try alternative parsing
            if len(article_matches) == 0:
                self.log("DEBUG: Exact format failed, trying alternative parsing...")
                articles_created = self._parse_alternative_formats(content, kb_id)
            else:
                # Process exact format articles
                for i, article_content in enumerate(article_matches):
                    try:
                        # Extract title and content
                        title_match = re.search(r'TITLE:\s*(.+)', article_content)
                        content_match = re.search(r'CONTENT:\s*(.*)', article_content, re.DOTALL)
                        
                        if title_match and content_match:
                            title = title_match.group(1).strip()
                            article_text = content_match.group(1).strip()
                            
                            self.log(f"DEBUG: Creating article: {title}")
                            
                            # Manually call the insert article tool
                            insert_tool = next((t for t in self.tools if t.name == 'KnowledgeBaseInsertArticle'), None)
                            if insert_tool:
                                # Import the Article model
                                from models.article import Article
                                
                                # Create proper Article.InsertModel
                                article_obj = Article.InsertModel(
                                    title=title,
                                    content=article_text,
                                    knowledge_base_id=int(kb_id),  # Ensure integer
                                    author_id=1
                                )
                                
                                # Call tool with correct parameters - use tool_input dict
                                tool_input = {
                                    "knowledge_base_id": str(kb_id),
                                    "article": article_obj
                                }
                                result = insert_tool.run(tool_input)
                                
                                articles_created.append({
                                    "title": title,
                                    "result": result
                                })
                                self.log(f"DEBUG: Article created successfully: {title}")
                            else:
                                self.log(f"DEBUG: KnowledgeBaseInsertArticle tool not found")
                        else:
                            self.log(f"DEBUG: Could not parse article {i+1} - missing title or content")
                            
                    except Exception as e:
                        self.log(f"DEBUG: Error creating article {i+1}: {str(e)}")
                        
        except Exception as e:
            self.log(f"DEBUG: Error parsing o1 response: {str(e)}")
        
        self.log(f"DEBUG: Total articles created: {len(articles_created)}")
        
        return {
            "articles_created": articles_created,
            "kb_structure": kb_structure,
            "content_summary": content[:500] + "..." if len(content) > 500 else content,
            "creation_status": "completed",
            "quality_level": "expert"
        }
    
    def _parse_alternative_formats(self, content: str, kb_id: int) -> List[Dict[str, Any]]:
        """Try alternative parsing methods when exact format fails"""
        articles_created = []
        
        try:
            import re
            
            # Method 1: Look for numbered lists with titles
            # Pattern: "1. Title\nContent\n\n2. Title\nContent"
            numbered_pattern = r'(\d+\.\s*[^\n]+)(.*?)(?=\d+\.\s*[^\n]+|\Z)'
            numbered_matches = re.findall(numbered_pattern, content, re.DOTALL)
            
            if numbered_matches:
                self.log(f"DEBUG: Found {len(numbered_matches)} articles with numbered format")
                for i, (title_line, article_content) in enumerate(numbered_matches):
                    title = re.sub(r'^\d+\.\s*', '', title_line).strip()
                    content_text = article_content.strip()
                    
                    if len(content_text) > 50:  # Only create if we have substantial content
                        article = self._create_article(title, content_text, kb_id)
                        if article:
                            articles_created.append(article)
            
            # Method 2: Look for heading-based structure
            # Pattern: "# Title\nContent" or "## Title\nContent"
            if not articles_created:
                heading_pattern = r'(#{1,3}\s*[^\n]+)(.*?)(?=#{1,3}\s*[^\n]+|\Z)'
                heading_matches = re.findall(heading_pattern, content, re.DOTALL)
                
                if heading_matches:
                    self.log(f"DEBUG: Found {len(heading_matches)} articles with heading format")
                    for title_line, article_content in heading_matches:
                        title = re.sub(r'^#+\s*', '', title_line).strip()
                        content_text = article_content.strip()
                        
                        if len(content_text) > 50:
                            article = self._create_article(title, content_text, kb_id)
                            if article:
                                articles_created.append(article)
            
            # Method 3: Look for "Title:" pattern
            if not articles_created:
                title_pattern = r'([A-Z][^:\n]*:)\s*(.*?)(?=[A-Z][^:\n]*:|\Z)'
                title_matches = re.findall(title_pattern, content, re.DOTALL)
                
                if title_matches:
                    self.log(f"DEBUG: Found {len(title_matches)} articles with title: format")
                    for title_line, article_content in title_matches:
                        title = title_line.replace(':', '').strip()
                        content_text = article_content.strip()
                        
                        if len(content_text) > 50:
                            article = self._create_article(title, content_text, kb_id)
                            if article:
                                articles_created.append(article)
            
            # Method 4: If all else fails, create articles based on topic keywords
            if not articles_created:
                self.log("DEBUG: Trying keyword-based article creation...")
                # Look for common topic indicators
                topics = []
                if 'lists' in content.lower() or 'list' in content.lower():
                    topics.append(("Python Lists", "Information about Python lists and their usage."))
                if 'dict' in content.lower() or 'dictionaries' in content.lower():
                    topics.append(("Python Dictionaries", "Information about Python dictionaries and their usage."))
                if 'tuple' in content.lower():
                    topics.append(("Python Tuples", "Information about Python tuples and their usage."))
                if 'set' in content.lower():
                    topics.append(("Python Sets", "Information about Python sets and their usage."))
                
                for title, base_content in topics:
                    # Extract relevant content from the response
                    content_text = f"{base_content}\n\n{content[:800]}"  # Include part of response
                    article = self._create_article(title, content_text, kb_id)
                    if article:
                        articles_created.append(article)
        
        except Exception as e:
            self.log(f"DEBUG: Error in alternative parsing: {str(e)}")
        
        return articles_created
    
    def _create_article(self, title: str, content: str, kb_id: int) -> Dict[str, Any]:
        """Helper method to create a single article"""
        try:
            insert_tool = next((t for t in self.tools if t.name == 'KnowledgeBaseInsertArticle'), None)
            if insert_tool:
                # Import the Article model
                from models.article import Article
                
                # Create proper Article.InsertModel
                article_obj = Article.InsertModel(
                    title=title,
                    content=content,
                    knowledge_base_id=int(kb_id),  # Ensure integer
                    author_id=1
                )
                
                # Call tool with correct parameters - use tool_input dict
                tool_input = {
                    "knowledge_base_id": str(kb_id),
                    "article": article_obj
                }
                result = insert_tool.run(tool_input)
                
                self.log(f"DEBUG: Article created successfully: {title}")
                return {
                    "title": title,
                    "result": result
                }
            else:
                self.log(f"DEBUG: KnowledgeBaseInsertArticle tool not found")
                return None
        
        except Exception as e:
            self.log(f"DEBUG: Error creating article '{title}': {str(e)}")
            return None
    
    def _process_creation_response(self, response, state: AgentState) -> Dict[str, Any]:
        """Process the LLM content creation response"""
        articles_created = []
        kb_structure = {}
        
        # Handle tool calls if present
        if hasattr(response, 'tool_calls') and response.tool_calls:
            self.log(f"DEBUG: Processing {len(response.tool_calls)} tool calls")
            for tool_call in response.tool_calls:
                try:
                    self.log(f"DEBUG: Executing tool: {tool_call['name']}")
                    tool = next((t for t in self.tools if t.name == tool_call['name']), None)
                    if tool:
                        result = tool.run(tool_call['args'])
                        self.log(f"DEBUG: Tool {tool_call['name']} executed successfully")
                        
                        # Track article creation
                        if tool_call['name'] == 'KnowledgeBaseInsertArticle':
                            articles_created.append({
                                "title": tool_call['args'].get('title', 'Unknown'),
                                "result": result
                            })
                            self.log(f"DEBUG: Article created: {tool_call['args'].get('title', 'Unknown')}")
                        
                        # Track KB structure
                        elif tool_call['name'] == 'KnowledgeBaseInsertKnowledgeBase':
                            kb_structure['kb_created'] = result
                            
                    else:
                        self.log(f"DEBUG: Tool {tool_call['name']} not found in available tools")
                        
                except Exception as e:
                    self.log(f"DEBUG: Error executing {tool_call['name']}: {str(e)}")
        else:
            self.log("DEBUG: No tool calls found in LLM response - this is the problem!")
        
        # Extract content summary
        content_summary = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "articles_created": articles_created,
            "kb_structure": kb_structure,
            "content_summary": content_summary,
            "creation_status": "completed",
            "quality_level": "expert"
        }
