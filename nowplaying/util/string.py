from secrets import choice
from string import ascii_letters, digits


ALPHABET = ascii_letters + digits


# We only need these: https://core.telegram.org/bots/api#html-style
def escape_html(string: str) -> str:
    escape_rules = [
        ('&', '&amp;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
    ]
    for old, new in escape_rules:
        string = string.replace(old, new)
    return string


def random_string(length: int = 5) -> str:
    return ''.join([choice(ALPHABET) for _ in range(length)])


def chunks(line, size: int) -> list:
    result_chunks = []
    for index in range(0, len(line), size):
        result_chunks.append(line[index:index + size])
    return result_chunks
