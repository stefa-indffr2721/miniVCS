import hashlib

from repository import *


def create_blob(file_path):
    repo = find_repo()
    abs_path = os.path.normpath(os.path.join(repo, file_path))

    if not os.path.exists(abs_path):
        return None

    with open(abs_path, "rb") as f:
        content = f.read()

    blob_hash = hashlib.sha1(content).hexdigest()

    os.makedirs(objects_path(), exist_ok=True)

    blob_file = os.path.join(objects_path(), blob_hash)

    if not os.path.exists(blob_file):
        with open(blob_file, "wb") as f:
            f.write(content)

    return blob_hash


def build_tree_structure(index_entries):
    root = {}

    for mode, file_path in index_entries:
        parts = file_path.split("/")
        node = root

        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                node[part] = ("blob", file_path, mode)
            else:
                if part not in node:
                    node[part] = ("tree", {})
                node = node[part][1]

    return root


def write_tree(tree_dict):
    entries = []

    for name in sorted(tree_dict.keys()):
        node = tree_dict[name]

        if node[0] == "blob":
            _, file_path, mode = node
            blob_hash = create_blob(file_path)
            if blob_hash:
                entries.append(f"{mode} blob {blob_hash} {name}")

        elif node[0] == "tree":
            subtree = node[1]
            sub_hash = write_tree(subtree)
            if sub_hash:
                entries.append(f"040000 tree {sub_hash} {name}")

    if not entries:
        return None

    tree_body = "\n".join(entries)
    tree_hash = hashlib.sha1(tree_body.encode()).hexdigest()

    os.makedirs(objects_path(), exist_ok=True)

    with open(os.path.join(objects_path(), tree_hash), "w") as f:
        f.write(tree_body)

    return tree_hash


def create_tree():
    if not os.path.exists(index_path()):
        return None

    with open(index_path(), "r") as f:
        index_entries = []

        for line in f:
            line = line.strip()

            if not line:
                continue

            mode, path = line.split("\t", 1)
            index_entries.append((mode, unescape_path(path)))

    tree_dict = build_tree_structure(index_entries)

    return write_tree(tree_dict)