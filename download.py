import os
import sys
import requests
from urllib.parse import urljoin

from helpers.config import load_env_file
from helpers.general import clear_dir, get_dir_contents, input_adv, merge_files, sanitize_filename
from helpers.laracasts import (
    build_absolute_url,
    build_session,
    choose_closest_height,
    download_video_segments,
    fetch_page_json,
    get_lesson_playback,
    get_video_by_height,
    get_video_heights,
    is_course_url,
    list_course_episodes,
    normalize_course_url,
    parse_master_playlist,
    parse_media_playlist,
)

WORK_DIR = "work"
OUTPUT_DIR = "downloads"
AVAILABLE_HEIGHTS = [480, 720, 1080, 1440, 2160]


load_env_file()
session = build_session()

course_url = input_adv(
    "Course URL (e.g. https://laracasts.com/series/laravel-from-scratch-2026): ",
    validate=is_course_url,
)
course_url = normalize_course_url(course_url)

print("Fetching course info ...")
try:
    first_episode_json = fetch_page_json(session, course_url + "/episodes/1")
except requests.exceptions.RequestException as error:
    print("Request to the course URL failed: %s" % str(error))
    input()
    sys.exit()

course_title = first_episode_json["props"]["series"]["title"]
episodes = list_course_episodes(first_episode_json)

print("Course: %s (%d episodes)" % (course_title, len(episodes)))

print("Preferred video resolution (used for every episode; falls back to the closest available height):")
for height in AVAILABLE_HEIGHTS:
    print("- %d" % height)
def is_valid_height_choice(input):
    try:
        return int(input) > 0
    except:
        return False
preferred_height = int(input_adv("Your choice: ", validate=is_valid_height_choice))


course_dir = os.path.join(OUTPUT_DIR, sanitize_filename(course_title))
work_video_dir = os.path.join(WORK_DIR, "video")

for episode in episodes:
    episode_label = "%02d - %s" % (episode["position"], episode["title"])
    print("")
    print("=== %s ===" % episode_label)

    chapter_dir = os.path.join(course_dir, "%02d - %s" % (episode["chapter_number"], sanitize_filename(episode["chapter_heading"])))
    base_name = "%02d - %s" % (episode["position"], sanitize_filename(episode["title"]))
    video_output_path = os.path.join(chapter_dir, base_name + ".mp4")
    captions_output_path = os.path.join(chapter_dir, base_name + ".en.vtt")

    if os.path.exists(video_output_path):
        print("Already downloaded. Skipping.")
        continue

    episode_url = build_absolute_url(episode["path"])
    try:
        episode_json = fetch_page_json(session, episode_url)
    except requests.exceptions.RequestException as error:
        print("Failed to fetch episode page: %s" % str(error))
        continue

    playback = get_lesson_playback(episode_json)
    if not playback or not playback.get("src"):
        print("No video available for this episode (locked or unpublished). Skipping.")
        continue
    master_playlist_url = playback["src"]

    try:
        master_playlist_response = session.get(master_playlist_url, timeout=30)
        master_playlist_response.raise_for_status()
    except requests.exceptions.RequestException as error:
        print("Failed to fetch master playlist: %s" % str(error))
        continue

    available_streams = parse_master_playlist(master_playlist_response.text)
    available_video_heights = get_video_heights(available_streams)
    chosen_height = choose_closest_height(available_video_heights, preferred_height)
    selected_stream = get_video_by_height(available_streams, chosen_height)
    print("Using video height: %d" % chosen_height)

    media_playlist_url = urljoin(master_playlist_url, selected_stream["url"])
    try:
        media_playlist_response = session.get(media_playlist_url, timeout=30)
        media_playlist_response.raise_for_status()
    except requests.exceptions.RequestException as error:
        print("Failed to fetch media playlist: %s" % str(error))
        continue

    media_playlist = parse_media_playlist(media_playlist_response.text)
    print("Downloading %d segments ..." % len(media_playlist["segment_urls"]))

    clear_dir(work_video_dir)
    download_video_segments(session, media_playlist_url, media_playlist, segments_dir=work_video_dir)
    video_segments = get_dir_contents(work_video_dir)

    os.makedirs(chapter_dir, exist_ok=True)
    print("Merging segments into %s ..." % video_output_path)
    merge_files(video_segments, video_output_path)

    captions = playback.get("captions") or []
    english_captions = next((caption for caption in captions if caption.get("language") == "en"), None)
    if english_captions:
        try:
            captions_response = session.get(english_captions["src"], timeout=30)
            if captions_response.ok:
                open(captions_output_path, "wb").write(captions_response.content)
                print("Captions saved.")
        except requests.exceptions.RequestException:
            print("Fetching captions failed, skipping.")

    print("Done with %s." % episode_label)

clear_dir(work_video_dir)
print("")
print("All episodes processed.")
input()

