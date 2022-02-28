"""Module containing general utilities for parsing"""
import gzip
from typing import Callable, Union

ParseT = Union[None, float, int, str]


def parse_type(item: str, na: None = None) -> ParseT:
    """
    Attempts to parse a string into basic python types.
    """
    value: ParseT = None

    try:
        if not item:
            value = na
        elif "." in item:
            value = float(item)
        else:
            value = int(item)
    except ValueError:
        value = item

    return value


def get_read_func(fpath: str) -> Callable:
    """
    Returns either the open or gzip.open function
    for a provided file path. This is only for reading, so the file
    has to exist.
    """
    func: Callable
    func = open

    # Open file and check for gzip header
    gzip_magic = b"\037\213"
    with open(fpath, "rb") as fh:
        magic = fh.read(2)
        if magic == gzip_magic:
            func = gzip.open
    return func
