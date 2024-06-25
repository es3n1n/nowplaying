from nowplaying.util.string import chunks, escape_html


def test_escape_html() -> None:
    assert escape_html('&TEST HELLO > AND < HMM &amp') == '&amp;TEST HELLO &gt; AND &lt; HMM &amp;amp'


def test_chunks() -> None:
    assert chunks('ababa', 2) == ['ab', 'ab', 'a']

