import os
from typing import List, Optional, Type
from langchain_core.callbacks import  CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field, field_validator

from dotenv import load_dotenv
load_dotenv(override=True)

from operations.teamcity_operations import TeamcityOperations

teamcity_Operations=TeamcityOperations()

class TeamCityTools():
    
    class TeamCityGetProjectsTool(BaseTool):
        name: str = "TeamCityGetProjectsTool"
        description: str = "useful for when you need get a list of projects from a TeamCity server"
        return_direct: bool = True
               
        def _run(self) -> str:
            project_ids=teamcity_Operations.get_project_ids()
            return str(project_ids)
    
    class TeamCityGetBuildDefinitionsByProjectId(BaseTool):
        name: str = "TeamCityGetBuildDefinitionsByProjectId"
        description: str = """
            useful for when you need a build definition by project id from a TeamCity server.
        """.strip()
        return_direct: bool = False

        class TeamCityGetBuildDefinitionsByProjectIdInputModel(BaseModel):
            project_id: str = Field(description="project_id")

            # Validation method to check parameter input from agent
            @field_validator("project_id")
            def validate_query_param(project_id):
                if not project_id:
                    raise ValueError("TeamCityGetBuildDefinitionsByProjectId error: project_id parameter is empty")
                else:
                    return project_id
                
        args_schema: Optional[ArgsSchema] = TeamCityGetBuildDefinitionsByProjectIdInputModel
    
        def _run(self, project_id: str) -> str:
            builds=teamcity_Operations.get_build_definitions_by_project_id(project_id)
            return str(builds)

    # Init above tools and make available
    def __init__(self) -> None:
        self.tools = [self.TeamCityGetProjectsTool(), self.TeamCityGetBuildDefinitionsByProjectId()]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def tools(self) -> List[BaseTool]:
        return self.tools
