import os

from github import Github
from github import Auth
from dotenv import load_dotenv
load_dotenv(override=True)

pat=os.getenv('Github_PAT')
def main():
    username="drewelewis"
    repo= "drewelewis/ContosoBankAPI"

#    get_repo_list_by_username(username)
    create_issue(repo, "Test Issue", "This is a test issue created by the script.")

def get_repo_list_by_username(user_name: str) -> str:
    try:
        g = Github(pat, per_page=100)
        user=g.get_user(user_name)

        repo_list = []
        for repo in user.get_repos():
            repo_list.append(repo.name)
        
        g.close()
        return repo_list
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        g.close()

def create_issue(repo_name: str, title: str, body: str) -> None:
    try:
        g = Github(pat, per_page=100)
        repo = g.get_repo(repo_name)
        repo.create_issue(title=title, body=body)
        print(f"Issue '{title}' created in repository '{repo_name}'.")
    except Exception as e:
        print(f"An error occurred while creating the issue: {e}")
    finally:
        g.close()
if __name__ == "__main__":
    main()
