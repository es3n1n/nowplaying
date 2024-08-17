def is_mp3(data: bytes) -> bool:
    # ref: https://en.wikipedia.org/wiki/List_of_file_signatures
    return data[:3] == b'ID3' or data[:2] in {b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'}
