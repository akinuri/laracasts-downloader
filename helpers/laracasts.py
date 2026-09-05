import json
import os
import re
import requests
from urllib.parse import urljoin

from helpers.config import get_required_env

# Laracasts now serves videos as standard HLS from media.laracasts.com
# instead of Vimeo's playlist.json format. media.laracasts.com rejects
# requests without a logged-in session's cookies, even with matching
# browser headers, so callers must use the session from build_session().
# Visiting an episode's page (fetch_page_json) refreshes the session's
# lc_video_auth cookie for that specific video automatically.

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
    return session

def is_course_url(value):
    pattern = r"^https:\/\/laracasts\.com\/series\/[a-z0-9-]+\/?(?:\?.*)?$"
    return bool(re.fullmatch(pattern, value))

def normalize_course_url(value):
    match = re.match(r"^https:\/\/laracasts\.com\/series\/[a-z0-9-]+", value)
    return match.group(0)

def build_absolute_url(path):
    return urljoin("https://laracasts.com", path)

def fetch_page_json(session, url):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    match = re.search(r'<script data-page="app" type="application/json">(.*?)</script>', response.text, re.S)
    if not match:
        raise RuntimeError("Could not find embedded page data at %s" % url)
    return json.loads(match.group(1))

def list_course_episodes(page_json):
    episodes = []
    for chapter in page_json["props"]["series"]["chapters"]:
        for episode in chapter["episodes"]:
            episodes.append({
                "id" : episode["id"],
                "chapter_number" : chapter["number"],
                "chapter_heading" : chapter["heading"],
                "position" : episode["position"],
                "title" : episode["title"],
                "path" : episode["path"],
            })
    return episodes

def get_lesson_playback(page_json):
    lesson = page_json["props"]["lesson"]
    return lesson.get("cloudflarePlayback")

def choose_closest_height(available_heights, desired_height):
    if desired_height in available_heights:
        return desired_height
    lower_or_equal = [height for height in available_heights if height <= desired_height]
    if lower_or_equal:
        return max(lower_or_equal)
    return min(available_heights)

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

def download_video_segments(session, media_playlist_url, media_playlist, segments_dir = "work/video"):
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