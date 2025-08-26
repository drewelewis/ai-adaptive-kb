from typing import List, Optional, Literal
from pydantic import BaseModel as PydanticBaseModel, Field

from dotenv import load_dotenv
load_dotenv(override=True)

# Define the status enum type to match the database
KnowledgeBaseStatus = Literal["to_do", "in_progress", "done"]


class KnowledgeBase():

    class BaseModel(PydanticBaseModel):
        id: int = Field(..., description="ID of the knowledge base")
        name: str = Field(..., description="Name of the knowledge base")
        description: str = Field(..., description="Description of the knowledge base")
        author_id: int = Field(..., description="ID of the author (user)")
        is_active: bool = Field(..., description="Is the knowledge base active?")
        gitlab_project_id: Optional[int] = Field(None, description="GitLab project ID for issue tracking and project management")
        status: KnowledgeBaseStatus = Field(..., description="Workflow status: to_do (ready to start), in_progress (actively working), done (completed)")

    class InsertModel(PydanticBaseModel):
        name: str = Field(..., description="Title of the article")
        description: str = Field(..., description="Content of the article")
        author_id: int = Field(..., description="ID of the author (user)")
        gitlab_project_id: Optional[int] = Field(None, description="GitLab project ID for issue tracking and project management")
        status: KnowledgeBaseStatus = Field(default="to_do", description="Workflow status: to_do (ready to start), in_progress (actively working), done (completed)")

    class UpdateModel(PydanticBaseModel):
        id: int = Field(..., description="ID of the knowledge base")
        name: str = Field(..., description="Name of the knowledge base")
        description: str = Field(..., description="Description of the knowledge base")
        author_id: int = Field(..., description="ID of the author (user)")
        is_active: bool = Field(..., description="Is the knowledge base active?")
        gitlab_project_id: Optional[int] = Field(None, description="GitLab project ID for issue tracking and project management")
        status: KnowledgeBaseStatus = Field(..., description="Workflow status: to_do (ready to start), in_progress (actively working), done (completed)")       
    


    # Init above tools and make available
    def __init__(self) -> None:
        self.models = [self.InsertModel, self.BaseModel]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def models(self) -> List[PydanticBaseModel]:
        return self.models
