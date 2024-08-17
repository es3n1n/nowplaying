from secrets import choice
from string import ascii_letters, digits


ALPHABET = ascii_letters + digits
QUERY_SEPARATOR = '_'


def random_string(length: int = 5) -> str:
    return ''.join([choice(ALPHABET) for _ in range(length)])


def chunks(line: str | bytes | list, size: int) -> list:
    result_chunks = []
    for index in range(0, len(line), size):
        result_chunks.append(line[index : index + size])  # noqa: PERF401
    return result_chunks


def extract_from_query(text: str, arguments_count: int = 2) -> list[str]:
    return text.split(QUERY_SEPARATOR, maxsplit=arguments_count - 1)


def encode_query(*args: str) -> str:
    return QUERY_SEPARATOR.join(args)
