"""This module contails related validation classes for PyInquirer."""
import re

from PyInquirer import ValidationError, Validator


class URLQueryStringValidator(Validator):
    """Validate Query strying for PyInquirer input."""

    def validate(self, document):
        """Validate user input."""
        match = re.match(r"^([A-Za-z0-9-]+?=[A-Za-z0-9-]+(&|$))*$", document.text)
        if not match:
            raise ValidationError(
                message="Format should be a URL Query alike string (e.g. Content-Type=hello&Cache-Control=world)",
                cursor_position=len(document.text),
            )


class CommaListValidator(Validator):
    """Validate comma seperated list for PyInquirer input."""

    def validate(self, document):
        """Validate user input."""
        match = re.match(
            r"^((id|emailAddress|uri)=[A-Za-z@.\/:-]+?(,|$))+", document.text
        )
        if not match:
            raise ValidationError(
                message="Format should be a comma seperated list (e.g. id=XXX,emailAddress=XXX@gmail.com,uri=http://acs.amazonaws.com/groups/global/AllUsers)",
                cursor_position=len(document.text),
            )


class StackNameValidator(Validator):
    """Validate cloudformation stack name input."""

    def validate(self, document):
        """Validate user input."""
        if not document.text:
            raise ValidationError(
                message="StackName is required", cursor_position=len(document.text)
            )
        match = re.match(r"^[a-zA-Z0-9-]+$", document.text)
        if not match:
            raise ValidationError(
                message="Cloudformation StackName can only contain alphanumeric characters and hyphens",
                cursor_position=len(document.text),
            )
