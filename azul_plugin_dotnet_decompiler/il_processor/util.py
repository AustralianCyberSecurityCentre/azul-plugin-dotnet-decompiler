"""String manipulation utility functions."""

# For replacing spaces in strings, to avoid breaking regexes in il_parser.
# The magic string needs to not occur in il code.
magic = "!b@n@n@!"


def redo_space(line: str) -> str:
    """Turns 'magic' back to spaces, then re-magics any spaces that are in brackets."""
    i = line
    i = unreplace_space(i)
    i = replace_space(i)
    return i


def replace_space(line: str) -> str:
    """Replaces spaces within brackets with a magic number."""
    if not line:
        return ""
    outline = line
    pairs = {"[": "]", "'": "'", "(": ")", "<": ">"}
    bracket_stack = []
    i = 0
    while i < len(outline):
        char = outline[i]
        if len(bracket_stack) > 0:
            # last_b is the char we expect to close the most recent brackets
            last_b = bracket_stack[len(bracket_stack) - 1]
        else:
            last_b = None

        if char in pairs and last_b != char:
            # add closing bracket to the stack
            bracket_stack.append(pairs[char])
        elif last_b == char:
            bracket_stack.pop()

        if len(bracket_stack) > 0 and char == " ":
            outline = outline[:i] + magic + outline[i + 1 :]
            i += len(magic) - 1
        i += 1
    return outline


def unreplace_space(line: str) -> str:
    """Replaces magic patterns in a line with a space."""
    return line.replace(magic, " ") if line else ""
