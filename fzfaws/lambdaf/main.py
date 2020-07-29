"""Contains the entry point for all lambda operations."""
from fzfaws.lambdaf import Lambdaf
from typing import List, Any


def lambdaf(raw_args: List[Any]) -> None:
    """Parse arguments and direct traffic to lambda handler, internal use only.

    The raw_args are the processed args through cli.py main function.
    It also already contains the user default args so no need to process
    default args anymore.

    :param raw_args: list of args to be parsed
    :type raw_args: list
    """

    lambdaf = Lambdaf()
    lambdaf.set_lambdaf()
