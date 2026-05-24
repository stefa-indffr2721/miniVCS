import argparse

from commands import init, add, commit


def get_args():
    parser = argparse.ArgumentParser(prog="vcs", description="Система контроля версий")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="инициализировать репозиторий")

    add_parser = subparsers.add_parser("add", help="добавить файл")
    add_parser.add_argument("file", type=str)

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

    else:
        print("No command")


if __name__ == "__main__":
    main()
