import os

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

def merge_files(file_paths, output_file_path):
    with open(output_file_path, "wb") as outfile:
        for file_path in file_paths:
            with open(file_path, "rb") as infile:
                outfile.write(infile.read())