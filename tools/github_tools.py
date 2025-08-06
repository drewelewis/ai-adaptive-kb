import os
from typing import List, Optional, Type
from langchain_core.callbacks import  CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field, field_validator

from github import Github
from github import Auth
from dotenv import load_dotenv
load_dotenv(override=True)

from operations.github_operations import GitHubOperations

github_Operations=GitHubOperations()

class GithubTools():
    
    class GithubGetReposByUserTool(BaseTool):
        name: str = "GithubGetReposByUserTool"
        description: str = """
            A tool to get a list of repositories from a Github user account
            This tool is useful for when you need to get a list of repositories from a user.
            Before using this tool, you should have the username of the user.
            If you don't have the username, you can ask the user for it.
            Before getting a list of files in a repository, you should get the list of repositories using this tool.
        """.strip()
        return_direct: bool = False
        
        class GithubGetReposByUserToolInputModel(BaseModel):
            user: str = Field(description="user")

            # Validation method to check parameter input from agent
            @field_validator("user")
            def validate_query_param(user):
                if not user:
                    raise ValueError("GithubGetReposByUserTool error: user parameter is empty")
                else:
                    return user
            
        args_schema: Optional[ArgsSchema] = GithubGetReposByUserToolInputModel
     
        def _run(self, user: str) -> str:
            repos=github_Operations.get_repo_list_by_username(user)
            return str(repos)

    
            
    class GithubCreateIssueTool(BaseTool):
        name: str = "GithubCreateIssueTool"
        description: str = """
            A tool to create an issue in a Github repository.
            The repository should be in the format 'username/repo_name'.

        """.strip()
        return_direct: bool = False
    
        class GithubCreateIssueToolInputModel(BaseModel):
            repo: str = Field(description="repo"),
            title: str = Field(description="title"),
            body: str = Field(description="path")

            # Validation method to check parameter input from agent
            @field_validator("repo")
            def validate_query_param(repo):
                if not repo:
                    raise ValueError("GithubCreateIssueTool error: repo parameter is empty")
                else:
                    return repo
            
            @field_validator("title")
            def validate_query_param(title):
                if not title:
                    raise ValueError("GithubCreateIssueTool error: title parameter is empty")
                else:
                    return title
                
            @field_validator("body")
            def validate_query_param(body):
                if not body:
                    raise ValueError("GithubCreateIssueTool error: body parameter is empty")
                else:
                    return body
                
        args_schema: Optional[ArgsSchema] = GithubCreateIssueToolInputModel

        def _run(self, repo: str, title: str, body: str) -> str:
            issue=github_Operations.create_issue(repo,title,body)
            return str(issue)
            
    
    

    # Init above tools and make available
    def __init__(self) -> None:
        self._tools = [self.GithubGetReposByUserTool(), self.GithubCreateIssueTool()]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def tools(self) -> List[BaseTool]:
        return self._tools