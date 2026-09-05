import json
import sys
import requests
from urllib.parse import urljoin

from helpers.config import load_env_file
from helpers.general import get_dir_contents, input_adv, merge_files
from helpers.laracasts import (
    build_captions_url,
    build_session,
    download_video_segments,
    get_video_by_height,
    get_video_heights,
    is_master_playlist_url,
    parse_master_playlist,
    parse_media_playlist,
)


load_env_file()
session = build_session()

master_playlist_url = input_adv(
    "master.m3u8 URL: ",
    validate=is_master_playlist_url,
)

print("Fetching master playlist ...")
try:
    master_playlist_response = session.get(master_playlist_url, timeout=30)
except requests.exceptions.RequestException as error:
    print("Request to the master playlist URL failed: %s" % str(error))
    input()
    sys.exit()
if master_playlist_response.ok is False:
    print("Request to the master playlist URL failed. URL might be expired. Try a new one.")
    input()
    sys.exit()
print("Fetched master playlist.")

available_streams = parse_master_playlist(master_playlist_response.text)

print(json.dumps(available_streams, indent=4))


available_video_heights = get_video_heights(available_streams)
print("Select a video resolution:")
for height in available_video_heights:
    print("- %d" % height)
def is_valid_video_height(input):
    try:
        input = int(input)
    except:
        input = 0
    return input in available_video_heights
selected_video_height = input_adv(
    "Your choice: ",
    validate=is_valid_video_height,
)
selected_video_height = int(selected_video_height)

print("Selected video height: %d" % selected_video_height)


selected_stream = get_video_by_height(available_streams, selected_video_height)
media_playlist_url = urljoin(master_playlist_url, selected_stream["url"])

print("Fetching media playlist ...")
try:
    media_playlist_response = session.get(media_playlist_url, timeout=30)
except requests.exceptions.RequestException as error:
    print("Request to the media playlist URL failed: %s" % str(error))
    input()
    sys.exit()
if media_playlist_response.ok is False:
    print("Request to the media playlist URL failed. URL might be expired. Try a new one.")
    input()
    sys.exit()
print("Fetched media playlist.")

media_playlist = parse_media_playlist(media_playlist_response.text)
segment_count = len(media_playlist["segment_urls"])
print("Downloading %d segments ..." % segment_count)

download_video_segments(session, media_playlist_url, media_playlist)
video_segments = get_dir_contents("segments/video")

print("Downloaded %d segment files." % len(video_segments))


print("Merging segments into segments/video.mp4 ...")
merge_files(video_segments, "segments/video.mp4")
print("Merged.")


captions_url = build_captions_url(master_playlist_url)
if captions_url:
    print("Fetching captions ...")
    try:
        captions_response = session.get(captions_url, timeout=30)
        if captions_response.ok:
            open("segments/en.vtt", "wb").write(captions_response.content)
            print("Captions saved.")
        else:
            print("Captions not available.")
    except requests.exceptions.RequestException as error:
        print("Fetching captions failed: %s" % str(error))


print("Done.")
input()

