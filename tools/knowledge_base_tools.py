import os
from typing import List, Optional, Type, Dict, Any
from langchain_core.callbacks import  CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field, field_validator
from models.article import Article
from models.knowledge_base import KnowledgeBase
from models.tags import Tags

from dotenv import load_dotenv
load_dotenv(override=True)

from operations.knowledge_base_operations import KnowledgeBaseOperations

kb_Operations=KnowledgeBaseOperations()

class KnowledgeBaseTools():
    
    class KnowledgeBaseGetKnowledgeBases(BaseTool):
        name: str = "KnowledgeBaseGetKnowledgeBases"
        description: str = """
            useful for when you need to get all Knowledge Bases.
        """.strip()
        return_direct: bool = False

        def _run(self) -> str:
            try:
                # Get raw knowledge bases data
                raw_kb_data = kb_Operations.get_knowledge_bases()
                
                # Parse and format the knowledge bases nicely
                if isinstance(raw_kb_data, str) and raw_kb_data.startswith('['):
                    # Handle string representation of list
                    import ast
                    try:
                        # Convert string back to list (this is a workaround for the current implementation)
                        kb_list_str = raw_kb_data
                        # Extract meaningful data using string parsing since we get string representation
                        lines = []
                        lines.append("Available Knowledge Bases:")
                        lines.append("")
                        
                        # Simple parsing to extract ID and name from the string
                        import re
                        id_matches = re.findall(r"'id': (\d+)", kb_list_str)
                        name_matches = re.findall(r"'name': '([^']+)'", kb_list_str)
                        desc_matches = re.findall(r"'description': '([^']+)'", kb_list_str)
                        
                        for i, (kb_id, name, desc) in enumerate(zip(id_matches, name_matches, desc_matches)):
                            lines.append(f"  📚 ID: {kb_id}")
                            lines.append(f"     Name: {name}")
                            lines.append(f"     Description: {desc}")
                            lines.append("")
                        
                        return "\n".join(lines)
                        
                    except Exception as parse_error:
                        return f"Error parsing knowledge bases: {parse_error}\nRaw data: {raw_kb_data}"
                
                elif isinstance(raw_kb_data, list) and len(raw_kb_data) == 0:
                    return "No knowledge bases found. You may want to create a new one."
                
                else:
                    return f"Available Knowledge Bases:\n{raw_kb_data}"
                    
            except Exception as e:
                return f"Error retrieving knowledge bases: {e}"

    class KnowledgeBaseSetContext(BaseTool):
        name: str = "KnowledgeBaseSetContext"
        description: str = """
            useful for when you need to set the current knowledge base context.
            This establishes which knowledge base should be used for subsequent operations.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseSetContextInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id to set as current context")

            @field_validator("knowledge_base_id")
            def validate_knowledge_base_id(cls, knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseSetContext error: knowledge_base_id parameter is empty")
                return knowledge_base_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseSetContextInputModel
    
        def _run(self, knowledge_base_id: str) -> Dict[str, Any]:
            # Validate that the knowledge base exists
            kb = kb_Operations.get_knowledge_base_by_id(knowledge_base_id)
            if not kb:
                return {
                    "success": False,
                    "error": f"Knowledge base with ID {knowledge_base_id} not found"
                }
            
            return {
                "success": True,
                "knowledge_base_id": knowledge_base_id,
                "knowledge_base_name": kb.name,
                "message": f"Knowledge base context set to: {kb.name} (ID: {knowledge_base_id})"
            }

    class KnowledgeBaseSetArticleContext(BaseTool):
        name: str = "KnowledgeBaseSetArticleContext"
        description: str = """
            useful for when you need to set focus on a specific article within the knowledge base.
            This establishes which article should be the current working context for detailed operations.
            Use this when user says things like "work on article 1", "focus on category 1", "main article 1", etc.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseSetArticleContextInputModel(BaseModel):
            article_id: str = Field(description="article_id to set as current context")
            knowledge_base_id: str = Field(description="knowledge_base_id containing the article")

            @field_validator("article_id")
            def validate_article_id(cls, article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseSetArticleContext error: article_id parameter is empty")
                return article_id

            @field_validator("knowledge_base_id")
            def validate_knowledge_base_id(cls, knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseSetArticleContext error: knowledge_base_id parameter is empty")
                return knowledge_base_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseSetArticleContextInputModel
    
        def _run(self, knowledge_base_id: str, article_id: str) -> Dict[str, Any]:
            # Validate that the article exists
            article = kb_Operations.get_article_by_id(knowledge_base_id, article_id)
            if not article:
                return {
                    "success": False,
                    "error": f"Article with ID {article_id} not found in knowledge base {knowledge_base_id}"
                }
            
            return {
                "success": True,
                "knowledge_base_id": knowledge_base_id,
                "article_id": article_id,
                "article_title": article.title,
                "message": f"Article context set to: {article.title} (ID: {article_id})"
            }
        
    class KnowledgeBaseInsertKnowledgeBase(BaseTool):
        name: str = "KnowledgeBaseInsertKnowledgeBase"
        description: str = """
            useful for when you need to insert a new Knowledge Base.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseInsertKnowledgeBaseInputModel(BaseModel):
            knowledge_base: KnowledgeBase.InsertModel = Field(description="knowledge_base")

            # Validation method to check parameter input from agent
            @field_validator("knowledge_base")
            def validate_query_param(knowledge_base):
                if not knowledge_base:
                    raise ValueError("KnowledgeBaseInsertKnowledgeBase error: knowledge_base parameter is empty")
                else:
                    return knowledge_base
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseInsertKnowledgeBaseInputModel
    
        def _run(self, knowledge_base: KnowledgeBase.InsertModel) -> KnowledgeBase.BaseModel:
            knowledge_base=kb_Operations.insert_knowledge_base(knowledge_base)
            return knowledge_base
    
    # KonowledgeBase Update KnowledgeBase
    class KnowledgeBaseUpdateKnowledgeBase(BaseTool):
        name: str = "KnowledgeBaseUpdateKnowledgeBase"
        description: str = """
            useful for when you need to update a Knowledge Base.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseUpdateKnowledgeBaseInputModel(BaseModel):
            knowledge_base: KnowledgeBase.UpdateModel = Field(description="knowledge_base")

            # Validation method to check parameter input from agent
            @field_validator("knowledge_base")
            def validate_query_param(knowledge_base):
                if not knowledge_base:
                    raise ValueError("KnowledgeBaseUpdateKnowledgeBase error: knowledge_base parameter is empty")
                else:
                    return knowledge_base
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseUpdateKnowledgeBaseInputModel
    
        def _run(self, knowledge_base: KnowledgeBase.UpdateModel) -> KnowledgeBase.BaseModel:
            knowledge_base=kb_Operations.update_knowledge_base(knowledge_base)
            return knowledge_base
        

    class KnowledgeBaseGetArticleHierarchy(BaseTool):
        name: str = "KnowledgeBaseGetArticleHierarchy"
        description: str = """
            useful for when you need to get all articles in a Knowledge Base as a hierarchy.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetArticleHierarchyInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetArticleHierarchyInputModel error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                
        def _run(self, knowledge_base_id: str) -> str:
            articles=kb_Operations.get_article_hierarchy(knowledge_base_id)
            return str(articles)
          
    class KnowledgeBaseGetRootLevelArticles(BaseTool):
        name: str = "KnowledgeBaseGetRootLevelArticles"
        description: str = """
            useful for when you need to get root level articles in a Knowledge Base.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetRootLevelArticlesInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetRootLevelArticlesInputModel error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                
        def _run(self, knowledge_base_id: str) -> str:
            articles=kb_Operations.get_root_level_articles(knowledge_base_id)
            return str(articles)

    class KnowledgeBaseGetArticleByArticleId(BaseTool):
        name: str = "KnowledgeBaseGetArticleByArticleId"
        description: str = """
            useful for when you need get articles in a Knowledge Base for a given article_id.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetArticleByArticleIdInputModel(BaseModel):
            article_id: str = Field(description="article_id")
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("article_id")
            def validate_query_param(article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseGetArticleByArticleId error: article_id parameter is empty")
                else:
                    return article_id
            
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetArticleByArticleId error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                    
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetArticleByArticleIdInputModel
    
        def _run(self, knowledge_base_id: str, article_id: str) -> str:
            article=kb_Operations.get_article_by_id(knowledge_base_id, article_id)
            return str(article)

    class KnowledgeBaseGetChildArticlesByParentIds(BaseTool):
        name: str = "KnowledgeBaseGetChildArticlesByParentIds"
        description: str = """
            useful for when you need get child articles in a Knowledge Base for a given list of parent ids.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetChildArticlesByParentIdsInputModel(BaseModel):
            parent_ids: list[str] = Field(description="parent_ids")
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("parent_ids")
            def validate_query_param(parent_ids):
                if not parent_ids:
                    raise ValueError("KnowledgeBaseGetChildArticlesByParentIds error: parent_ids parameter is empty")
                else:
                    return parent_ids
            
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetChildArticlesByParentIds error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                    
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetChildArticlesByParentIdsInputModel
    
        def _run(self, knowledge_base_id: str, parent_ids: list[str]) -> str:
            articles=kb_Operations.get_articles_by_parentids(knowledge_base_id, parent_ids)
            return str(articles)
        
    class KnowledgeBaseInsertArticle(BaseTool):
        name: str = "KnowledgeBaseInsertArticle"
        description: str = """
            useful for when you need to add an article to a Knowledge Base.
            IMPORTANT: Do NOT include an 'id' field in the article object - IDs are auto-generated.
            Article must contain: title, content, author_id, parent_id, knowledge_base_id.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseInsertArticleInputModel(BaseModel):
            article: Article.InsertModel = Field(description="article")
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("article")
            def validate_query_param(article):
                if not article:
                    raise ValueError("KnowledgeBaseInsertArticle error: article parameter is empty")
                else:
                    return article
                
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseInsertArticle error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                   
        args_schema: Optional[ArgsSchema] = KnowledgeBaseInsertArticleInputModel
    
        def _run(self, knowledge_base_id: str, article: Article.InsertModel) -> Article.BaseModel:
            article=kb_Operations.insert_article(knowledge_base_id, article)
            return article
        
    # KnowledgeBase UpdateArticle
    class KnowledgeBaseUpdateArticle(BaseTool):
        name: str = "KnowledgeBaseUpdateArticle"
        description: str = """
            useful for when you need to update an article in a Knowledge Base.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseUpdateArticleInputModel(BaseModel):
            article: Article.UpdateModel = Field(description="article")
            knowledge_base_id: str = Field(description="knowledge_base_id")

            # Validation method to check parameter input from agent
            @field_validator("article")
            def validate_query_param(article):
                if not article:
                    raise ValueError("KnowledgeBaseUpdateArticle error: article parameter is empty")
                else:
                    return article
                
            @field_validator("knowledge_base_id")
            def validate_query_param(knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseInsertArticle error: knowledge_base_id parameter is empty")
                else:
                    return knowledge_base_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseUpdateArticleInputModel
    
        def _run(self, knowledge_base_id: str, article: Article.UpdateModel) -> Article.BaseModel:
            article=kb_Operations.update_article(knowledge_base_id, article)
            return article

    # =============================================
    # TAG MANAGEMENT TOOLS
    # =============================================
    
    class KnowledgeBaseGetTagsByKnowledgeBase(BaseTool):
        name: str = "KnowledgeBaseGetTagsByKnowledgeBase"
        description: str = """
            useful for when you need to get all tags for a specific knowledge base.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetTagsByKnowledgeBaseInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id")

            @field_validator("knowledge_base_id")
            def validate_query_param(cls, knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetTagsByKnowledgeBase error: knowledge_base_id parameter is empty")
                return knowledge_base_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetTagsByKnowledgeBaseInputModel
    
        def _run(self, knowledge_base_id: str) -> List[Tags.BaseModel]:
            tags = kb_Operations.get_tags_by_knowledge_base(knowledge_base_id)
            return tags

    class KnowledgeBaseGetTagById(BaseTool):
        name: str = "KnowledgeBaseGetTagById"
        description: str = """
            useful for when you need to get a specific tag by its ID.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetTagByIdInputModel(BaseModel):
            tag_id: str = Field(description="tag_id")

            @field_validator("tag_id")
            def validate_query_param(cls, tag_id):
                if not tag_id:
                    raise ValueError("KnowledgeBaseGetTagById error: tag_id parameter is empty")
                return tag_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetTagByIdInputModel
    
        def _run(self, tag_id: str) -> Optional[Tags.BaseModel]:
            tag = kb_Operations.get_tag_by_id(tag_id)
            return tag

    class KnowledgeBaseInsertTag(BaseTool):
        name: str = "KnowledgeBaseInsertTag"
        description: str = """
            useful for when you need to create a new tag in a knowledge base.
            The tag name will be automatically normalized to lowercase.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseInsertTagInputModel(BaseModel):
            tag: Tags.InsertModel = Field(description="tag to insert")

            @field_validator("tag")
            def validate_query_param(cls, tag):
                if not tag:
                    raise ValueError("KnowledgeBaseInsertTag error: tag parameter is empty")
                return tag
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseInsertTagInputModel
    
        def _run(self, tag: Tags.InsertModel) -> Optional[Tags.BaseModel]:
            new_tag = kb_Operations.insert_tag(tag)
            return new_tag

    class KnowledgeBaseUpdateTag(BaseTool):
        name: str = "KnowledgeBaseUpdateTag"
        description: str = """
            useful for when you need to update an existing tag.
            The tag name will be automatically normalized to lowercase.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseUpdateTagInputModel(BaseModel):
            tag: Tags.UpdateModel = Field(description="tag to update")

            @field_validator("tag")
            def validate_query_param(cls, tag):
                if not tag:
                    raise ValueError("KnowledgeBaseUpdateTag error: tag parameter is empty")
                return tag
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseUpdateTagInputModel
    
        def _run(self, tag: Tags.UpdateModel) -> Optional[Tags.BaseModel]:
            updated_tag = kb_Operations.update_tag(tag)
            return updated_tag

    class KnowledgeBaseDeleteTag(BaseTool):
        name: str = "KnowledgeBaseDeleteTag"
        description: str = """
            useful for when you need to delete a tag. This will also remove the tag from all articles.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseDeleteTagInputModel(BaseModel):
            tag_id: str = Field(description="tag_id to delete")

            @field_validator("tag_id")
            def validate_query_param(cls, tag_id):
                if not tag_id:
                    raise ValueError("KnowledgeBaseDeleteTag error: tag_id parameter is empty")
                return tag_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseDeleteTagInputModel
    
        def _run(self, tag_id: str) -> bool:
            result = kb_Operations.delete_tag(tag_id)
            return result

    # =============================================
    # ARTICLE-TAG RELATIONSHIP TOOLS
    # =============================================

    class KnowledgeBaseGetTagsForArticle(BaseTool):
        name: str = "KnowledgeBaseGetTagsForArticle"
        description: str = """
            useful for when you need to get all tags associated with a specific article.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetTagsForArticleInputModel(BaseModel):
            article_id: str = Field(description="article_id")

            @field_validator("article_id")
            def validate_query_param(cls, article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseGetTagsForArticle error: article_id parameter is empty")
                return article_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetTagsForArticleInputModel
    
        def _run(self, article_id: str) -> List[Tags.BaseModel]:
            tags = kb_Operations.get_tags_for_article(article_id)
            return tags

    class KnowledgeBaseGetArticlesForTag(BaseTool):
        name: str = "KnowledgeBaseGetArticlesForTag"
        description: str = """
            useful for when you need to get all articles that have a specific tag.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetArticlesForTagInputModel(BaseModel):
            tag_id: str = Field(description="tag_id")

            @field_validator("tag_id")
            def validate_query_param(cls, tag_id):
                if not tag_id:
                    raise ValueError("KnowledgeBaseGetArticlesForTag error: tag_id parameter is empty")
                return tag_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetArticlesForTagInputModel
    
        def _run(self, tag_id: str) -> List[Article.BaseModel]:
            articles = kb_Operations.get_articles_for_tag(tag_id)
            return articles

    class KnowledgeBaseAddTagToArticle(BaseTool):
        name: str = "KnowledgeBaseAddTagToArticle"
        description: str = """
            useful for when you need to add a tag to an article.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseAddTagToArticleInputModel(BaseModel):
            article_id: str = Field(description="article_id")
            tag_id: str = Field(description="tag_id")

            @field_validator("article_id")
            def validate_article_id(cls, article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseAddTagToArticle error: article_id parameter is empty")
                return article_id

            @field_validator("tag_id")
            def validate_tag_id(cls, tag_id):
                if not tag_id:
                    raise ValueError("KnowledgeBaseAddTagToArticle error: tag_id parameter is empty")
                return tag_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseAddTagToArticleInputModel
    
        def _run(self, article_id: str, tag_id: str) -> bool:
            result = kb_Operations.add_tag_to_article(article_id, tag_id)
            return result

    class KnowledgeBaseRemoveTagFromArticle(BaseTool):
        name: str = "KnowledgeBaseRemoveTagFromArticle"
        description: str = """
            useful for when you need to remove a tag from an article.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseRemoveTagFromArticleInputModel(BaseModel):
            article_id: str = Field(description="article_id")
            tag_id: str = Field(description="tag_id")

            @field_validator("article_id")
            def validate_article_id(cls, article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseRemoveTagFromArticle error: article_id parameter is empty")
                return article_id

            @field_validator("tag_id")
            def validate_tag_id(cls, tag_id):
                if not tag_id:
                    raise ValueError("KnowledgeBaseRemoveTagFromArticle error: tag_id parameter is empty")
                return tag_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseRemoveTagFromArticleInputModel
    
        def _run(self, article_id: str, tag_id: str) -> bool:
            result = kb_Operations.remove_tag_from_article(article_id, tag_id)
            return result

    class KnowledgeBaseSetArticleTags(BaseTool):
        name: str = "KnowledgeBaseSetArticleTags"
        description: str = """
            useful for when you need to set all tags for an article (replaces existing tags).
            Provide a list of tag IDs to associate with the article.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseSetArticleTagsInputModel(BaseModel):
            article_id: str = Field(description="article_id")
            tag_ids: List[str] = Field(description="list of tag_ids to associate with the article")

            @field_validator("article_id")
            def validate_article_id(cls, article_id):
                if not article_id:
                    raise ValueError("KnowledgeBaseSetArticleTags error: article_id parameter is empty")
                return article_id

            @field_validator("tag_ids")
            def validate_tag_ids(cls, tag_ids):
                if tag_ids is None:
                    return []
                return tag_ids
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseSetArticleTagsInputModel
    
        def _run(self, article_id: str, tag_ids: List[str]) -> bool:
            result = kb_Operations.set_article_tags(article_id, tag_ids)
            return result

    # =============================================
    # ADVANCED TAG TOOLS
    # =============================================

    class KnowledgeBaseGetTagsWithUsageCount(BaseTool):
        name: str = "KnowledgeBaseGetTagsWithUsageCount"
        description: str = """
            useful for when you need to get all tags with their usage statistics (how many articles use each tag).
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetTagsWithUsageCountInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id")

            @field_validator("knowledge_base_id")
            def validate_query_param(cls, knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseGetTagsWithUsageCount error: knowledge_base_id parameter is empty")
                return knowledge_base_id
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetTagsWithUsageCountInputModel
    
        def _run(self, knowledge_base_id: str) -> List[Tags.TagWithUsageModel]:
            tags = kb_Operations.get_tags_with_usage_count(knowledge_base_id)
            return tags

    class KnowledgeBaseSearchArticlesByTags(BaseTool):
        name: str = "KnowledgeBaseSearchArticlesByTags"
        description: str = """
            useful for when you need to search for articles by tag names.
            Set match_all=True to find articles that have ALL specified tags.
            Set match_all=False to find articles that have ANY of the specified tags.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseSearchArticlesByTagsInputModel(BaseModel):
            knowledge_base_id: str = Field(description="knowledge_base_id")
            tag_names: List[str] = Field(description="list of tag names to search for")
            match_all: bool = Field(default=False, description="if True, articles must have ALL tags; if False, articles must have ANY tag")

            @field_validator("knowledge_base_id")
            def validate_knowledge_base_id(cls, knowledge_base_id):
                if not knowledge_base_id:
                    raise ValueError("KnowledgeBaseSearchArticlesByTags error: knowledge_base_id parameter is empty")
                return knowledge_base_id

            @field_validator("tag_names")
            def validate_tag_names(cls, tag_names):
                if not tag_names or len(tag_names) == 0:
                    raise ValueError("KnowledgeBaseSearchArticlesByTags error: tag_names parameter is empty")
                return tag_names
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseSearchArticlesByTagsInputModel
    
        def _run(self, knowledge_base_id: str, tag_names: List[str], match_all: bool = False) -> List[Article.BaseModel]:
            articles = kb_Operations.search_articles_by_tags(knowledge_base_id, tag_names, match_all)
            return articles
        
    # Init above tools and make available
    def __init__(self) -> None:
        self._tools = [
            # Knowledge Base tools
            self.KnowledgeBaseGetKnowledgeBases(), 
            self.KnowledgeBaseSetContext(),
            self.KnowledgeBaseSetArticleContext(),
            self.KnowledgeBaseInsertKnowledgeBase(), 
            self.KnowledgeBaseUpdateKnowledgeBase(),
            # Article tools
            self.KnowledgeBaseGetRootLevelArticles(), 
            self.KnowledgeBaseGetChildArticlesByParentIds(), 
            self.KnowledgeBaseInsertArticle(), 
            self.KnowledgeBaseUpdateArticle(), 
            self.KnowledgeBaseGetArticleHierarchy(), 
            self.KnowledgeBaseGetArticleByArticleId(),
            # Tag management tools
            self.KnowledgeBaseGetTagsByKnowledgeBase(),
            self.KnowledgeBaseGetTagById(),
            self.KnowledgeBaseInsertTag(),
            self.KnowledgeBaseUpdateTag(),
            self.KnowledgeBaseDeleteTag(),
            # Article-Tag relationship tools
            self.KnowledgeBaseGetTagsForArticle(),
            self.KnowledgeBaseGetArticlesForTag(),
            self.KnowledgeBaseAddTagToArticle(),
            self.KnowledgeBaseRemoveTagFromArticle(),
            self.KnowledgeBaseSetArticleTags(),
            # Advanced tag tools
            self.KnowledgeBaseGetTagsWithUsageCount(),
            self.KnowledgeBaseSearchArticlesByTags()
        ]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def tools(self) -> List[BaseTool]:
        return self._tools
