from helpers import input_adv, is_playlist_json_url

playlist_url = input_adv(
    "playlist.json URL: ",
    validate=is_playlist_json_url,
)

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
