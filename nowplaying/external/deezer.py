# Slightly modified version of https://github.com/kmille/deezer-downloader/blob/master/deezer_downloader/deezer.py
import html.parser
import json
import re
import struct
from binascii import a2b_hex, b2a_hex
from io import BytesIO

from Crypto.Cipher import AES, Blowfish
from Crypto.Hash import MD5
from httpx import AsyncClient, Timeout

from ..core.config import config


# BEGIN TYPES
TYPE_TRACK = 'track'
TYPE_ALBUM = 'album'
TYPE_PLAYLIST = 'playlist'
TYPE_ALBUM_TRACK = 'album_track'  # used for listing songs of an album
# END TYPES

session = AsyncClient(
    headers={
        'Pragma': 'no-cache',
        'Origin': 'https://www.deezer.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 '
                      'Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': '*/*',
        'Cache-Control': 'no-cache',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': 'https://www.deezer.com/login',
        'DNT': '1',
    },
    cookies={
        'arl': config.DEEZER_ARL_COOKIE,
        'comeback': '1'
    },
    timeout=Timeout(timeout=60.)
)


class Deezer404Exception(Exception):
    pass


class Deezer403Exception(Exception):
    pass


class ScriptExtractor(html.parser.HTMLParser):
    """ extract <script> tag contents from a html page """

    def __init__(self):
        html.parser.HTMLParser.__init__(self)
        self.scripts = []
        self.curtag = None

    def handle_starttag(self, tag, attrs):
        self.curtag = tag.lower()

    def handle_data(self, data):
        if self.curtag == 'script':
            self.scripts.append(data)

    def handle_endtag(self, tag):
        self.curtag = None


def md5hex(data):
    """ return hex string of md5 of the given string """
    # type(data): bytes
    # returns: bytes
    h = MD5.new()
    h.update(data)
    return b2a_hex(h.digest())


def hexaescrypt(data, key):
    """ returns hex string of aes encrypted data """
    c = AES.new(key.encode(), AES.MODE_ECB)
    return b2a_hex(c.encrypt(data))


def genurlkey(songid, md5origin, mediaver=4, fmt=1):
    """ Calculate the deezer download url given the songid, origin and media+format """
    data_concat = b'\xa4'.join(_ for _ in [md5origin.encode(),
                                           str(fmt).encode(),
                                           str(songid).encode(),
                                           str(mediaver).encode()])
    data = b'\xa4'.join([md5hex(data_concat), data_concat]) + b'\xa4'
    if len(data) % 16 != 0:
        data += b'\0' * (16 - len(data) % 16)
    return hexaescrypt(data, 'jo6aey6haid2Teih')


def calcbfkey(songid):
    """ Calculate the Blowfish decrypt key for a given songid """
    key = b'g4el58wc0zvf9na1'
    songid_md5 = md5hex(songid.encode())

    def xor_op(i):
        return chr(songid_md5[i] ^ songid_md5[i + 16] ^ key[i])

    decrypt_key = ''.join([xor_op(i) for i in range(16)])
    return decrypt_key


def blowfishDecrypt(data, key):
    iv = a2b_hex('0001020304050607')
    c = Blowfish.new(key.encode(), Blowfish.MODE_CBC, iv)
    return c.decrypt(data)


def decryptfile(fh, key, fo):
    """
    Decrypt data from file <fh>, and write to file <fo>.
    decrypt using blowfish with <key>.
    Only every third 2048 byte block is encrypted.
    """
    blockSize = 2048
    i = 0

    def iter_slices(string, slice_length):
        """Iterate over slices of a string."""
        pos = 0
        if slice_length is None or slice_length <= 0:
            slice_length = len(string)
        while pos < len(string):
            yield string[pos: pos + slice_length]
            pos += slice_length

    for data in iter_slices(fh.content, blockSize):
        if not data:
            break

        isEncrypted = ((i % 3) == 0)
        isWholeBlock = len(data) == blockSize

        if isEncrypted and isWholeBlock:
            data = blowfishDecrypt(data, key)

        fo.write(data)
        i += 1


def writeid3v1_1(fo, song):
    # Bugfix changed song['SNG_TITLE... to song.get('SNG_TITLE... to avoid 'key-error' in case the key does not exist
    def song_get(song, key):
        try:
            return song.get(key).encode('utf-8')
        except:  # noqa
            return b''

    def album_get(key):
        global album_Data
        try:
            return album_Data.get(key).encode('utf-8')
        except:  # noqa
            return b''

    # what struct.pack expects
    # B => int
    # s => bytes
    data = struct.pack('3s' '30s' '30s' '30s' '4s' '28sB' 'H'  'B',
                       b'TAG',  # header
                       song_get(song, 'SNG_TITLE'),  # title
                       song_get(song, 'ART_NAME'),  # artist
                       song_get(song, 'ALB_TITLE'),  # album
                       album_get('PHYSICAL_RELEASE_DATE'),  # year
                       album_get('LABEL_NAME'), 0,  # comment
                       int(song_get(song, 'TRACK_NUMBER')),  # tracknum
                       255  # genre
                       )

    fo.write(data)


async def downloadpicture(pic_idid):
    resp = await session.get(get_picture_link(pic_idid))
    return resp.content


def get_picture_link(pic_idid):
    setting_domain_img = 'https://e-cdns-images.dzcdn.net/images'
    url = setting_domain_img + '/cover/' + pic_idid + '/1200x1200.jpg'
    return url


async def writeid3v2(fo, song):
    def make28bit(x):
        return ((x << 3) & 0x7F000000) | ((x << 2) & 0x7F0000) | ((x << 1) & 0x7F00) | (x & 0x7F)

    def maketag(tag, content):
        return struct.pack('>4sLH', tag.encode('ascii'), len(content), 0) + content

    def album_get(key):
        global album_Data
        try:
            return album_Data.get(key)
        except:  # noqa
            # raise
            return ''

    def song_get(song, key):
        try:
            return song[key]
        except:  # noqa
            # raise
            return ''

    def makeutf8(txt):
        # return b'\x03' + txt.encode('utf-8')
        return '\x03{}'.format(txt).encode()

    def makepic(data):
        # Picture type:
        # 0x00     Other
        # 0x01     32x32 pixels 'file icon' (PNG only)
        # 0x02     Other file icon
        # 0x03     Cover (front)
        # 0x04     Cover (back)
        # 0x05     Leaflet page
        # 0x06     Media (e.g. lable side of CD)
        # 0x07     Lead artist/lead performer/soloist
        # 0x08     Artist/performer
        # 0x09     Conductor
        # 0x0A     Band/Orchestra
        # 0x0B     Composer
        # 0x0C     Lyricist/text writer
        # 0x0D     Recording Location
        # 0x0E     During recording
        # 0x0F     During performance
        # 0x10     Movie/video screen capture
        # 0x11     A bright coloured fish
        # 0x12     Illustration
        # 0x13     Band/artist logotype
        # 0x14     Publisher/Studio logotype
        imgframe = (b'\x00',  # text encoding
                    b'image/jpeg', b'\0',  # mime type
                    b'\x03',  # picture type: 'Cover (front)'
                    b''[:64], b'\0',  # description
                    data
                    )

        return b''.join(imgframe)

    # get Data as DDMM
    try:
        phyDate_YYYYMMDD = album_get('PHYSICAL_RELEASE_DATE').split('-')  # '2008-11-21'
        phyDate_DDMM = phyDate_YYYYMMDD[2] + phyDate_YYYYMMDD[1]
    except:  # noqa
        phyDate_DDMM = ''

    # get size of first item in the list that is not 0
    try:
        FileSize = [
            song_get(song, i)
            for i in (
                'FILESIZE_AAC_64',
                'FILESIZE_MP3_320',
                'FILESIZE_MP3_256',
                'FILESIZE_MP3_64',
                'FILESIZE',
            ) if song_get(song, i)
        ][0]
    except:  # noqa
        FileSize = 0

    try:
        track = '%02s' % song['TRACK_NUMBER']
        track += '/%02s' % album_get('TRACKS')
    except:  # noqa
        pass

    # http://id3.org/id3v2.3.0#Attached_picture
    id3 = [
        maketag('TRCK', makeutf8(track)),
        # The 'Track number/Position in set' frame is a numeric string containing the order number of the audio-file
        # on its original recording. This may be extended with a '/' character and a numeric string containing the
        # total numer of tracks/elements on the original recording. E.g. '4/9'.
        maketag('TLEN', makeutf8(str(int(song['DURATION']) * 1000))),
        # The 'Length' frame contains the length of the audiofile in milliseconds, represented as a numeric string.
        maketag('TORY', makeutf8(str(album_get('PHYSICAL_RELEASE_DATE')[:4]))),
        # The 'Original release year' frame is intended for the year when the original recording was released. if for
        # example the music in the file should be a cover of a previously released song
        maketag('TYER', makeutf8(str(album_get('DIGITAL_RELEASE_DATE')[:4]))),
        # The 'Year' frame is a numeric string with a year of the recording. This frames is always four characters
        # long (until the year 10000).
        maketag('TDAT', makeutf8(str(phyDate_DDMM))),
        # The 'Date' frame is a numeric string in the DDMM format containing the date for the recording. This field
        # is always four characters long.
        maketag('TPUB', makeutf8(album_get('LABEL_NAME'))),
        # The 'Publisher' frame simply contains the name of the label or publisher.
        maketag('TSIZ', makeutf8(str(FileSize))),
        # The 'Size' frame contains the size of the audiofile in bytes, excluding the ID3v2 tag, represented as a
        # numeric string.
        maketag('TFLT', makeutf8('MPG/3')),

    ]  # decimal, no term NUL
    id3.extend([
        maketag(ID_id3_frame, makeutf8(song_get(song, ID_song))) for (ID_id3_frame, ID_song) in (
            ('TALB', 'ALB_TITLE'),
            # The 'Album/Movie/Show title' frame is intended for the title of the recording(/source of sound) which
            # the audio in the file is taken from.
            ('TPE1', 'ART_NAME'),
            # The 'Lead artist(s)/Lead performer(s)/Soloist(s)/Performing group' is used for the main artist(s). They
            # are seperated with the '/' character.
            ('TPE2', 'ART_NAME'),
            # The 'Band/Orchestra/Accompaniment' frame is used for additional information about the performers in the
            # recording.
            ('TPOS', 'DISK_NUMBER'),
            # The 'Part of a set' frame is a numeric string that describes which part of a set the audio came from.
            # This frame is used if the source described in the 'TALB' frame is divided into several mediums,
            # e.g. a double CD. The value may be extended with a '/' character and a numeric string containing the
            # total number of parts in the set. E.g. '1/2'.
            ('TIT2', 'SNG_TITLE'),
            # The 'Title/Songname/Content description' frame is the actual name of the piece (e.g. 'Adagio',
            # 'Hurricane Donna').
            ('TSRC', 'ISRC'),
            # The 'ISRC' frame should contain the International Standard Recording Code (ISRC) (12 characters).
        )
    ])

    try:
        id3.append(maketag('APIC', makepic(await downloadpicture(song['ALB_PICTURE']))))
    except Exception as e:
        print('ERROR: no album cover?', e)

    id3data = b''.join(id3)
    # >      big-endian
    # s      char[]  bytes
    # H      unsigned short  integer 2
    # B      unsigned char   integer 1
    # L      unsigned long   integer 4

    hdr = struct.pack('>'
                      '3s' 'H' 'B' 'L',
                      'ID3'.encode('ascii'),
                      0x300,  # version
                      0x00,  # flags
                      make28bit(len(id3data)))

    fo.write(hdr)
    fo.write(id3data)


async def download_song(song: dict, output_file: BytesIO) -> bool:
    # downloads and decrypts the song from Deezer. Adds ID3 and art cover
    # song: dict with information of the song (grabbed from Deezer.com)
    # output_file: absolute file name of the output file
    song_quality = 3 if song.get('FILESIZE_MP3_320') and song.get('FILESIZE_MP3_320') != '0' else \
        5 if song.get('FILESIZE_MP3_256') and song.get('FILESIZE_MP3_256') != '0' else 1

    urlkey = genurlkey(song['SNG_ID'], song['MD5_ORIGIN'], song['MEDIA_VERSION'], song_quality)
    key = calcbfkey(song['SNG_ID'])
    url = 'https://e-cdns-proxy-%s.dzcdn.net/mobile/1/%s' % (song['MD5_ORIGIN'][0], urlkey.decode())
    fh = await session.get(url)
    if fh.status_code != 200:
        # I don't why this happens. to reproduce:
        # go to https://www.deezer.com/de/playlist/1180748301
        # search for Moby
        # open in a new tab the song Moby - Honey
        # this will give you a 404!?
        # but you can play the song in the browser
        print('ERROR: Can not download this song. Got a {}'.format(fh.status_code))
        return False

    await writeid3v2(output_file, song)
    decryptfile(fh, key, output_file)
    writeid3v1_1(output_file, song)
    return True


async def get_song_infos_from_deezer_website(search_type, id):
    # search_type: either one of the constants: TYPE_TRACK|TYPE_ALBUM|TYPE_PLAYLIST
    # id: deezer_id of the song/album/playlist (like https://www.deezer.com/de/track/823267272)
    # return: if TYPE_TRACK => song (dict grabbed from the website with information about a song)
    # return: if TYPE_ALBUM|TYPE_PLAYLIST => list of songs
    # raises
    # Deezer404Exception if
    # 1. open playlist https://www.deezer.com/de/playlist/1180748301 and click on song Honey from Moby in a new tab:
    # 2. Deezer gives you a 404: https://www.deezer.com/de/track/68925038
    # Deezer403Exception if we are not logged in

    url = 'https://www.deezer.com/de/{}/{}'.format(search_type, id)
    resp = await session.get(url)
    if resp.status_code == 404:
        raise Deezer404Exception('ERROR: Got a 404 for {} from Deezer'.format(url))
    if 'MD5_ORIGIN' not in resp.text:
        raise Deezer403Exception('ERROR: we are not logged in on deezer.com. Please update the cookie')

    parser = ScriptExtractor()
    parser.feed(resp.text)
    parser.close()

    songs = []
    for script in parser.scripts:
        regex = re.search(r'{"DATA":.*', script)
        if regex:
            DZR_APP_STATE = json.loads(regex.group())
            global album_Data
            album_Data = DZR_APP_STATE.get('DATA')
            if DZR_APP_STATE['DATA']['__TYPE__'] == 'playlist' or DZR_APP_STATE['DATA']['__TYPE__'] == 'album':
                # songs if you searched for album/playlist
                for song in DZR_APP_STATE['SONGS']['data']:
                    songs.append(song)
            elif DZR_APP_STATE['DATA']['__TYPE__'] == 'song':
                # just one song on that page
                songs.append(DZR_APP_STATE['DATA'])
    return songs[0] if search_type == TYPE_TRACK else songs
