import argparse

from commands import init, add, commit, log, tag, reset


def get_args():
    parser = argparse.ArgumentParser(prog="vcs", description="Система контроля версий")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="инициализировать репозиторий")

    add_parser = subparsers.add_parser("add", help="добавить файл")
    add_parser.add_argument("file", type=str)

    tag_parser = subparsers.add_parser("tag", help="создать тег или показать список")
    tag_parser.add_argument("name", nargs="?", default="")
    tag_parser.add_argument("-m", "--message", default="")
    tag_parser.add_argument("-l", "--list", action="store_true")

    reset_parser = subparsers.add_parser("reset", help="откатиться до указанного коммита")
    reset_parser.add_argument("hash", type=str)

    subparsers.add_parser("log", help="просмотр лога коммитов")

    commit_parser = subparsers.add_parser("commit", help="зафиксировать изменения")
    commit_parser.add_argument("-m", "--message", default="")

    return parser.parse_args()


def main():
    args = get_args()

    if args.command == "init":
        print(init())

    elif args.command == "add":
        print(add(args.file))

    elif args.command == "commit":
        print(commit(args.message))

    elif args.command == "reset":
        print(reset(args.hash))

    elif args.command == "log":
        print(log())

    elif args.command == "tag":
        print(tag(args.name, message=args.message, list_tags=args.list))

    else:
        print("No command")


if __name__ == "__main__":
    main()
