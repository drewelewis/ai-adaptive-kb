import os
from typing import List, Optional, Type
from langchain_core.callbacks import  CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field, field_validator
from models.article import Article
from models.knowledge_base import KnowledgeBase

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

        def _run(self) -> List[KnowledgeBase.BaseModel]:
            knowledge_bases=kb_Operations.get_knowledge_bases()
            return knowledge_bases
        
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
        
    # Init above tools and make available
    def __init__(self) -> None:
        self._tools = [self. KnowledgeBaseGetKnowledgeBases(), self.KnowledgeBaseInsertKnowledgeBase(), self.KnowledgeBaseGetRootLevelArticles(), self.KnowledgeBaseGetChildArticlesByParentIds(), self.KnowledgeBaseInsertArticle(), self.KnowledgeBaseUpdateArticle(), self.KnowledgeBaseGetArticleHierarchy(), self.KnowledgeBaseGetArticleByArticleId(), self.KnowledgeBaseUpdateKnowledgeBase()    ]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def tools(self) -> List[BaseTool]:
        return self._tools
