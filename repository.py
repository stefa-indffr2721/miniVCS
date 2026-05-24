import os


def find_repo():
    path = os.getcwd()

    while True:
        if os.path.exists(os.path.join(path, ".vcs")):
            return path

        parent = os.path.dirname(path)

        if parent == path:
            return None

        path = parent


def vcs_path():
    repo = find_repo()
    if not repo:
        return None
    return os.path.join(repo, ".vcs")


def index_path():
    return os.path.join(vcs_path(), "index")


def head_path():
    return os.path.join(vcs_path(), "head")


def objects_path():
    return os.path.join(vcs_path(), "objects")


def log_path():
    return os.path.join(vcs_path(), "log")


def check_repo():
    path = vcs_path()
    return path is not None and os.path.exists(path)


def escape_path(path):
    return (
        path.replace("\\", "\\\\")
            .replace(" ", "\\s")
            .replace("\t", "\\t")
    )


def unescape_path(path):
    return (
        path.replace("\\t", "\t")
            .replace("\\s", " ")
            .replace("\\\\", "\\")
    )