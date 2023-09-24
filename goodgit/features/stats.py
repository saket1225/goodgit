import subprocess
from rich import print as rprint
from rich.table import Table

def run_command(command):
    return subprocess.getoutput(command)

def get_gitignored_files():
    return set(run_command("git ls-files --ignored --exclude-standard").split("\n"))

def gg_stats():
    try:
        gitignored_files = get_gitignored_files()  # Fetch the gitignored files

        # Create a table
        table = Table(title="GoodGit Repository Stats")
        table.add_column("Metric", justify="right", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")

        # Language Stats (Basic)
        all_files = run_command("git ls-files").split("\n")
        language_stats = {}
        total_lines = 0
        for file in all_files:
            if file in gitignored_files:
                continue
            extension = file.split('.')[-1]
            language_stats[extension] = language_stats.get(extension, 0) + 1
            try:
                lines_in_file = int(run_command(f"wc -l < {file}").strip())
                total_lines += lines_in_file
            except ValueError:
                # Skip files that can't be read by wc -l
                continue

        table.add_row("Total Lines of Code", str(total_lines))
        table.add_row("Language Stats", str(language_stats))

        # Number of Collaborators and Contributions
        collaborators = run_command("git shortlog -s -n")
        table.add_row("Collaborators and Contributions", collaborators)

        # Branches and List
        branches = run_command("git branch")
        branch_count = len(branches.strip().split("\n"))
        table.add_row("Branches", f"{branch_count}\n{branches}")

        # Commit Count
        commit_count = run_command("git rev-list --all --count")
        table.add_row("Total Commits", commit_count)

        # File Count
        file_count = len(all_files) - len(gitignored_files)
        table.add_row("Total Files", str(file_count))

        # Last Commit Details
        last_commit = run_command("git log -1")
        table.add_row("Last Commit Details", last_commit)

        # Print the table
        rprint(table)

    except Exception as e:
        rprint(f"[red]An error occurred:[/red] {e}")

if __name__ == "__main__":
    gg_stats()
