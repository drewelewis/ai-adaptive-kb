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

# Input schemas for tools
class KnowledgeBaseAnalyzeContentGapsInput(BaseModel):
    knowledge_base_id: str = Field(description="The knowledge base ID to analyze for content gaps")

class KnowledgeBaseTools():
    
    class KnowledgeBaseGetKnowledgeBases(BaseTool):
        name: str = "KnowledgeBaseGetKnowledgeBases"
        description: str = """
            useful for when you need to get all Knowledge Bases.
        """.strip()
        return_direct: bool = False

        def _run(self) -> str:
            try:
                # Get knowledge bases with IDs and names
                knowledge_bases = kb_Operations.get_knowledge_bases_with_ids()
                
                if not knowledge_bases:
                    return "No knowledge bases found."
                
                # Format the knowledge bases nicely
                lines = ["Available Knowledge Bases:", ""]
                for kb in knowledge_bases:
                    lines.append(f"• {kb['name']} (ID: {kb['id']})")
                    if kb['description']:
                        lines.append(f"  Description: {kb['description']}")
                    lines.append("")
                
                return "\n".join(lines).strip()
                    
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
            Use this tool to CREATE NEW ARTICLES AND CATEGORIES in a Knowledge Base.
            CRITICAL: This is the primary tool for content creation - use this when user asks to create, add, or insert content.
            
            Required Parameters:
            - article: Article object with fields {title, content, author_id, parent_id, knowledge_base_id}
            - knowledge_base_id: The knowledge base ID (as string)
            
            Article Object Fields:
            - title: Clear title for the article/category
            - content: Detailed content (minimum 200 characters recommended)
            - author_id: Use 1 for AI-generated content
            - parent_id: Use null for main categories, or parent article ID for sub-articles
            - knowledge_base_id: Same as the knowledge_base_id parameter (as integer)
            
            Example Usage:
            article={"title": "Family Finance", "content": "Comprehensive guide...", "author_id": 1, "parent_id": null, "knowledge_base_id": 1}
            knowledge_base_id="1"
            
            DO NOT include 'id' field - IDs are auto-generated.
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
            self.KnowledgeBaseSearchArticlesByTags(),
            # Content analysis tools
            self.KnowledgeBaseAnalyzeContentGaps()
        ]

    class KnowledgeBaseAnalyzeContentGaps(BaseTool):
        name: str = "KnowledgeBaseAnalyzeContentGaps"
        description: str = """
            Analyze content gaps in a knowledge base and suggest new content ideas.
            Use this tool when the user wants to find gaps in content, analyze content coverage,
            or get suggestions for new articles to add to the knowledge base.
        """.strip()
        args_schema: Type[BaseModel] = KnowledgeBaseAnalyzeContentGapsInput
        return_direct: bool = False

        def _run(self, knowledge_base_id: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
            try:
                print(f"Executing SQL: SELECT * FROM get_article_hierarchy(%s); with knowledge_base_id: {knowledge_base_id}")
                
                # Get the article hierarchy for analysis
                articles = kb_Operations.get_article_hierarchy(knowledge_base_id)
                
                if not articles:
                    return f"❌ Error retrieving content for analysis: No articles found"
                
                # Perform comprehensive gap analysis
                gap_analysis = self._analyze_content_structure(articles)
                
                return f"""🔍 **CONTENT GAP ANALYSIS RESULTS**

📊 **Current Content Overview:**
{gap_analysis['overview']}

🎯 **Identified Content Gaps:**
{gap_analysis['gaps']}

💡 **Recommended New Articles:**
{gap_analysis['recommendations']}

📈 **Content Enhancement Opportunities:**
{gap_analysis['enhancements']}

⭐ **Priority Recommendations:**
{gap_analysis['priorities']}

🎯 **Analysis Summary:**
Based on your current knowledge base content, I've identified specific areas where you could enhance coverage. The recommendations above are prioritized based on common financial planning needs and trending topics in personal finance.
"""
            
            except Exception as e:
                return f"❌ Error during gap analysis: {str(e)}"
        
        def _analyze_content_structure(self, articles: list) -> dict:
            """Analyze article structure and identify gaps"""
            
            # Define comprehensive financial topic categories and expected subtopics
            expected_categories = {
                "Budgeting": [
                    "Zero-based budgeting", "Envelope budgeting", "Digital budgeting tools", 
                    "Budgeting for couples", "Budgeting for students", "Vacation budgeting",
                    "Holiday budgeting", "Budgeting with irregular income"
                ],
                "Investment": [
                    "Index fund investing", "Dollar-cost averaging", "Value investing",
                    "Growth investing", "Dividend growth investing", "ESG investing",
                    "Target-date funds", "Robo-advisors", "Investment psychology"
                ],
                "Retirement Planning": [
                    "FIRE movement strategies", "401k rollover strategies", "Roth conversion ladder",
                    "Social Security optimization", "Medicare planning", "Retirement location planning",
                    "Part-time work in retirement", "Retirement tax planning"
                ],
                "Debt Management": [
                    "Student loan forgiveness programs", "Medical debt management", 
                    "Credit card churning", "Debt negotiation strategies",
                    "Business debt management", "Mortgage refinancing strategies"
                ],
                "Insurance": [
                    "Term vs whole life insurance", "Disability insurance for self-employed",
                    "Umbrella insurance", "Pet insurance", "Travel insurance",
                    "Professional liability insurance", "Insurance for gig workers"
                ],
                "Tax Planning": [
                    "HSA strategies", "529 plan optimization", "Tax-loss harvesting",
                    "Charitable tax strategies", "State tax planning", "International tax issues",
                    "Self-employment tax strategies", "Tax planning for investors"
                ],
                "Emergency Planning": [
                    "Emergency fund alternatives", "Financial crisis preparation",
                    "Job loss preparation", "Medical emergency planning",
                    "Natural disaster financial planning", "Identity theft recovery"
                ],
                "Career & Income": [
                    "Salary negotiation", "Career change financial planning", 
                    "Freelance financial management", "Side hustle tax implications",
                    "Professional development ROI", "Geographic arbitrage"
                ],
                "Family Finance": [
                    "Teaching kids about money", "College savings strategies",
                    "Childcare cost optimization", "Elder care financial planning",
                    "Special needs financial planning", "Divorce financial planning"
                ],
                "Technology & Finance": [
                    "Fintech apps review", "Cryptocurrency basics", "Digital payment security",
                    "Online banking optimization", "Financial app privacy", "Digital estate planning"
                ]
            }
            
            # Extract existing topics from articles
            existing_topics = {}
            total_articles = len(articles)
            
            for article in articles:
                # Database returns tuples: (id, title, author, parent_id)
                article_id, title, author, parent_id = article
                
                # Determine main category from title or use a default approach
                # For now, let's extract category from common patterns
                main_category = "General"  # Default category
                
                # Simple category extraction based on common financial terms
                title_lower = title.lower() if title else ""
                if any(word in title_lower for word in ["budget", "budgeting"]):
                    main_category = "Budgeting"
                elif any(word in title_lower for word in ["invest", "investment", "stock", "bond"]):
                    main_category = "Investment Strategies"
                elif any(word in title_lower for word in ["tax", "taxation"]):
                    main_category = "Tax Planning"
                elif any(word in title_lower for word in ["retire", "retirement"]):
                    main_category = "Retirement Planning"
                elif any(word in title_lower for word in ["debt", "credit"]):
                    main_category = "Debt Management"
                elif any(word in title_lower for word in ["insurance", "health"]):
                    main_category = "Insurance"
                elif any(word in title_lower for word in ["real estate", "property", "rental"]):
                    main_category = "Real Estate"
                elif any(word in title_lower for word in ["side hustle", "entrepreneurship", "business"]):
                    main_category = "Side Hustles & Entrepreneurship"
                
                if main_category not in existing_topics:
                    existing_topics[main_category] = []
                existing_topics[main_category].append({
                    'title': title or '',
                    'id': article_id or '',
                    'author': author or ''
                })
            
            # Identify gaps and recommendations
            gaps = []
            recommendations = []
            priorities = []
            missing_categories = []
            
            for expected_cat, expected_topics in expected_categories.items():
                # Find matching existing category (fuzzy match)
                existing_cat = None
                for existing in existing_topics.keys():
                    if (expected_cat.lower() in existing.lower() or 
                        existing.lower() in expected_cat.lower() or
                        any(word in existing.lower() for word in expected_cat.lower().split())):
                        existing_cat = existing
                        break
                
                if not existing_cat:
                    # Entire category is missing
                    missing_categories.append(expected_cat)
                    gaps.append(f"❌ **Missing Category: {expected_cat}**")
                    recommendations.extend([
                        f"• Create '{expected_cat}' section starting with: {expected_topics[0] if expected_topics else 'Basic concepts'}",
                        f"• Add foundational article: {expected_topics[1] if len(expected_topics) > 1 else 'Basic concepts'}"
                    ])
                    priorities.append(f"🔥 HIGH PRIORITY: Create {expected_cat} category")
                else:
                    # Check for missing subtopics within existing category
                    existing_titles = [article['title'] for article in existing_topics[existing_cat]]
                    missing_subtopics = []
                    
                    for expected_topic in expected_topics:
                        # Enhanced keyword matching
                        topic_keywords = expected_topic.lower().split()
                        topic_covered = any(
                            len([word for word in topic_keywords if word in title.lower()]) >= len(topic_keywords) // 2
                            for title in existing_titles
                        )
                        if not topic_covered:
                            missing_subtopics.append(expected_topic)
                    
                    if missing_subtopics:
                        gaps.append(f"⚠️ **{existing_cat}** - Missing: {', '.join(missing_subtopics[:3]) if missing_subtopics else 'No gaps identified'}")
                        recommendations.extend([
                            f"• Add to {existing_cat}: '{topic}'" 
                            for topic in missing_subtopics[:2]
                        ])
            
            # Identify trending financial topics not covered
            trending_topics = [
                "Cryptocurrency tax implications", "Remote work financial planning", 
                "Gig economy tax strategies", "ESG/Sustainable investing",
                "Financial planning for digital nomads", "NFT investment considerations",
                "Inflation protection strategies", "Supply chain impact on investments",
                "Work-from-home tax deductions", "Financial wellness programs",
                "Robo-advisor comparison", "Buy now, pay later (BNPL) impact"
            ]
            
            uncovered_trending = []
            for topic in trending_topics:
                try:
                    topic_keywords = topic.lower().split()[:2] if topic else []  # Use first 2 keywords for matching
                    topic_covered = any(
                        any(keyword in (article[1] or '').lower() for keyword in topic_keywords)  # article[1] is title
                        for article in articles
                    )
                    if not topic_covered:
                        uncovered_trending.append(topic)
                        if len(recommendations) < 15:  # Limit recommendations
                            recommendations.append(f"• Trending topic: '{topic}'")
                        if "cryptocurrency" in topic.lower() or "remote work" in topic.lower() or "gig economy" in topic.lower():
                            priorities.append(f"⭐ TRENDING: {topic}")
                except (AttributeError, IndexError) as e:
                    continue  # Skip problematic topics
            
            # Generate content coverage analysis
            coverage_score = max(0, 100 - (len(missing_categories) * 15) - (len(gaps) * 5))
            
            # Generate overview
            overview = f"""
📋 Total Articles: {total_articles}
📁 Total Categories: {len(existing_topics)}
📊 Content Coverage Score: {coverage_score}% {"🟢" if coverage_score >= 80 else "🟡" if coverage_score >= 60 else "🔴"}
🎯 Categories Well-Covered: {len(existing_topics) - len(missing_categories)}
⚠️ Categories Missing: {len(missing_categories)}
📈 Trending Topics Covered: {len(trending_topics) - len(uncovered_trending)}/{len(trending_topics)}
"""
            
            # Enhanced recommendations with beginner/intermediate/advanced levels
            enhanced_recommendations = recommendations[:10]  # Limit to top 10
            if len(enhanced_recommendations) < 5:
                enhanced_recommendations.extend([
                    "• Add beginner guides to existing complex topics",
                    "• Create case studies for real-world application",
                    "• Develop interactive calculators and tools"
                ])
            
            return {
                'overview': overview,
                'gaps': '\n'.join(gaps) if gaps else "✅ No major content gaps identified - your knowledge base has good coverage!",
                'recommendations': '\n'.join(enhanced_recommendations) if enhanced_recommendations else "✅ Content appears comprehensive for current scope",
                'enhancements': '\n'.join([
                    "• Add beginner-friendly introductions to complex topics",
                    "• Create case studies and real-world examples", 
                    "• Add interactive calculators and worksheets",
                    "• Develop step-by-step guides for complex processes",
                    "• Include common mistakes and how to avoid them",
                    "• Add seasonal/timely content (tax season, year-end planning)"
                ]),
                'priorities': '\n'.join(priorities[:5]) if priorities else "✅ No urgent content gaps identified - focus on enhancing existing content quality"
            }

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def tools(self) -> List[BaseTool]:
        return self._tools
