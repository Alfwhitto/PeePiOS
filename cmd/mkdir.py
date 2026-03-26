COMMAND = "mkdir"
DESCRIPTION = "Create a new directory."


def execute(context, args, commands):
    if not args:
        raise ValueError("mkdir: missing operand")

    target = context.resolve_path(args[0])
    target.mkdir(parents=True, exist_ok=False)
