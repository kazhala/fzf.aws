"""Custom exceptions"""


class NoCommandFound(Exception):
    """Exception to raise when there is no action command found in sys.argv[1]"""
    pass


class NoSelectionMade(Exception):
    """Exception to raise when there is no selection made through fzf"""
    pass


class NoNameEntered(Exception):
    """When there is no name specified"""
    pass