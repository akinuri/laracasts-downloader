import json
import sys
import requests
from helpers import input_adv, is_playlist_json_url, parse_playlist_url

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

json_data = json.loads(playlist_response.text)

print(json.dumps(json_data, indent=4))

print("Moving on ...")
input()


# TODO: select video
# TODO: download video segments
# TODO: merge video segments
# TODO: select audio
# TODO: download audio segments
# TODO: merge audio segments
# TODO: merge the video and the audio
