import os
from typing import Optional


def find_repo() -> Optional[str]:
    """Ищет корневую директорию репозитория, поднимаясь по дереву каталогов.

    Returns:
        абсолютный путь к корню репозитория, или None если не найден.
    """
    path = os.getcwd()

    while True:
        if os.path.exists(os.path.join(path, ".vcs")):
            return path

        parent = os.path.dirname(path)

        if parent == path:
            return None

        path = parent


def vcs_path() -> Optional[str]:
    """Возвращает путь к директории .vcs.

    Returns:
        путь к директории .vcs, или None если репозиторий не найден.
    """
    repo = find_repo()
    if not repo:
        return None
    return os.path.join(repo, ".vcs")


def index_path() -> str:
    """Возвращает путь к файлу индекса.

    Returns:
        путь к файлу index внутри .vcs.
    """
    return os.path.join(vcs_path(), "index")


def head_path() -> str:
    """Возвращает путь к файлу HEAD.

    Returns:
        путь к файлу head внутри .vcs.
    """
    return os.path.join(vcs_path(), "head")


def objects_path() -> str:
    """Возвращает путь к директории объектов.

    Returns:
        путь к директории objects внутри .vcs.
    """
    return os.path.join(vcs_path(), "objects")


def log_path() -> str:
    """Возвращает путь к директории логов коммитов.

    Returns:
        путь к директории log внутри .vcs.
    """
    return os.path.join(vcs_path(), "log")


def tags_path() -> str:
    """Возвращает путь к директории тегов.

    Returns:
        путь к директории tags внутри .vcs.
    """
    return os.path.join(vcs_path(), "tags")


def check_repo() -> bool:
    """Проверяет, инициализирован ли репозиторий в текущем дереве каталогов.

    Returns:
        True если директория .vcs существует, False иначе.
    """
    path = vcs_path()
    return path is not None and os.path.exists(path)


def escape_path(path: str) -> str:
    """Экранирует специальные символы в пути для хранения в индексе.

    Args:
        path: исходный путь к файлу.

    Returns:
        путь с экранированными пробелами, табуляциями и обратными слешами.
    """
    return (
        path.replace("\\", "\\\\")
            .replace(" ", "\\s")
            .replace("\t", "\\t")
    )


def unescape_path(path: str) -> str:
    """Восстанавливает оригинальный путь из экранированной строки.

    Args:
        path: экранированный путь из индекса.

    Returns:
        исходный путь с восстановленными специальными символами.
    """
    return (
        path.replace("\\t", "\t")
            .replace("\\s", " ")
            .replace("\\\\", "\\")
    )


def collect_reachable_objects(tree_hash: str, reachable: set[str]) -> None:
    """Рекурсивно собирает хеши всех объектов, достижимых из дерева.

    Args:
        tree_hash: хеш корневого объекта дерева.
        reachable: множество, в которое добавляются найденные хеши.
    """
    if tree_hash in reachable:
        return

    reachable.add(tree_hash)

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

            reachable.add(obj_hash)

            if obj_type == "tree":
                collect_reachable_objects(obj_hash, reachable)


def gc() -> str:
    """Удаляет недостижимые объекты из хранилища объектов.

    Returns:
        строка с количеством удалённых объектов.

    Raises:
        нет явных исключений, при отсутствии репозитория возвращает строку с ошибкой.
    """
    if not check_repo():
        return "GC ERROR: not init repo"

    reachable = set()

    for commit_hash in os.listdir(log_path()):
        commit_file = os.path.join(log_path(), commit_hash)

        if not os.path.isfile(commit_file):
            continue

        with open(commit_file, "r") as f:
            for line in f:
                if line.startswith("tree "):
                    tree_hash = line[5:].strip()
                    collect_reachable_objects(tree_hash, reachable)
                    break

    removed = 0

    for obj_hash in os.listdir(objects_path()):
        obj_file = os.path.join(objects_path(), obj_hash)

        if obj_hash not in reachable:
            if os.path.isfile(obj_file):
                os.remove(obj_file)
                removed += 1

    return f"GC: removed {removed} unreachable objects"