import os
import re
import time


def save_document_to_disk(directory_path: str, title: str, body: str) -> str:
    document_file_name = get_safe_file_name(title)
    document_file_path = f"{directory_path}/{document_file_name}"

    with open(document_file_path, "w") as file:
        # Append data to the file
        file.write(body)

    return document_file_path


def get_safe_file_name(name: str, file_extension: str = ".txt") -> str:
    MAX_CHARACTERS = 200

    if len(name) > MAX_CHARACTERS:
        name = name[:MAX_CHARACTERS]

    # Replace characters not allowed in filenames with underscore
    safe_file_name = strip_non_alpha_characters(input=name)

    current_timestamp = int(time.time())
    safe_file_name = f"{safe_file_name}-{current_timestamp}{file_extension}"
    safe_file_name = safe_file_name.lower()

    return safe_file_name


def strip_non_alpha_characters(input: str, replacement_character: str = "_") -> str:
    # Replace characters not allowed in filenames with underscore
    output = re.sub(r"\W+", replacement_character, input)
    output = output.strip()

    # Replace consecutive spaces with single space
    output = re.sub(r"\s+", " ", output)
    output = output.replace(" ", replacement_character)

    return output


def delete_file(filepath: str) -> tuple[bool, str | None]:
    file_was_deleted = False
    warning_message = None

    try:
        os.remove(filepath)
        file_was_deleted = True
    except FileNotFoundError:
        warning_message = f"{filepath}: file not found."
    except PermissionError:
        warning_message = f"{filepath}: Permission denied. Check file permissions."
    except Exception as e:
        warning_message = f"{filepath}: Error occurred: {e}"

    return (file_was_deleted, warning_message)
