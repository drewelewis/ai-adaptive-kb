import os
from typing import List, Optional, Type
from langchain_core.callbacks import  CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field, field_validator

from dotenv import load_dotenv
load_dotenv(override=True)

from operations.postgres_operations import PostgresOperations

postgres_Operations=PostgresOperations()

class PostgresTools():
    
    
    class KnowledgeBaseGetRootLevelArticles(BaseTool):
        name: str = "KnowledgeBaseGetRootLevelArticles"
        description: str = """
            useful for when you need to get root level articles in a Knowledge Base.
        """.strip()
        return_direct: bool = False

        def _run(self) -> str:
            articles=postgres_Operations.get_root_level_articles()
            return str(articles)


    class KnowledgeBaseGetChildArticlesByParentIds(BaseTool):
        name: str = "KnowledgeBaseGetChildArticlesByParentIds"
        description: str = """
            useful for when you need get child articles in a Knowledge Base for a given list of parent ids.
        """.strip()
        return_direct: bool = False

        class KnowledgeBaseGetChildArticlesByParentIdsInputModel(BaseModel):
            parent_ids: list[str] = Field(description="parent_ids")

            # Validation method to check parameter input from agent
            @field_validator("parent_ids")
            def validate_query_param(parent_ids):
                if not parent_ids:
                    raise ValueError("KnowledgeBaseGetChildArticlesByParentIds error: parent_ids parameter is empty")
                else:
                    return parent_ids
                
        args_schema: Optional[ArgsSchema] = KnowledgeBaseGetChildArticlesByParentIdsInputModel
    
        def _run(self, parent_ids: list[str]) -> str:
            articles=postgres_Operations.get_articles_by_parentids(parent_ids)
            return str(articles)
            

    # Init above tools and make available
    def __init__(self) -> None:
        self.tools = [self.KnowledgeBaseGetRootLevelArticles(), self.KnowledgeBaseGetChildArticlesByParentIds()]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def tools(self) -> List[BaseTool]:
        return self.tools
