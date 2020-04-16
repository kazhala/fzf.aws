"""filter files based on exclude pattern and include pattern

using a list of pattern to filter files
"""
import fnmatch


def exclude_file(exclude=[], include=[], filename=None):
    """check filename is valid

    process exclude list first than use include to double check
    if the filename should be included

    list should be glob pattern, trying to be in sync with aws cli

    Args:
        exclude: list, list of exclude pattern
        include: list, list of include pattern
        filename: string, name of the file
    Returns:
        should_exclude: bool, indicating whether the file
        should be excluded
    """

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
