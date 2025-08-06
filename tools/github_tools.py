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

    class GithubGetFilesByRepoTool(BaseTool):
        name: str = "GithubGetFilesByRepoTool"
        description: str = """
            A tool to get a list of files in a Github repository.
            The repository should be in the format 'username/repo_name'.
            This tool is useful for when you need to get a list of files in a repository.
            Before opening file content, you should get the list of files using this tool.
        """.strip()
        return_direct: bool = False
        
        class GithubGetFilesByRepoToolInputModel(BaseModel):
            repo: str = Field(description="repo")

            # Validation method to check parameter input from agent
            @field_validator("repo")
            def validate_query_param(repo):
                if not repo:
                    raise ValueError("GithubGetFilesByRepoTool error: repo parameter is empty")
                else:
                    return repo
            
        args_schema: Optional[ArgsSchema] = GithubGetFilesByRepoToolInputModel

        def _run(self, repo: str) -> str:
            files=github_Operations.get_file_list_by_repo(repo)
            return str(files)
    
    class GithubGetFileContentByRepoandPathTool(BaseTool):
        name: str = "GithubGetFileContentByRepoandPathTool"
        description: str = """
            A tool to get contents of files in a Github repository.
            This tool is useful for when you need to get the content of a file in a repository at a specific path.
        """.strip()
        return_direct: bool = False
        
        class GithubGetFileContentByRepoandPathToolInputModel(BaseModel):
            repo: str = Field(description="repo"),
            path: str = Field(description="path")

            # Validation method to check parameter input from agent
            @field_validator("repo")
            def validate_query_param(repo):
                if not repo:
                    raise ValueError("GithubGetFileContentByRepoandPathTool error: repo parameter is empty")
                else:
                    return repo
            
            @field_validator("path")
            def validate_query_param(path):
                if not path:
                    raise ValueError("GithubGetFileContentByRepoandPathTool error: path parameter is empty")
                else:
                    return path
        args_schema: Optional[ArgsSchema] = GithubGetFileContentByRepoandPathToolInputModel

        def _run(self, repo: str, path: str) -> str:
            content=github_Operations.get_file_content_by_repo_and_path(repo,path)
            return str(content)
            
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
            
    
    # class GithubCodeSearchTool(BaseTool):
    #     name: str = "GithubCodeSearchTool"
    #     description: str = """useful for when you need search for items from github.
    #     Before using this tool, you should have a repository name and a list of files in the repository.
    #     If you don't have the repository name and files, you can use the GithubGetReposByUserTool and GithubGetFilesByRepoTool to get them.
        
    #     Here are some example of queries:

    #     Find all instancesinstall repo:charles/privaterepo	 of install in code from the repository charles/privaterepo.

    #     shogun user:heroku	Find references to shogun from all public heroku repositories.

    #     join extension:coffee	Find all instances of join in code with coffee extension.

    #     system size:>1000	Find all instances of system in code of file size greater than 1000kbs.
        
    #     examples path:/docs/	Find all examples in the path /docs/.

    #     """.strip()
    #     return_direct: bool = True

    #     class CodeSearchQuery(BaseModel):
    #         query: str = Field(description="search query"),

    #          # Validation method to check parameter input from agent
    #         @field_validator("query")
    #         def validate_query_param(query):
    #             if not query:
    #                 raise ValueError("GithubGetReposTool error: query parameter is empty")
    #             else:
    #                 return query
        
    #     args_schema: Optional[ArgsSchema] = CodeSearchQuery

    #     def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
    #         """Use the tool"""
    #         code_snippets = github_Operations.search_code(query=query)
    #         if code_snippets:
    #             return str(code_snippets)
    #         else:
    #             return str("No code snippets found for the given query.")
        


            # To close connections after use
            g.close()
            return str("")

    # Init above tools and make available
    def __init__(self) -> None:
        self.tools = [self.GithubGetReposByUserTool(), self.GithubGetFilesByRepoTool(), self.GithubGetFileContentByRepoandPathTool(), self.GithubCreateIssueTool()]

    # Method to get tools (for ease of use, made so class works similarly to LangChain toolkits)
    def tools(self) -> List[BaseTool]:
        return self.tools