import subprocess

def undo_last_commit():
    try:
        subprocess.run(["git", "reset", "--soft", "HEAD~1"], check=True)
        print("Successfully undone the last commit.")
    except subprocess.CalledProcessError:
        print("Failed to undo the last commit. Make sure you're in a Git repository.")

# To use the function
undo_last_commit()
