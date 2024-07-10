import json
from helpers import input_adv, is_playlist_json_url, parse_playlist_url

playlist_url = input_adv(
    "playlist.json URL: ",
    validate=is_playlist_json_url,
)

parsed_playlist_url = parse_playlist_url(playlist_url)

print(json.dumps(parsed_playlist_url, indent=4))

print("Moving on ...")
input()


# TODO: get playlist.json response
# TODO: select video
# TODO: download video segments
# TODO: merge video segments
# TODO: select audio
# TODO: download audio segments
# TODO: merge audio segments
# TODO: merge the video and the audio
