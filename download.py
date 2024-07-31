import json
import sys
import requests

from helpers.general import get_dir_contents, input_adv, merge_files
from helpers.laracasts import download_video_segments, get_video_by_height, get_video_heights, is_playlist_json_url, parse_playlist_url


playlist_url = input_adv(
    "playlist.json URL: ",
    validate=is_playlist_json_url,
)
parsed_playlist_url = parse_playlist_url(playlist_url)

print(json.dumps(parsed_playlist_url, indent=4))


playlist_response = requests.get(playlist_url)
if playlist_response.ok is False:
    print("Request to the playlist URL failed. URL might be expired. Try a new one.")
    input()
    sys.exit()
playlist_json = json.loads(playlist_response.text)

print(json.dumps(playlist_json, indent=4))


available_video_heights = get_video_heights(playlist_json)
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


selected_video = get_video_by_height(playlist_json, selected_video_height)
download_video_segments(selected_video, parsed_playlist_url)
video_segments = get_dir_contents("segments/video")

print(json.dumps(video_segments, indent=4))


merge_files(video_segments, "segments/video.mp4")


print("Moving on ...")
input()


# TODO: select audio
# TODO: download audio segments
# TODO: merge audio segments
# TODO: merge the video and the audio
