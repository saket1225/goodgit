from .ssh import *

def main():
    accounts = load_accounts()

    if accounts:
        list_accounts(accounts)

    choice = input("Do you want to add a new account? (y/n): ")

    if choice.lower() == 'y':
        email = input("Enter your email (Same as your GitHub account): ")
        email, token = github_device_auth(email)

        if email and token:
            accounts[email] = token
            save_accounts(accounts)
            print("Account added successfully.")

            # Check if SSH config exists
            config_exists = os.path.exists(os.path.expanduser("~/.ssh/config"))

            if not config_exists:
                make_default = input("Do you want to make this the default GitHub account? (y/n): ")
                if make_default.lower() == 'y':
                    update_ssh_config(email.split('@')[0], make_default=True)
                else:
                    default_email = input("Enter the email for the default GitHub account: ")
                    # Generate SSH for default account and update config
                    # (Assuming you have a function to generate SSH for a given email)
                    generate_ssh_for_default_account(default_email)

            else:
                update_ssh_config(email.split('@')[0])

        else:
            print("Failed to add account.")

    # List all accounts at the end
    print("\nAll available accounts:")
    list_accounts(accounts)

if __name__ == "__main__":
    main()
