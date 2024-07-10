import re

#region ==================== GENERAL

def input_adv(
        prompt_text,
        allow_empty = False,
        empty_warning = "Input can't be empty.",
        validate = None,
        invalid_warning = "Input is invalid.",
    ):
    value = input(prompt_text)
    if len(value) == 0:
        print(empty_warning)
        value = input_adv(prompt_text, allow_empty, empty_warning)
    if validate is not None and callable(validate):
        if validate(value) is False:
            print(invalid_warning)
            value = input_adv(prompt_text, allow_empty, empty_warning, validate, invalid_warning)
    return value

#endregion

#region ==================== LARACASTS

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

#endregion
