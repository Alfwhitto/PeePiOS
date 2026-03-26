COMMAND = "cat"
DESCRIPTION = "Read files, join multiple files, or write and append text using '>' and '>>'."


def _read_file(context, raw_path):
    target = context.resolve_path(raw_path)

    if not target.exists():
        raise FileNotFoundError(f"cat: {raw_path}: No such file or directory")

    if target.is_dir():
        raise IsADirectoryError(f"cat: {raw_path}: Is a directory")

    return target.read_text(encoding="utf-8")


def _read_stdin():
    lines = []
    terminator = "EOF"

    while True:
        try:
            line = input()
        except EOFError:
            break

        if line == terminator:
            break

        lines.append(line)

    if not lines:
        return ""

    return "\n".join(lines) + "\n"


def execute(context, args, commands):
    if not args:
        raise ValueError("cat: missing file operand")

    output_mode = None
    output_path = None
    source_paths = []
    index = 0

    while index < len(args):
        arg = args[index]

        if arg in {">", ">>"}:
            if output_mode is not None:
                raise ValueError("cat: multiple output redirections are not supported")
            if index + 1 >= len(args):
                raise ValueError(f"cat: expected file after '{arg}'")

            output_mode = "a" if arg == ">>" else "w"
            output_path = args[index + 1]
            index += 2
            continue

        source_paths.append(arg)
        index += 1

    if output_mode is None:
        print("".join(_read_file(context, raw_path) for raw_path in source_paths), end="")
        return

    target = context.resolve_path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if source_paths:
        content = "".join(_read_file(context, raw_path) for raw_path in source_paths)
    else:
        print("Enter text. Type EOF on its own line to finish.")
        content = _read_stdin()

    with target.open(output_mode, encoding="utf-8") as file_handle:
        file_handle.write(content)
