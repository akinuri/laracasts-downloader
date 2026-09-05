import os
import re
import shutil

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

def get_dir_contents(dir_path, real_path=True):
    item_names = [item_name for item_name in os.listdir(dir_path)]
    item_names.sort()
    if real_path:
        item_names = [os.path.realpath(os.path.join(dir_path, item_name)) for item_name in item_names]
    return item_names

def clear_dir(dir_path):
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)

def sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    return name.strip().rstrip(".")

def merge_files(file_paths, output_file_path):
    # write to a temp path first so an interrupted merge never leaves a partial file at output_file_path
    temp_output_path = output_file_path + ".part"
    with open(temp_output_path, "wb") as outfile:
        for file_path in file_paths:
            with open(file_path, "rb") as infile:
                outfile.write(infile.read())
    os.replace(temp_output_path, output_file_path)