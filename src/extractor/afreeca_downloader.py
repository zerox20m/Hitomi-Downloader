# uncompyle6 version 3.5.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.16 (v2.7.16:413a49145e, Mar  4 2019, 01:30:55) [MSC v.1500 32 bit (Intel)]
# Embedded file name: afreeca_downloader.pyo
# Compiled at: 2019-10-07 03:48:35
import downloader
from utils import Soup, Downloader, get_outdir, Session, LazyUrl, compatstr, try_n
import re
from fucking_encoding import clean_title
from timee import sleep
import os
from io import BytesIO
import shutil
from m3u8_tools import playlist2stream, M3u8_stream

class Video(object):

    def __init__(self, stream, referer, id, title, url_thumb, format='title'):
        self.url = LazyUrl(referer, lambda x: stream, self)
        self.id = id
        format = format.replace('title', '###title').replace('id', '###id')
        title = format.replace('###title', title).replace('###id', (u'{}').format(self.id))
        self.title = title
        self.filename = u'{}.mp4'.format(clean_title(title))
        self.url_thumb = url_thumb
        self.thumb = BytesIO()
        downloader.download(url_thumb, buffer=self.thumb)


@Downloader.register
class Downloader_afreeca(Downloader):
    type = 'afreeca'
    URLS = ['afreecatv.com']
    single = True

    def init(self):
        self.url = self.url.replace('afreeca_', '')

    @property
    def id(self):
        return self.url

    def read(self):
        format = compatstr(self.ui_setting.youtubeFormat.currentText()).lower().strip()
        session = Session()
        video = get_video(self.url, session, format)
        self.urls.append(video.url)

        self.setIcon(video.thumb)
        
        self.title = video.title


@try_n(4)
def _get_stream(url_m3u8):
    print('_get_stream', url_m3u8)
    try:
        stream = playlist2stream(url_m3u8)
    except Exception as e:
        print(e)
        stream = M3u8_stream(url_m3u8)
    return stream


@try_n(2)
def get_video(url, session, format='title'):
    while url.strip().endswith('/'):
        url = url[:-1]

    html = downloader.read_html(url, session=session)
    soup = Soup(html)
    url_thumb = soup.find('meta', {'property': 'og:image'}).attrs['content']
    params = re.findall('VodParameter *= *[\'"]([^\'"]+)[\'"]', html)[0]
    url_xml = 'http://afbbs.afreecatv.com:8080/api/video/get_video_info.php?' + params
    print(url_xml)
    html = downloader.read_html(url_xml, session=session, referer=url)
    soup = Soup(html)
    title = soup.find('title').string.strip()
    urls_m3u8 = re.findall('https?://[^>]+playlist.m3u8', html)
    if not urls_m3u8:
        raise Exception('no m3u8')
    streams = []
    for url_m3u8 in urls_m3u8:
        try:
            stream = _get_stream(url_m3u8)
        except Exception as e:
            print(e)
            continue #2193
        streams.append(stream)
    for stream in streams[1:]:
        streams[0] += stream
    stream = streams[0]
    id = url.split('/')[(-1)].split('?')[0].split('#')[0]
    video = Video(stream, url, id, title, url_thumb, format)
    return video
