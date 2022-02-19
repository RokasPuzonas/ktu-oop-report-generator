from os.path import join, relpath
from os import walk
from fnmatch import fnmatch
from typing import Iterable

def is_file_included(filename: str, included: list[str], excluded: list[str]) -> bool:
    for pattern in included:
        if not fnmatch(filename, pattern):
            return False

    for pattern in excluded:
        if fnmatch(filename, pattern):
            return False

    return True

def list_files(folder_path: str, included: list[str], excluded: list[str]) -> Iterable[str]:
    for (root, _, files) in walk(folder_path, topdown=True):
        for name in files:
            full_path = join(root, name)
            if is_file_included(relpath(full_path, folder_path), included, excluded):
                yield full_path
