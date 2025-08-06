from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from dotenv import load_dotenv
load_dotenv(override=True)


class Tags():

    class BaseModel(BaseModel):
        id: int = Field(..., description="ID of the tag")
        name: str = Field(..., description="Name of the tag")
        knowledge_base_id: int = Field(..., description="ID of the knowledge base this tag belongs to")
        
        @field_validator('name')
        @classmethod
        def validate_name(cls, v):
            if not v or not v.strip():
                raise ValueError('Tag name cannot be empty')
            return v.strip().lower()  # Normalize tag names to lowercase

    class InsertModel(BaseModel):
        name: str = Field(..., description="Name of the tag")
        knowledge_base_id: int = Field(..., description="ID of the knowledge base this tag belongs to")
        
        @field_validator('name')
        @classmethod
        def validate_name(cls, v):
            if not v or not v.strip():
                raise ValueError('Tag name cannot be empty')
            return v.strip().lower()  # Normalize tag names to lowercase

    class UpdateModel(BaseModel):
        id: int = Field(..., description="ID of the tag")
        name: str = Field(..., description="Name of the tag")
        knowledge_base_id: int = Field(..., description="ID of the knowledge base this tag belongs to")
        
        @field_validator('name')
        @classmethod
        def validate_name(cls, v):
            if not v or not v.strip():
                raise ValueError('Tag name cannot be empty')
            return v.strip().lower()  # Normalize tag names to lowercase

    class ArticleTagsModel(BaseModel):
        article_id: int = Field(..., description="ID of the article")
        tag_id: int = Field(..., description="ID of the tag")

    class TagWithUsageModel(BaseModel):
        id: int = Field(..., description="ID of the tag")
        name: str = Field(..., description="Name of the tag")
        knowledge_base_id: int = Field(..., description="ID of the knowledge base this tag belongs to")
        usage_count: int = Field(0, description="Number of articles using this tag")

    # Init above models and make available
    def __init__(self) -> None:
        self.models = [self.InsertModel, self.UpdateModel, self.BaseModel, self.ArticleTagsModel, self.TagWithUsageModel]

    # Method to get models (for ease of use, made so class works similarly to LangChain toolkits)
    def models(self) -> List[BaseModel]:
        return self.models
