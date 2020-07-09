"""Custom exceptions."""


class NoNameEntered(Exception):
    """When there is no name specified."""

    pass


class InvalidS3PathPattern(Exception):
    """The input s3 path set by -p is invalid format."""

    pass


class InvalidFileType(Exception):
    """The file type is not accepted file type."""

    pass


class InvalidParameterType(Exception):
    """When the input parameter in not correct type."""

    pass


class EmptyList(Exception):
    """The input list to fzf process list is empty."""

    pass


class NoSelectionMade(Exception):
    """Exception to raise when there is no selection made through fzf."""

    pass


class EC2Error(Exception):
    """Generic exception when the error is caused by during EC2 operation."""

    pass
