COMMAND = "touch"
DESCRIPTION = "Create an empty file, or update the timestamp of an existing file."


def execute(context, args, commands):
    if not args:
        raise ValueError("touch: missing file operand")

    target = context.resolve_path(args[0])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch(exist_ok=True)
