import subprocess

def list_branch(skip_default=False):
    branches = subprocess.getoutput("git branch --list").split("\n")
    for branch in branches:
        print(branch)

def switch_branch(branch_name=""):
    current_branch = subprocess.getoutput("git symbolic-ref --short HEAD")
    uncommitted_changes = subprocess.getoutput("git status --porcelain")
    
    if uncommitted_changes:
        print(f"Creating a temporary commit in {current_branch}...")
        subprocess.run(["git", "add", "-A"])
        subprocess.run(["git", "commit", "-m", "TEMP_COMMIT"])
    
    list_branch()
    
    if not branch_name:
        branch_name = input("Enter the branch name to switch to: ")
    
    if branch_name not in subprocess.getoutput("git branch --list"):
        create_new = input(f"Branch {branch_name} doesn't exist. Do you want to create it? (y/n): ")
        if create_new.lower() == 'y':
            new_branch(branch_name)
            return
    
    subprocess.run(["git", "checkout", branch_name])
    
    # Check if the last commit is a temporary commit and undo it
    last_commit_message = subprocess.getoutput("git log -1 --pretty=%B")
    if last_commit_message.strip() == "TEMP_COMMIT":
        print(f"Undoing temporary commit in {branch_name}...")
        subprocess.run(["git", "reset", "HEAD~"])

def new_branch(branch_name=""):
    current_branch = subprocess.getoutput("git symbolic-ref --short HEAD")
    uncommitted_changes = subprocess.getoutput("git status --porcelain")
    
    if uncommitted_changes:
        print(f"Creating a temporary commit in {current_branch}...")
        subprocess.run(["git", "add", "-A"])
        subprocess.run(["git", "commit", "-m", "TEMP_COMMIT"])
    
    if not branch_name:
        branch_name = input("Enter the new branch name: ")
    
    if branch_name in subprocess.getoutput("git branch --list"):
        switch = input(f"Branch {branch_name} already exists. Do you want to switch to it? (y/n): ")
        if switch.lower() == 'y':
            switch_branch(branch_name)
            return
    
    subprocess.run(["git", "checkout", "-b", branch_name])
    
    # Check if the last commit is a temporary commit and undo it
    last_commit_message = subprocess.getoutput("git log -1 --pretty=%B")
    if last_commit_message.strip() == "TEMP_COMMIT":
        print(f"Undoing temporary commit in {branch_name}...")
        subprocess.run(["git", "reset", "HEAD~"])
