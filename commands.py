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


def tag(name, message="", list_tags=False):
    if not check_repo():
        return "TAG ERROR: not init repo"

    os.makedirs(tags_path(), exist_ok=True)

    if list_tags:
        tags = os.listdir(tags_path())

        if not tags:
            return "no tags yet"

        for t in sorted(tags):
            with open(os.path.join(tags_path(), t), "r") as f:
                commit_hash = f.readline().strip()
                tag_message = f.readline().strip()

            if tag_message:
                print(f"{t}  ->  {commit_hash[:8]}  \"{tag_message}\"")
            else:
                print(f"{t}  ->  {commit_hash[:8]}")

        return ""

    if not name:
        return "TAG ERROR: no tag name"

    with open(head_path(), "r") as f:
        current_hash = f.read().strip()

    if not current_hash:
        return "TAG ERROR: no commits yet"

    with open(os.path.join(tags_path(), name), "w") as f:
        f.write(current_hash + "\n")
        f.write(message)

    return f"Tag '{name}' -> {current_hash[:8]}"


def get_tags_by_commit():
    result = {}

    if not os.path.exists(tags_path()):
        return result

    for t in os.listdir(tags_path()):
        with open(os.path.join(tags_path(), t), "r") as f:
            commit_hash = f.readline().strip()
            tag_message = f.readline().strip()
        result[commit_hash] = (t, tag_message)

    return result


def log():
    if not check_repo():
        return "LOG ERROR: not init repo"

    if not os.path.exists(head_path()):
        return "LOG ERROR: no commits yet"

    with open(head_path(), "r") as f:
        current_hash = f.read().strip()

    if not current_hash:
        return "LOG ERROR: no commits yet"

    tags = get_tags_by_commit()

    with open(head_path(), "r") as f:
        head_hash = f.read().strip()

    while current_hash:
        commit_file = os.path.join(log_path(), current_hash)

        if not os.path.exists(commit_file):
            break

        with open(commit_file, "r") as f:
            content = f.read()

        lines = content.splitlines()

        tree_hash = ""
        parent_hash = ""
        author_line = ""
        message_lines = []
        after_blank = False

        for line in lines:
            if line.startswith("tree "):
                tree_hash = line[5:]
            elif line.startswith("parent "):
                parent_hash = line[7:]
            elif line.startswith("author "):
                author_line = line[7:]
            elif line == "" and not after_blank:
                after_blank = True
            elif after_blank:
                message_lines.append(line)

        parts = author_line.rsplit(" ", 1)
        author = parts[0] if len(parts) == 2 else author_line
        timestamp = int(parts[1]) if len(parts) == 2 else 0
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        message = " ".join(message_lines).strip()

        head_label = "  (HEAD)" if current_hash == head_hash else ""

        if current_hash in tags:
            tag_name, tag_message = tags[current_hash]
            tag_label = f"  [{tag_name}]"
            if tag_message:
                tag_label += f"  \"{tag_message}\""
        else:
            tag_label = ""

        print(f"commit {current_hash}{head_label}{tag_label}")
        print(f"author: {author}")
        print(f"date:   {date_str}")
        if message:
            print(f"message: {message}")

        tree_file = os.path.join(objects_path(), tree_hash)
        if os.path.exists(tree_file):
            print("files:")
            with open(tree_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(" ", 3)
                    if len(parts) == 4:
                        print(f"  {parts[3]}")

        print()

        current_hash = parent_hash

    return ""


def restore_files(tree_hash, base_path=""):
    repo = find_repo()
    tree_file = os.path.join(objects_path(), tree_hash)

    if not os.path.exists(tree_file):
        return

    with open(tree_file, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split(" ", 3)
        if len(parts) != 4:
            continue

        mode, obj_type, obj_hash, name = parts

        if base_path:
            rel_path = base_path + "/" + name
        else:
            rel_path = name

        abs_path = os.path.join(repo, rel_path)

        if obj_type == "blob":
            blob_file = os.path.join(objects_path(), obj_hash)
            if os.path.exists(blob_file):
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(blob_file, "rb") as src:
                    content = src.read()
                with open(abs_path, "wb") as dst:
                    dst.write(content)
                os.chmod(abs_path, int(mode, 8))

        elif obj_type == "tree":
            restore_files(obj_hash, rel_path)


def collect_files_from_tree(tree_hash, base_path, result):
    tree_file = os.path.join(objects_path(), tree_hash)

    if not os.path.exists(tree_file):
        return

    with open(tree_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(" ", 3)
            if len(parts) != 4:
                continue

            mode, obj_type, obj_hash, name = parts

            if base_path:
                rel_path = base_path + "/" + name
            else:
                rel_path = name

            if obj_type == "blob":
                result.add(rel_path)
            elif obj_type == "tree":
                collect_files_from_tree(obj_hash, rel_path, result)


def collect_index_entries(tree_hash, base_path, result):
    tree_file = os.path.join(objects_path(), tree_hash)

    if not os.path.exists(tree_file):
        return

    with open(tree_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(" ", 3)
            if len(parts) != 4:
                continue

            mode, obj_type, obj_hash, name = parts

            if base_path:
                rel_path = base_path + "/" + name
            else:
                rel_path = name

            if obj_type == "blob":
                result.append((mode, rel_path))
            elif obj_type == "tree":
                collect_index_entries(obj_hash, rel_path, result)


def reset(commit_hash):
    if not check_repo():
        return "RESET ERROR: not init repo"

    if not commit_hash:
        return "RESET ERROR: no commit hash"

    commit_file = os.path.join(log_path(), commit_hash)

    if not os.path.exists(commit_file):
        return f"RESET ERROR: commit {commit_hash} not found"

    with open(commit_file, "r") as f:
        content = f.read()

    tree_hash = ""
    for line in content.splitlines():
        if line.startswith("tree "):
            tree_hash = line[5:]
            break

    if not tree_hash:
        return "RESET ERROR: tree not found in commit"

    current_files = set()
    with open(head_path(), "r") as f:
        current_head = f.read().strip()

    if current_head:
        current_commit_file = os.path.join(log_path(), current_head)
        if os.path.exists(current_commit_file):
            with open(current_commit_file, "r") as f:
                for line in f.read().splitlines():
                    if line.startswith("tree "):
                        current_tree_hash = line[5:]
                        collect_files_from_tree(current_tree_hash, "", current_files)
                        break

    files_in_commit = set()
    collect_files_from_tree(tree_hash, "", files_in_commit)

    repo = find_repo()
    for file_path in current_files:
        if file_path not in files_in_commit:
            abs_path = os.path.join(repo, file_path)
            if os.path.exists(abs_path):
                os.remove(abs_path)

    for file_path in current_files:
        if file_path not in files_in_commit:
            folder = os.path.dirname(os.path.join(repo, file_path))
            while folder != repo:
                if os.path.exists(folder) and not os.listdir(folder):
                    os.rmdir(folder)
                folder = os.path.dirname(folder)

    restore_files(tree_hash)

    with open(head_path(), "w") as f:
        f.write(commit_hash)

    index_entries = []
    collect_index_entries(tree_hash, "", index_entries)

    with open(index_path(), "w") as idx:
        for mode, file_path in index_entries:
            idx.write(f"{mode}\t{escape_path(file_path)}\n")

    return f"Reset to {commit_hash[:8]}"


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