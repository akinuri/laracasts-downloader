import re

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