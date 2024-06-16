from random import choice
from string import ascii_letters, digits


ALPHABET = ascii_letters + digits


def escape_html(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def random_string(length: int = 5) -> str:
    return ''.join([choice(ALPHABET) for _ in range(length)])


def chunks(line, n: int) -> list:
    return [line[i:i + n] for i in range(0, len(line), n)]
