COMMAND = "ls"
DESCRIPTION = "List files and folders in the current directory or in a provided path."


def execute(context, args, commands):
    target = context.resolve_path(args[0] if args else ".")

    if not target.exists():
        raise FileNotFoundError(f"ls: cannot access '{args[0]}': No such file or directory")

    if target.is_file():
        print(target.name)
        return

    entries = sorted(target.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
    print("  ".join(entry.name for entry in entries))
