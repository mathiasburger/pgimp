import os


def get_content(file: str) -> str:
    with open(file, 'r') as file_handle:
        content = file_handle.read()
    return content


def relative_to(file: str, path: str):
    return os.path.join(os.path.dirname(file), path)


def touch(file: str):
    with open(file, 'a'):
        os.utime(file)


def append(file: str, content: str):
    with open(file, 'a') as file_handle:
        file_handle.write(content)
