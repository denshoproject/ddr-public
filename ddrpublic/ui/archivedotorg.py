import re

from django.conf import settings
from django.core.cache import cache
import httpx

# "... [ia_external_id:EXTERNALID]; ..."
EXTERNAL_OBJECT_ID_PATTERN = re.compile(r'ia_external_id:([\w._-]+)')


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
        result = httpx.get(url, timeout=10)
        data = result.json()
        results = data
        cache.set(key, results, settings.CACHE_TIMEOUT)
    return results
