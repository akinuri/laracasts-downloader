import os
import re
import requests
from urllib.parse import urljoin

from helpers.config import get_required_env

# Laracasts now serves videos as standard HLS from media.laracasts.com
# instead of Vimeo's playlist.json format. media.laracasts.com rejects
# requests without a logged-in session's cookies, even with matching
# browser headers, so callers must use the session from build_session().

DEFAULT_HEADERS = {
    "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "Referer" : "https://laracasts.com/",
    "Origin" : "https://laracasts.com",
    "Sec-Fetch-Dest" : "empty",
    "Sec-Fetch-Mode" : "cors",
    "Sec-Fetch-Site" : "same-site",
}

def build_session():
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    session.cookies.set("laracasts_session", get_required_env("LARACASTS_SESSION"), domain=".laracasts.com")
    session.cookies.set("lc_video_auth", get_required_env("LC_VIDEO_AUTH"), domain=".laracasts.com")
    return session

def is_master_playlist_url(value):
    pattern = r"^https:\/\/media\.laracasts\.com\/videos\/[A-Za-z0-9]+\/v\d+\/hls\/master\.m3u8(\?.*)?$"
    return bool(re.fullmatch(pattern, value))

def parse_attribute_list(attrs_str):
    result = {}
    for match in re.finditer(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)', attrs_str):
        key, value = match.group(1), match.group(2)
        result[key] = value.strip('"')
    return result

def parse_master_playlist(m3u8_text):
    streams = []
    pending_stream = None
    for line in m3u8_text.splitlines():
        line = line.strip()
        if line.startswith("#EXT-X-STREAM-INF:"):
            attrs = parse_attribute_list(line.split(":", 1)[1])
            width, height = (int(value) for value in attrs["RESOLUTION"].split("x"))
            pending_stream = {
                "bandwidth" : int(attrs["BANDWIDTH"]),
                "width" : width,
                "height" : height,
                "url" : None,
            }
        elif line and not line.startswith("#"):
            if pending_stream is not None:
                pending_stream["url"] = line
                streams.append(pending_stream)
                pending_stream = None
    return streams

def get_video_heights(streams):
    heights = sorted(set(stream["height"] for stream in streams))
    return heights

def get_video_by_height(streams, video_height):
    result = None
    for stream in streams:
        if stream["height"] == video_height:
            result = stream
    return result

def parse_media_playlist(m3u8_text):
    init_segment_url = None
    segment_urls = []
    for line in m3u8_text.splitlines():
        line = line.strip()
        if line.startswith("#EXT-X-MAP:"):
            match = re.search(r'URI="([^"]+)"', line)
            if match:
                init_segment_url = match.group(1)
        elif line and not line.startswith("#"):
            segment_urls.append(line)
    return {
        "init_segment_url" : init_segment_url,
        "segment_urls" : segment_urls,
    }

def download_video_segments(session, media_playlist_url, media_playlist, segments_dir = "segments/video"):
    os.makedirs(segments_dir, exist_ok=True)
    segment_prefix = "segment"
    segment_count = len(media_playlist["segment_urls"])
    segment_digits = len(str(segment_count))
    if media_playlist["init_segment_url"]:
        init_segment_path = "%s/%s-%s.mp4" % (
            segments_dir,
            segment_prefix,
            "0".rjust(segment_digits, "0"),
        )
        init_url = urljoin(media_playlist_url, media_playlist["init_segment_url"])
        print("Downloading init segment ...")
        init_response = session.get(init_url, timeout=30)
        open(init_segment_path, "wb").write(init_response.content)
    for index, segment_url in enumerate(media_playlist["segment_urls"]):
        full_segment_url = urljoin(media_playlist_url, segment_url)
        print("Downloading segment %s/%s ..." % (str(index + 1), str(segment_count)))
        segment_response = session.get(full_segment_url, timeout=30)
        segment_path = "%s/%s-%s.m4s" % (
            segments_dir,
            segment_prefix,
            str(index + 1).rjust(segment_digits, "0"),
        )
        open(segment_path, "wb").write(segment_response.content)

def build_captions_url(master_playlist_url, language = "en"):
    match = re.match(r"^(https:\/\/media\.laracasts\.com\/videos\/[A-Za-z0-9]+\/v\d+)\/hls\/master\.m3u8", master_playlist_url)
    if not match:
        return None
    return "%s/captions/%s.vtt" % (match.group(1), language)