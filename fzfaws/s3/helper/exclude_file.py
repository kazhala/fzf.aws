"""filter files based on exclude pattern and include pattern

using a list of pattern to filter files
"""
import fnmatch
from typing import Optional, List


def exclude_file(
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    filename=None,
) -> bool:
    """check filename is valid

    process exclude list first than use include to double check
    if the filename should be included

    list should be glob pattern, trying to be in sync with aws cli

    :param exclude: exclude glob pattern
    :type exclude: List[str], optional
    :param include: include glob pattern
    :type include: List[str], optional
    :return: bool value indicating whether the file should be excluded
    :rtype: bool
    """
    if not exclude:
        exclude = []
    if not include:
        include = []

    should_exclude = False
    # validate the relative_path against exclude list
    for pattern in exclude:
        if fnmatch.fnmatch(filename, pattern):
            should_exclude = True
    # validate against include list if it is previous denied
    if should_exclude:
        for pattern in include:
            if fnmatch.fnmatch(filename, pattern):
                should_exclude = False
    return should_exclude
