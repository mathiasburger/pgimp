import os


def get_content(file: str) -> str:
    with open(file, 'r') as file_handle:
        content = file_handle.read()
    return content


def relative_to(file: str, path: str):
    return os.path.join(os.path.dirname(file), path)
