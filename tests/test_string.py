from nowplaying.util.string import chunks, encode_query, extract_from_query


def test_chunks() -> None:
    assert chunks('ababa', 2) == ['ab', 'ab', 'a']


def test_query_builder() -> None:
    query = encode_query('test', 'hello', 'asdasd')
    assert extract_from_query(query, arguments_count=3) == ['test', 'hello', 'asdasd']

