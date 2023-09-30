# commit_script.py
import subprocess
import requests
import json
import questionary
from rich import print, highlighter
from goodgit.utils import is_git_repo  # Importing the common function

def get_git_diff():
    result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True)
    return result.stdout

def main():
    if not is_git_repo():
        print("[red]Not a git repository. Exiting.[/red]")
        return

    add_choice = questionary.select(
        "Do you want to add all files or specific files?",
        choices=["All files", "Specific files"]
    ).ask()

    if add_choice == "All files":
        subprocess.run(["git", "add", "."])
    else:
        files_to_add = questionary.path("Enter the files to add:").ask()
        subprocess.run(["git", "add", files_to_add])

    git_diff = get_git_diff()

    payload = json.dumps({
        "git_diff": git_diff,
    })

    headersList = {
        "Accept": "*/*",
        "User-Agent": "GoodGit",
        "Content-Type": "application/json",
    }

    reqUrl = "https://orca-app-qmx5i.ondigitalocean.app/api/commit/"
    response = requests.request("POST", reqUrl, data=payload,  headers=headersList)

    if response.status_code == 200:
        commit_json = response.json()
        print("[green]Suggested Commit Message:[/green]")
        print(f"[yellow]{commit_json['subject']}[/yellow]")
        print(f"[yellow]{commit_json['description']}[/yellow]")

        commit_choice = questionary.confirm("Do you want to commit with this message?").ask()
        if commit_choice:
            subprocess.run(["git", "commit", "-m", commit_json['subject'], "-m", commit_json['description']])
            print("[green]Commit successful![/green]")
    else:
        print("[red]API call failed. Exiting.[/red]")
