import subprocess
import questionary

def git_grep_interactive():
    try:
        # Validate if we're in a git repository
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True)
    except subprocess.CalledProcessError:
        print("You're not in a Git repository. Please navigate to one and try again. Or run git init :)")
        return

    # Ask for the search term
    search_term = questionary.text("What is the search term?").ask()

    # Ask where to search
    where = questionary.checkbox("Where do you want to search?", choices=[
        "Specific file types",
        "Previous commits",
        "Branches",
        "Current code"
    ]).ask()

    file_type, commit_hash, branch = None, None, None

    if "Specific file types" in where:
        file_type = questionary.text("Which file types (e.g., py, js, txt)?").ask()
    
    if "Previous commits" in where:
        # Fetch commit messages and hashes
        commit_list = subprocess.getoutput("git log --pretty=format:'%h %s'").split("\n")
        commit_hash = questionary.select("Choose a commit:", choices=commit_list).ask().split()[0]
    
    if "Branches" in where:
        # Fetch branch names
        branch_list = subprocess.getoutput("git branch --format '%(refname:short)'").split("\n")
        branch = questionary.select("Choose a branch:", choices=branch_list).ask()

    # Ask for search options
    options = questionary.checkbox("Select search options:", choices=[
        "Case insensitive",
        "Line number",
        "Count",
        "Context lines",
        "AND terms",
        "OR terms",
        "Show filenames only"
    ]).ask()

    case_insensitive = "Case insensitive" in options
    line_number = "Line number" in options
    count = "Count" in options
    context_lines = 2 if "Context lines" in options else None
    and_terms = questionary.text("AND terms (separate by comma):").ask() if "AND terms" in options else None
    or_terms = questionary.text("OR terms (separate by comma):").ask() if "OR terms" in options else None
    show_filenames = "Show filenames only" in options

    # Call the original git_grep function
    try:
        print("Performing your search... Hang tight!")
        # Call the original git_grep function
        result = git_grep(
            search_term, 
            case_insensitive=case_insensitive, 
            line_number=line_number, 
            count=count, 
            file_type=file_type, 
            commit_hash=commit_hash, 
            branch=branch, 
            context_lines=context_lines, 
            and_terms=and_terms, 
            or_terms=or_terms, 
            show_filenames=show_filenames
        )
        
        if result:
            print("Search completed. Here are the results:")
            print(result)
        else:
            print("No results found for your query.")

    except subprocess.CalledProcessError as e:
        print(f"Oops! An error occurred: {e.stderr}")
        
    except Exception as e:
        print(f"Something unexpected happened: {e}")

    print(result)


def git_grep(search_term, case_insensitive=False, line_number=False,
             count=False, file_type=None, commit_hash=None, branch=None,
             context_lines=None, and_terms=None, or_terms=None, show_filenames=False):
    # Base command
    cmd = ["git", "grep"]
    
    # Add options based on parameters
    if case_insensitive:
        cmd.append("-i")
    if line_number:
        cmd.append("-n")
    if count:
        cmd.append("-c")
    if context_lines:
        cmd.append(f"-C {context_lines}")
    if show_filenames:
        cmd.append("-l")
    
    # Add commit hash or branch if specified
    if commit_hash:
        cmd.extend([commit_hash, "--"])
    elif branch:
        cmd.extend([branch, "--"])
    
    # Add logical operations
    if and_terms:
        cmd.extend(["-e", search_term, "--and", "-e", and_terms])
    elif or_terms:
        cmd.extend(["-e", search_term, "--or", "-e", or_terms])
    else:
        cmd.append(search_term)
    
    # Add file type if specified
    if file_type:
        cmd.append(f"*.{file_type}")
    
    # Execute the command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr

# Example usage
if __name__ == "__main__":
    git_grep_interactive()
