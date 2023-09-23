from .ssh import *

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
    else:
        print("Failed to add account.")

# List all accounts at the end
print("\nAll available accounts:")
list_accounts(accounts)
