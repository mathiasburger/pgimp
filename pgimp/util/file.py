# Copyright 2018 Mathias Burger <mathias.burger@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import shutil


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
    with open(file, 'a', encoding='utf8') as file_handle:
        file_handle.write(content)


def copy_relative(src: str, dst: str):
    """
    If the new path only consists of a filename, the copy will be stored in the same directory as the original file.
    If the new path is relative, the copy will be stored relative to the original file. If the path is absolute,
    the copy will be stored in the absolute path.

    :param src: The source to copy.
    :param dst: The destination to copy to.
    :return: The destination file name.
    """
    if os.path.isabs(dst):
        shutil.copyfile(src, dst)
    else:
        dst = os.path.join(os.path.dirname(src), dst)
        shutil.copyfile(src, dst)
    return dst
