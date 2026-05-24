import time
import hashlib
import getpass

from repository import *
from objects import create_tree


def init():
    repo = os.getcwd()
    vcs = os.path.join(repo, ".vcs")

    os.makedirs(vcs, exist_ok=True)
    os.makedirs(os.path.join(vcs, "objects"), exist_ok=True)
    os.makedirs(os.path.join(vcs, "log"), exist_ok=True)

    with open(os.path.join(vcs, "index"), "w") as f:
        pass

    with open(os.path.join(vcs, "head"), "w") as f:
        pass

    return "Repo initialized"


def add(file_path):
    if not check_repo():
        return "ADD ERROR: not init repo"

    repo = find_repo()
    abs_path = os.path.abspath(file_path)
    rel_file_path = os.path.relpath(abs_path, repo)

    if not os.path.exists(abs_path):
        return "ADD ERROR: file not found"

    mode = "100" + oct(os.stat(abs_path).st_mode & 0o777)[2:]

    existing = set()
    idx = os.path.join(repo, ".vcs", "index")

    if os.path.exists(idx):
        with open(idx, "r") as f:
            for line in f:
                existing.add(line.split()[1])

    if rel_file_path not in existing:
        with open(idx, "a") as f:
            safe_path = escape_path(rel_file_path)
            f.write(f"{mode}\t{safe_path}\n")

    return f"Added: {rel_file_path}"


def commit(message=""):
    if not check_repo():
        return "COMMIT ERROR: not init repo"

    tree_hash = create_tree()

    if not tree_hash:
        return "ERROR: empty tree"

    parent = ""

    if os.path.exists(head_path()):
        with open(head_path(), "r") as f:
            parent = f.read().strip()

    author = getpass.getuser()
    timestamp = int(time.time())

    content = f"""commit
tree {tree_hash}
parent {parent}
author {author} {timestamp}

{message}"""

    commit_hash = hashlib.sha1(content.encode()).hexdigest()

    os.makedirs(log_path(), exist_ok=True)

    with open(os.path.join(log_path(), commit_hash), "w") as f:
        f.write(content)

    with open(head_path(), "w") as f:
        f.write(commit_hash)

    return commit_hash