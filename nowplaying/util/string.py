from secrets import choice
from string import ascii_letters, digits


ALPHABET = ascii_letters + digits


def escape_html(string: str) -> str:
    return string.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def random_string(length: int = 5) -> str:
    return ''.join([choice(ALPHABET) for _ in range(length)])


def chunks(line, size: int) -> list:
    result_chunks = []
    for index in range(0, len(line), size):
        result_chunks.append(line[index:index + size])
    return result_chunks
