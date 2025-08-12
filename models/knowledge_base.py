from typing import List, Optional
from pydantic import BaseModel as PydanticBaseModel, Field

from dotenv import load_dotenv
load_dotenv(override=True)


class KnowledgeBase():

    class BaseModel(PydanticBaseModel):
        id: int = Field(..., description="ID of the knowledge base")
        name: str = Field(..., description="Name of the knowledge base")
        description: str = Field(..., description="Description of the knowledge base")
        author_id: int = Field(..., description="ID of the author (user)")
        is_active: bool = Field(..., description="Is the knowledge base active?")
        gitlab_project_id: Optional[int] = Field(None, description="GitLab project ID for issue tracking and project management")

    class InsertModel(PydanticBaseModel):
        name: str = Field(..., description="Title of the article")
        description: str = Field(..., description="Content of the article")
        author_id: int = Field(..., description="ID of the author (user)")
        gitlab_project_id: Optional[int] = Field(None, description="GitLab project ID for issue tracking and project management")

    class UpdateModel(PydanticBaseModel):
        id: int = Field(..., description="ID of the knowledge base")
        name: str = Field(..., description="Name of the knowledge base")
        description: str = Field(..., description="Description of the knowledge base")
        author_id: int = Field(..., description="ID of the author (user)")
        is_active: bool = Field(..., description="Is the knowledge base active?")
        gitlab_project_id: Optional[int] = Field(None, description="GitLab project ID for issue tracking and project management")       
    


    # Init above tools and make available
    def __init__(self) -> None:
        self.models = [self.InsertModel, self.BaseModel]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def models(self) -> List[PydanticBaseModel]:
        return self.models
