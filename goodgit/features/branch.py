import subprocess
from datetime import datetime

def run_command(command):
    return subprocess.getoutput(command)

def get_current_branch():
    return run_command("git symbolic-ref --short HEAD").strip()

def has_changes():
    status = run_command("git status --porcelain")
    return bool(status.strip())

def list_branches(skip_default=False):
    branches = run_command("git branch").split("\n")
    print("Available branches:")
    for branch in branches:
        branch = branch.strip()
        if skip_default and branch == 'main':
            continue
        print(branch)

def switch_branch(branch_name=None):
    current_branch = get_current_branch()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stash_message = f"Switching to branch {branch_name} from {current_branch} at {timestamp} stash"
    stash_ref = None

    if has_changes():
        print(f"Stashing changes: {stash_message}")
        stash_output = run_command(f"git stash save --include-untracked '{stash_message}'")
        stash_ref = stash_output.split(":")[0]  # Extracting the stash reference

    if not branch_name:
        list_branches()
        branch_name = input("Which branch do you want to switch to? ").strip()

    if branch_name not in run_command("git branch"):
        confirm = input(f"The branch {branch_name} does not exist. Do you want to create it? (y/n): ")
        if confirm.lower() == 'y':
            new_branch(branch_name)
    else:
        run_command(f"git checkout {branch_name}")
        print(f"Switched to branch {branch_name}")
        if stash_ref:
            run_command(f"git stash apply {stash_ref}")
        
        

def new_branch(branch_name=None):
    current_branch = get_current_branch()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stash_message = f"Creating new branch {branch_name} from {current_branch} at {timestamp} stash"

    if has_changes():
        print(f"Stashing changes: {stash_message}")
        run_command(f"git stash save --include-untracked '{stash_message}'")

    if not branch_name:
        list_branches()
        branch_name = input("Enter the name of the new branch: ").strip()

    if branch_name in run_command("git branch"):
        confirm = input(f"The branch {branch_name} already exists. Do you want to switch to it? (y/n): ")
        if confirm.lower() == 'y':
            switch_branch(branch_name)
    else:
        run_command(f"git checkout -b {branch_name}")
        print(f"Created and switched to new branch {branch_name}")
        run_command("git stash apply")

def delete_branch(branch_name=None):
    current_branch = get_current_branch()

    if not branch_name:
        list_branches(skip_default=True)
        branch_name = input("Which branch do you want to delete? ").strip()

    confirm = input(f"Are you sure you want to delete the branch {branch_name}? (y/n): ")
    if confirm.lower() == 'y':
        if branch_name == current_branch:
            print("Switching to branch 'main'")
            switch_branch("main")
        run_command(f"git branch -d {branch_name}")
        print(f"Deleted branch {branch_name}")

# Example usage
switch_branch()
# new_branch()
# delete_branch()
# list_branches()
