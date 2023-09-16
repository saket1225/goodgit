import requests
import time
import webbrowser
import subprocess
import os
import platform
from urllib.parse import parse_qs

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

def generate_ssh_key(email):
    try:
        home = os.path.expanduser("~")
        subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-C", email, "-f", f"{home}/.ssh/id_rsa", "-N", ""])
        with open(f"{home}/.ssh/id_rsa.pub", "r") as f:
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

def github_device_auth(email):
    client_id = "5f4d455043e52e4de32c"
    device_code_url = "https://github.com/login/device/code"
    payload = {"client_id": client_id, "scope": "write:public_key read:public_key"}
    r = requests.post(device_code_url, data=payload)

    if r.status_code == 200:
        r_json = parse_qs(r.text)
        device_code = r_json['device_code'][0]
        user_code = r_json['user_code'][0]  # This was missing
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
                user_name = get_github_username(r_json['access_token'])
                if user_name:
                    subprocess.run(["git", "config", "--global", "user.name", user_name])
                    subprocess.run(["git", "config", "--global", "user.email", email])

                os_name = get_detailed_os_name()
                computer_name = platform.node()
                title = f"GoodGit-{os_name}-{computer_name}-{user_name}"
                ssh_key = generate_ssh_key(email)
                if ssh_key:
                    add_ssh_key(r_json['access_token'], title, ssh_key)
                return r_json['access_token']
            elif 'error' in r_json and r_json['error'] == "authorization_pending":
                time.sleep(interval)
            else:
                print("An error occurred.")
                return None
