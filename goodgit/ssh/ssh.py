import requests
import time
import webbrowser
import subprocess
import os
import platform
from urllib.parse import parse_qs
import configparser
import json
import git

def load_accounts():
    home = os.path.expanduser("~")
    filepath = os.path.join(home, ".goodgit", "accounts.json")
    ssh_folder_path = os.path.join(home, ".goodgit", "ssh")
    
    try:
        with open(filepath, 'r') as f:
            accounts = json.load(f)
    except FileNotFoundError:
        return {}
    
    # Check if SSH folders exist for each account
    for email, data in list(accounts.items()):  # Use list() to make a copy since we might modify the dict
        folder_name = f".ssh_{email.replace('@', '_').replace('.', '_')}"
        full_folder_path = os.path.join(ssh_folder_path, folder_name)
        
        if not os.path.exists(full_folder_path):
            print(f"SSH folder for {email} is missing. Removing from accounts.")
            del accounts[email]
    
    # Save the updated accounts back to the JSON file
    with open(filepath, 'w') as f:
        json.dump(accounts, f)
    
    return accounts


def save_accounts(accounts):
    home = os.path.expanduser("~")
    folder_path = os.path.join(home, ".goodgit")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filepath = os.path.join(folder_path, "accounts.json")
    with open(filepath, 'w') as f:
        json.dump(accounts, f)

# New function to list accounts
def list_accounts(accounts):
    print("Available accounts:")
    for idx, email in enumerate(accounts.keys()):
        print(f"{idx+1}. {email}")

def get_detailed_os_name():
    system_name = platform.system()
    if system_name == "Linux":
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro = line[3:].strip().replace('"', '')
                        return f"{distro}_os"
        except FileNotFoundError:
            return "linux_os"
    elif system_name == "Darwin":
        return "mac_os"
    elif system_name == "Windows":
        return f"windows{platform.release()}_os"
    else:
        return "unknown_os"

def generate_ssh_key(email, folder):
    try:
        home = os.path.expanduser("~")
        goodgit_folder = os.path.join(home, ".goodgit", "ssh", folder)
        
        # Create the folder if it doesn't exist
        if not os.path.exists(goodgit_folder):
            os.makedirs(goodgit_folder)
        
        key_path = os.path.join(goodgit_folder, "id_rsa")
        subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-C", email, "-f", key_path, "-N", ""])
        
        with open(f"{key_path}.pub", "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"An error occurred while generating the SSH key: {e}")
        return None

def add_ssh_key(token, title, key):
    url = "https://api.github.com/user/keys"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    payload = {"title": title, "key": key}
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code == 201:
        print("SSH key added successfully.")

def get_github_username(token):
    url = "https://api.github.com/user"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get("name", "Unknown")
    else:
        print("Failed to fetch GitHub username.")
        return None

def read_git_config():
    try:
        repo = git.Repo(search_parent_directories=True)
        config = repo.config_reader()  # get a config reader for read-only access
        email = config.get_value("user", "email", None)
        name = config.get_value("user", "name", None)
        return email, name
    except (git.InvalidGitRepositoryError, git.GitCommandError, KeyError):
        return None, None


def github_device_auth(email=None):
    accounts = load_accounts()
    if accounts:
        print("You have the following accounts already set up:")
        list_accounts(accounts)

    client_id = "5f4d455043e52e4de32c"
    device_code_url = "https://github.com/login/device/code"
    payload = {"client_id": client_id, "scope": "write:public_key read:public_key"}
    r = requests.post(device_code_url, data=payload)

    if r.status_code == 200:
        r_json = parse_qs(r.text)
        device_code = r_json['device_code'][0]
        user_code = r_json['user_code'][0]
        verification_uri = r_json['verification_uri'][0]
        expires_in = int(r_json['expires_in'][0])
        interval = int(r_json['interval'][0])

        print(f"Please go to {verification_uri} and enter this user code: {user_code}")
        webbrowser.open(verification_uri)

        token_url = "https://github.com/login/oauth/access_token"
        payload = {"client_id": client_id, "device_code": device_code, "grant_type": "urn:ietf:params:oauth:grant-type:device_code"}
        headers = {"Accept": "application/json"}

        end_time = time.time() + expires_in
        while time.time() < end_time:
            r = requests.post(token_url, data=payload, headers=headers)
            r_json = r.json()
            if 'access_token' in r_json:
                print("Authorization successful!")
                
                config_email, config_name = read_git_config()
                if config_name:
                    user_name = config_name
                else:
                    user_name = get_github_username(r_json['access_token'])
                    if user_name:
                        subprocess.run(["git", "config", "--global", "user.name", user_name])
                        subprocess.run(["git", "config", "--global", "user.email", email])

                print(f"Debug: Using email {email} for SSH key generation")  # Debug statement

                os_name = get_detailed_os_name()
                computer_name = platform.node()
                title = f"GoodGit-{os_name}-{computer_name}-{user_name}"
                
                folder = f".ssh_{email.replace('@', '_').replace('.', '_')}"
                print(f"Debug: SSH key will be saved in folder {folder}")  # Debug statement

                ssh_key = generate_ssh_key(email, folder)
                
                if ssh_key:
                    add_ssh_key(r_json['access_token'], title, ssh_key)
                
                return email, r_json['access_token']

            elif 'error' in r_json and r_json['error'] == "authorization_pending":
                time.sleep(interval)
            else:
                print("An error occurred.")
                return None, None  # Return None values if an error occurs