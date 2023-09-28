from .ssh import *

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
