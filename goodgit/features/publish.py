import requests
import json
import time
import os
import subprocess
from urllib.parse import parse_qs
from questionary import text, select, confirm

def check_git_remote():
    try:
        result = subprocess.run(['git', 'remote', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout:
            return True, result.stdout.split()[1]  # Extracting the remote URL
        else:
            return False, None
    except Exception as e:
        print(f"An error occurred while checking for git remote: {e}")
        return False, None

def fetch_github_username(access_token):
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['login']
    else:
        print(f"Failed to fetch GitHub username. HTTP Status Code: {response.status_code}. Raw response: {response.text}")
        return None

def load_host_mapping():
    try:
        with open(os.path.expanduser("~/.ssh/goodgit/config.json"), "r") as f:
            data = json.load(f)
            return {account['email']: account['host'] for account in data.get("accounts", [])}
    except FileNotFoundError:
        return {}

def store_access_token(token, email):
    config_path = os.path.expanduser("~/.ssh/goodgit/")
    os.makedirs(config_path, exist_ok=True)
    token_file_path = f"{config_path}access_tokens.json"
    
    tokens = {}
    if os.path.exists(token_file_path):
        with open(token_file_path, "r") as f:
            tokens = json.load(f)
    
    tokens[email] = token
    
    with open(token_file_path, "w") as f:
        json.dump(tokens, f)

def retrieve_access_token(email):
    token_file_path = os.path.expanduser("~/.ssh/goodgit/access_tokens.json")
    if os.path.exists(token_file_path):
        with open(token_file_path, "r") as f:
            tokens = json.load(f)
            return tokens.get(email)
    return None


def save_token(token):
    with open("access_token.txt", "w") as f:
        f.write(token)

def load_token():
    try:
        with open("access_token.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def load_accounts():
    try:
        with open(os.path.expanduser("~/.ssh/goodgit/config.json"), "r") as f:
            data = json.load(f)
            return data.get("accounts", [])
    except FileNotFoundError:
        return []

def create_repo(access_token, repo_name, is_private):
    headers = {'Authorization': f'token {access_token}'}
    data = {'name': repo_name, 'private': is_private}
    response = requests.post('https://api.github.com/user/repos', headers=headers, json=data)
    if response.status_code == 201:
        return repo_name
    else:
        print(f"Failed to create repository. HTTP Status Code: {response.status_code}. Raw response: {response.text}")
        return None

def push_to_repo(repo_name, username, selected_email, host_mapping):
    # Get the specific host for the selected email
    specific_host = host_mapping.get(selected_email, "github.com")
    
    print(f"Pushing to repo: {repo_name}, Username: {username}, Host: {specific_host}")
    
    commands = [
        "git init",
        "git add .",
        "git commit -m 'Initial commit'",
        "git branch -M main",
        f"git remote add origin git@{specific_host}:{username}/{repo_name}.git",
        "git push -u origin main"
    ]

    for cmd in commands:
        subprocess.run(cmd, shell=True)


def main(host_mapping):
    # Load accounts from config
    accounts = load_accounts()

    is_git_initialized, remote_link = check_git_remote()

    if is_git_initialized:
        print(f"A git remote link is already set up: {remote_link}")
        user_choice = input("Would you like to push the code to this remote? (y/n): ").lower()
        if user_choice == 'y':
            print("Pushing...")
            return  # Exit the function as the user chose to push to existing remote

        else:
            return


    if len(accounts) == 0:
        print("No accounts found in ~/.ssh/goodgit/config.json. Exiting.")
        return
    elif len(accounts) == 1:
        selected_email = accounts[0]['email']
        print(f"Using the only available account: {selected_email}")
    else:
        selected_email = select(
            "Select the account you want to use:",
            choices=[account['email'] for account in accounts]
        ).ask()


    # Check if the token already exists
    access_token = retrieve_access_token(selected_email)
    if access_token:
        print(f"Using existing access token: {access_token}")
    else:
        # Code for obtaining a new access token
        client_id = "5f4d455043e52e4de32c"
        device_code_url = "https://github.com/login/device/code"
        payload = {"client_id": client_id, "scope": "repo"}
        response = requests.post(device_code_url, data=payload)
        if response.status_code == 200:
            data = parse_qs(response.text)
            device_code = data['device_code'][0]
            user_code = data['user_code'][0]
            verification_uri = data['verification_uri'][0]
            expires_in = int(data['expires_in'][0])
            interval = int(data['interval'][0])
            
            print(f"Please go to {verification_uri} and enter this code: {user_code}")
            
            # Initialize a timeout counter
            timeout_counter = 0
            
            token_url = "https://github.com/login/oauth/access_token"
            while timeout_counter < expires_in:
                payload = {
                    "client_id": client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
                response = requests.post(token_url, data=payload)
                if response.status_code == 200:
                    data = parse_qs(response.text)
                    if 'access_token' in data:
                        access_token = data['access_token'][0]
                        store_access_token(access_token, selected_email)
                        print(f"Your access token is: {access_token}")
                        break
                time.sleep(interval)
                timeout_counter += interval
            else:
                print("Failed to get access token within the allowed time. Exiting.")
                return



    # Fetch GitHub username
    username = fetch_github_username(access_token)
    if not username:
        print("Failed to fetch GitHub username. Exiting.")
        return

    while True:
        # Ask the user for the new repository name
        repo_name = text("Enter the name for your new GitHub repository:").ask()
        is_private = select(
            "Should the repository be private or public?",
            choices=["Private", "Public"]
        ).ask() == "Private"


        # Create the new repository
        created_repo_name = create_repo(access_token, repo_name, is_private)

        if created_repo_name:
            print(f"Successfully created repository: {created_repo_name}")
            time.sleep(2)
            push_to_repo(created_repo_name, username, selected_email, host_mapping)
            break  # Exit the loop as the repo was successfully created
        else:
            print("Name already exists. Let's try again with a different name.")


if __name__ == "__main__":
    host_mapping = load_host_mapping()
    main(host_mapping)