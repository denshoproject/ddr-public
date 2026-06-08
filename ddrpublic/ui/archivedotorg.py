import json
from pathlib import Path
import re

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
import httpx2

# "... [ia_external_id:EXTERNALID]; ..."
EXTERNAL_OBJECT_ID_PATTERN = re.compile(r'ia_external_id:([\w._-]+)')


def handle_ia_external(entity):
    """Special processing for external IA videos
    - Get current direct URL for video
    - Check if they're stream-only
    see https://github.com/denshoproject/ddr-public/issues/230
    """
    try:
        ia_external_id = entity['ia_meta']['ia_external_id']
    except:
        ia_external_id = None
    if ia_external_id:
        entity['ia_meta']['files']['mp4']['url'] = get_mp4_url(ia_external_id)
        entity['ia_meta']['stream_only'] = is_streaming_only(ia_external_id)
    # special handling for certain stream-only videos in ddr-densho-1024
    if entity['id'] in BROKEN_ENTITY_FILE_URLS.keys():
        eid = entity['id']
        fid = BROKEN_ENTITY_FILE_URLS[eid]
        mp4_url = get_streaming_mpeg4_url(eid, fid)
        if mp4_url:
            entity['ia_meta']['files']['mp4']['url'] = mp4_url

def get_mp4_url(ia_external_id):
    """Get current URL for external IA video
    
    Some of these videos are marked streaming-only and have no stable URL.
    We have the IA identifier but we have to ask IA for the current server/dir
    so we can construct a URL for the MP4.
    see https://github.com/denshoproject/ddr-public/issues/230
    """
    iameta = get_ia_metadata(ia_external_id)
    if not iameta:
        return None
    iaserver = iameta['server']
    iadir = iameta['dir']
    for f in iameta['files']:
        if f['format'].lower() in ['h.264', 'mpeg4']:
            filename = f['name']
            mp4_url = f"https://{iaserver}{iadir}/{filename}"
            return mp4_url
    return None

def is_streaming_only(ia_external_id):
    """Indicate whether we can display a download link

    IA marks videos as stream-only by adding them to a global collection
    which appears in object metadata.

    Returns True (streaming-only), False (download okay), or None (shrug)
    """
    iameta = get_ia_metadata(ia_external_id)
    if not iameta:
        return None
    if 'stream_only' in iameta['metadata']['collection']:
        return True
    return False

def get_ia_metadata(ia_external_id: str) -> dict:
    """Use official IA client to get metadata for an IA object
    
    Cache so we don't hit the IA API too often.
    """
    key = f"archivedotorg:ia_meta:{ia_external_id}"
    results = cache.get(key)
    if not results:
        url = f"https://archive.org/metadata/{ia_external_id}"
        result = httpx2.get(url, timeout=10)
        data = result.json()
        results = data
        cache.set(key, results, settings.CACHE_TIMEOUT)
    return results

BROKEN_ENTITY_FILE_URLS = {
    'ddr-densho-1024-37': 'ddr-densho-1024-37-mezzanine-c87e531646',
    'ddr-densho-1024-45': 'ddr-densho-1024-45-mezzanine-7ba45b4b88',
    'ddr-densho-1024-55': 'ddr-densho-1024-55-mezzanine-7bb01254ca',
    'ddr-densho-1024-92': 'ddr-densho-1024-92-mezzanine-a65fa6c613',
}

def get_streaming_mpeg4_url(entity_id, file_id):
    """Special stream-only MP4 URLs for certain entities

    Certain videos will only play using an obfuscated URL
    For these videos, the .mp4 URL returns not a binary but a fragment
    of HTML. This fragment contains a <play-av> tag that contains
    the *actual* URL of the file.
    This function tries to return that actual URL.
    """
    url = f"https://archive.org/stream/{entity_id}/{file_id}.mp4"
    r = httpx2.get(url)
    if not r.status_code in [200, 301, 302]:
        return None
    sources = json.loads(
        BeautifulSoup(r.content).find_all('play-av')[0]['playlist']
    )
    mp4_urls = [
        filedata['file']
        for filedata in sources[0]['sources']
        if filedata['type'] == 'video/mp4'
    ]
    return mp4_urls[0]

