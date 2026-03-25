COMMAND = "cd"
DESCRIPTION = "Change the current directory. Use 'cd /' to return to the PeePiOS root."


def execute(context, args, commands):
    destination = args[0] if args else "/"
    target = context.resolve_path(destination)

    if not target.exists():
        raise FileNotFoundError(f"cd: no such file or directory: {destination}")

    if not target.is_dir():
        raise NotADirectoryError(f"cd: not a directory: {destination}")

    context.cwd = target
