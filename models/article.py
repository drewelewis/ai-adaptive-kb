import os
from typing import List, Optional, Type
# Removed unused LangChain imports that were causing hanging
from pydantic import BaseModel as PydanticBaseModel, Field, field_validator

from dotenv import load_dotenv
load_dotenv(override=True)



class Article():

    class BaseModel(PydanticBaseModel):
        id: int = Field(..., description="ID of the article")
        knowledge_base_id: int = Field(..., description="ID of the knowledge base")
        title: str = Field(..., description="Title of the article")
        content: str = Field(..., description="Content of the article")
        author_id: int = Field(..., description="ID of the author (user)")
        parent_id: Optional[int] = Field(None, description="ID of the parent article, if any")

    class InsertModel(PydanticBaseModel):
        knowledge_base_id: int = Field(..., description="ID of the knowledge base")
        title: str = Field(..., description="Title of the article")
        content: str = Field(..., description="Content of the article")
        author_id: int = Field(..., description="ID of the author (user)")
        parent_id: Optional[int] = Field(None, description="ID of the parent article, if any")
            
    class UpdateModel(PydanticBaseModel):
        knowledge_base_id: int = Field(..., description="ID of the knowledge base")
        title: str = Field(..., description="Title of the article")
        content: str = Field(..., description="Content of the article")
        author_id: int = Field(..., description="ID of the author (user)")
        parent_id: Optional[int] = Field(None, description="ID of the parent article, if any")

    class HierarchyModel(PydanticBaseModel):
        knowledge_base_id: int = Field(..., description="ID of the knowledge base")
        id: int = Field(..., description="ID of the article")
        title: str = Field(..., description="Title of the article")
        author: str = Field(..., description="Name of the author (user)")
        parent_id: Optional[int] = Field(None, description="ID of the parent article, if any")

    # Init above tools and make available
    def __init__(self) -> None:
        self.models = [self.InsertModel,self.UpdateModel, self.BaseModel]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def models(self) -> List[PydanticBaseModel]:
        return self.models
