import json
import re
import subprocess

from django.core.cache import cache

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
        if f['format'] == 'h.264':
            filename = f['name']
            mp4_url = f"https://{iaserver}{iadir}/{filename}"
            return mp4_url
    return None

def get_ia_metadata(ia_external_id: str) -> dict:
    """Use official IA client to get metadata for an IA object
    
    Cache so we don't hit the IA API too often.
    """
    key = f"archivedotorg:ia_meta:{ia_external_id}"
    results = cache.get(key)
    if not results:

        cmd = f'ia metadata {ia_external_id}'
        try:
            out = subprocess.check_output(cmd.split()).decode()
        except FileNotFoundError:
            msg = "Internet Archive `ia` command required for this operation. " \
                "Install using 'pip install -U internetarchive'."
            raise Exception(msg)
        results = json.loads(out)

        cache.set(key, results, 60) #settings.CACHE_TIMEOUT)
    return results
