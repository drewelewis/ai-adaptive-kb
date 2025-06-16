import os
from typing import List, Optional, Type
from langchain_core.callbacks import  CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field, field_validator

from dotenv import load_dotenv
load_dotenv(override=True)



class Article():

    class BaseModel(BaseModel):
        id: int = Field(..., description="ID of the article")
        knowledge_base_id: int = Field(..., description="ID of the knowledge base")
        title: str = Field(..., description="Title of the article")
        content: str = Field(..., description="Content of the article")
        author_id: int = Field(..., description="ID of the author (user)")
        parent_id: Optional[int] = Field(None, description="ID of the parent article, if any")

    class InsertModel(BaseModel):
        knowledge_base_id: int = Field(..., description="ID of the knowledge base")
        title: str = Field(..., description="Title of the article")
        content: str = Field(..., description="Content of the article")
        author_id: int = Field(..., description="ID of the author (user)")
        parent_id: Optional[int] = Field(None, description="ID of the parent article, if any")
            
    class UpdateModel(BaseModel):
        knowledge_base_id: int = Field(..., description="ID of the knowledge base")
        title: str = Field(..., description="Title of the article")
        content: str = Field(..., description="Content of the article")
        author_id: int = Field(..., description="ID of the author (user)")
        parent_id: Optional[int] = Field(None, description="ID of the parent article, if any")


    # Init above tools and make available
    def __init__(self) -> None:
        self.models = [self.InsertModel,self.UpdateModel, self.BaseModel]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def models(self) -> List[BaseModel]:
        return self.models
