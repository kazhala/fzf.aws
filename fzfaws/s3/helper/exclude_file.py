"""Contains function to handle glob pattern and determine if file should be excluded."""
import fnmatch
from typing import List, Optional


def exclude_file(
    exclude: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    filename: str = "",
) -> bool:
    """Check if the file should be included during any operations.

    Process exclude list first than use include list to double check
    if the filename should be included.

    List should be glob pattern, trying to be in sync with aws cli.

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
