import os
from typing import List, Optional
from pydantic import BaseModel, Field

from github import Github
from github import Auth
from dotenv import load_dotenv
load_dotenv(override=True)

pat=os.getenv('GITHUB_PAT')

if not pat:
    raise ValueError("Github Personal Access Token (PAT) is not set in environment variables.")

class GitHubOperations():
    def get_repo_list_by_username(self, user_name: str) -> str:
        try:
            g = Github(pat, per_page=100)
            user=g.get_user(user_name)

            repo_list = []
            for repo in user.get_repos():
                repo_list.append(repo.full_name)
            
            g.close()
            return repo_list
        except Exception as e:
            print(f"An error occurred with GitHubOperations.get_repo_list_by_username: {e}")
            return []
        finally:
            g.close()
    
    def get_file_content(self, repo: str) -> str:
        try:
            g = Github(pat, per_page=100)
            files= g.get_repo(repo).get_contents()

            file_list = []
            for file in files():
                file_list.append(file.name)
            
            g.close()
            return file_list
        except Exception as e:
            print(f"An error occurred with GitHubOperations.get_file_list_by_repo: {e}")
            return []
        finally:
            g.close()
            
    def get_file_list_by_repo(self, repo: str) -> str:
        try:
            g = Github(pat, per_page=100)
            repo = g.get_repo(repo)
            if not repo:
                raise ValueError(f"Repository '{repo}' not found.")
            
            # get files in the repository
            items = repo.get_contents("")

            file_list = []
            directories = []
            directories.append("/")  # start with the root directory

            # get all directories
            for item in items:
                if item.type == "dir":
                    directories.append(item.path)
            # get all files
            for directory in directories:
                files = repo.get_contents(directory)
                for file in files:
                    if file.type == "file":
                        file_list.append(file.path)

            # also add files in the root directory
            g.close()
            return file_list
        except Exception as e:
            print(f"An error occurred with GitHubOperations.get_file_list_by_repo: {e}")
            return []
        finally:
            g.close()

    def get_file_content_by_repo_and_path(self, repo: str, file_path: str) -> str:
        try:
            g = Github(pat, per_page=100)
            repo = g.get_repo(repo)
            if not repo:
                raise ValueError(f"Repository '{repo}' not found.")
            
            # get file content by path
            file_content = repo.get_contents(file_path)
            if file_content:
                return file_content.content
            else:
                raise ValueError(f"File '{file_path}' not found in repository '{repo}'.")
        except Exception as e:
            print(f"An error occurred with GitHubOperations.get_file_content_by_repo_and_path: {e}")
            return ""
        finally:
            g.close()

    def search_code(self, query: str) -> List[str]:
        try:
            g = Github(pat, per_page=100)
            results = g.search_code(query=query)
            code_snippets = [result.code for result in results]
            return code_snippets
        except Exception as e:
            print(f"An error occurred with GitHubOperations.search_code: {e}")
            return []
        finally:
            g.close()

    def create_issue(self, repo: str, title: str, body: str) -> str:
        try:
            g = Github(pat, per_page=100)
            repository = g.get_repo(repo)
            if not repository:
                raise ValueError(f"Repository '{repo}' not found.")
            
            issue = repository.create_issue(title=title, body=body)
            return f"Issue created successfully: {issue.html_url}"
        except Exception as e:
            print(f"An error occurred with GitHubOperations.create_issue: {e}")
            return ""
        finally:
            g.close()
    