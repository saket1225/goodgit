
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

def load_accounts_from_config():
    config_path = os.path.expanduser("~/.ssh/config")
    accounts = {}
    try:
        with open(config_path, 'r') as f:
            lines = f.readlines()
        host = None
        for line in lines:
            if "Host " in line:
                host = line.split("Host ")[1].strip()
            if "User git" in line and host:
                username = host.split("github-")[-1]
                accounts[username] = host
    except FileNotFoundError:
        return {}
    return accounts


def is_default_account_set():
    config_path = os.path.expanduser("~/.ssh/config")
    try:
        with open(config_path, "r") as f:
            lines = f.readlines()
        for line in lines:
            if "Host github.com" in line.strip():
                return True
    except FileNotFoundError:
        return False
    return False


def save_accounts(accounts, default_username=None):
    home = os.path.expanduser("~")
    folder_path = os.path.join(home, ".goodgit")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filepath = os.path.join(folder_path, "accounts.json")
    data = {'accounts': accounts}
    if default_username:
        data['default_username'] = default_username
    with open(filepath, 'w') as f:
        json.dump(data, f)

# New function to update JSON config
def update_json_config(email, host, action="add"):
    config_path = os.path.expanduser("~/.ssh/goodgit/config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                data = json.load(f)
        else:
            data = {"accounts": []}

        account_info = {"email": f"{email}(github.com)", "host": host}

        if action == "add":
            data["accounts"].append(account_info)
        elif action == "remove":
            data["accounts"] = [account for account in data["accounts"] if account != account_info]

        with open(config_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"An error occurred while updating the JSON config: {e}")

# Updated function to list accounts
def list_accounts(accounts):
    config_path = os.path.expanduser("~/.ssh/goodgit/config.json")
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        accounts = data.get('accounts', [])
        print("Available accounts:")
        for idx, account in enumerate(accounts):
            print(f"{idx+1}. {account['email']}")
    except FileNotFoundError:
        print("No accounts found.")


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
        username = email.split('@')[0]  # Extract username from email
        goodgit_folder = os.path.join(home, ".ssh", "goodgit", f'.ssh_{username}')  # Use only username for folder
        
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

def update_ssh_config(username, make_default=False):
    config_path = os.path.expanduser("~/.ssh/config")
    config_entry_general = f"""Host github-{username}
    HostName github.com
    User git
    IdentityFile ~/.ssh/goodgit/.ssh_{username}/id_rsa
    """
    config_entry_default = f"""Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/goodgit/.ssh_{username}/id_rsa
    """
    try:
        with open(config_path, "a") as f:
            if make_default:
                f.write("\n" + config_entry_default)  # Add as default
            f.write("\n" + config_entry_general)  # Add as general
        print("SSH config updated successfully.")
    except Exception as e:
        print(f"Failed to update SSH config: {e}")



def github_device_auth(email=None):
    accounts = load_accounts_from_config()
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

    if ssh_key:
        add_ssh_key(r_json['access_token'], title, ssh_key)
        
        # Check if SSH config exists
        config_exists = os.path.exists(os.path.expanduser("~/.ssh/config"))
        
        if not config_exists:
            make_default = input("Do you want to make this the default GitHub account? (y/n): ")
            if make_default.lower() == 'y':
                update_ssh_config(username, make_default=True)
            else:
                default_email = input("Enter the email for the default GitHub account: ")
                # Generate SSH for default account and update config
                # (Assuming you have a function to generate SSH for a given email)
                generate_ssh_for_default_account(default_email)
        
        else:
            update_ssh_config(username)


def main():
    accounts = load_accounts_from_config()

    if accounts:
        list_accounts(accounts)

    choice = input("Do you want to add a new account? (y/n): ")

    if choice.lower() == 'y':
        email = input("Enter your email (Same as your GitHub account): ")
        email, token = github_device_auth(email)
        
        if email and token:
            username = email.split('@')[0]
            host = accounts.get(username, f"github-{username}")  # Fetch the host for this username
            update_json_config(email, host, action="add")  # Update JSON config with the host

            config_exists = os.path.exists(os.path.expanduser("~/.ssh/config"))

            if not config_exists or os.path.getsize(os.path.expanduser("~/.ssh/config")) == 0:
                make_default = input("This is your first SSH key. Do you want to make this the default GitHub account? (y/n): ")
                if make_default.lower() == 'y':
                    update_ssh_config(username, make_default=True)
                else:
                    default_email = input("Enter the email for the default GitHub account: ")
                    generate_ssh_for_default_account(default_email)
                    update_ssh_config(default_email.split('@')[0])
            else:
                if not is_default_account_set():
                    make_default = input("Do you want to make this the default GitHub account? (y/n): ")
                    if make_default.lower() == 'y':
                        update_ssh_config(username, make_default=True)
                    else:
                        default_email = input("Enter the email for the default GitHub account: ")
                        generate_ssh_for_default_account(default_email)
                        update_ssh_config(default_email.split('@')[0])
                else:
                    update_ssh_config(username)  # <-- This line was missing, it adds the new account to SSH config

    print("\nAll available accounts:")
    list_accounts(load_accounts_from_config())  # Reload accounts to include the newly added one

if __name__ == "__main__":
    main()
