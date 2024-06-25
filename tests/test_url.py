from nowplaying.util.url import urlparse


def test_www_strip() -> None:
    assert urlparse('https://www.es3n1n.eu/').netloc == 'es3n1n.eu'
    assert urlparse('https://www.es3n1n.eu/', keep_www=True).netloc == 'www.es3n1n.eu'
    assert urlparse('https://es3n1n.eu/').netloc == 'es3n1n.eu'
