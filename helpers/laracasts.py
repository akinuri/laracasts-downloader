import base64
import os
import re
import requests

def is_playlist_json_url(value):
    pattern = r"^https:\/\/vod-adaptive-ak\.vimeocdn\.com\/[^/]+\/[^/]+\/v2\/playlist\/av\/primary\/playlist\.json\?[^/]{70,}$"
    return bool(re.fullmatch(pattern, value))

def parse_playlist_url(playlist_url):
    playlist_url = playlist_url.replace("//", "$$")
    parts = playlist_url.split("/")
    result = {
        "base" : parts[0].replace("$$", "//"),
        "session" : parts[1],
        "clip_id" : parts[2],
        "custom" : "/".join(parts[3:7]),
        "playlist" : parts[7],
    }
    return result

def get_video_heights(playlist_json):
    heights = []
    for video in playlist_json["video"]:
        heights.append(video["height"])
    heights.sort()
    return heights

def get_video_by_height(playlist_json, video_height):
    result = None
    for video in playlist_json["video"]:
        if video["height"] == video_height:
            result = video
    return result

def download_video_segments(video, parsed_video_playlist_url, segments_dir = "segments/video"):
    segment_prefix = "segment"
    segment_count = len(video["segments"])
    segment_digits = len(str(segment_count))
    init_segment_path = "%s/%s-%s.mp4" % (
        segments_dir,
        segment_prefix,
        "0".rjust(segment_digits, "0"),
    )
    init_segment_dir = os.path.dirname(init_segment_path)
    os.makedirs(init_segment_dir, exist_ok=True)
    open(init_segment_path, "wb").write(base64.b64decode(video["init_segment"]))
    for index, segment in enumerate(video["segments"]):
        video_segment_dict = build_video_segment_dict(
            parsed_video_playlist_url,
            video["id"],
            segment["url"],
        )
        video_segment_url = build_video_segment_url(video_segment_dict)
        segment_response = requests.get(video_segment_url)
        print("Downloading segment %s/%s" % (str(index + 1), str(segment_count)))
        segment_path = "%s/%s-%s.m4s" % (
            segments_dir,
            segment_prefix,
            str(index + 1).rjust(segment_digits, "0"),
        )
        open(segment_path, "wb").write(segment_response.content)

def build_video_segment_dict(parsed_playlist_url, video_id, segment_url):
    result = {
        "base" : parsed_playlist_url["base"],
        "session" : parsed_playlist_url["session"],
        "clip_id" : parsed_playlist_url["clip_id"],
        "custom" : "/v2/remux/avf",
        "custom" : "/".join(["v2", "remux", "avf"]),
        "video_id" : video_id,
        "segment" : segment_url,
    }
    return result

def build_video_segment_url(dict):
    values = list(dict.values())
    url = "/".join(values)
    return url