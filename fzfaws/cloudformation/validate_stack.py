"""contains the main function to validate a given template

search local files or s3 files and then use boto3 api to
validate the template syntax
"""
import json
from fzfaws.cloudformation.helper.file_validation import (
    is_yaml,
    is_json,
    check_is_valid,
)
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cloudformation.cloudformation import Cloudformation
from fzfaws.s3.s3 import S3
from fzfaws.utils.exceptions import UserError, InvalidFileType, NoSelectionMade


def validate_stack(
    profile=False, region=False, local_path=False, root=False, no_print=False
):
    # type: (Union[bool, str], Union[bool, str], Union[bool, str], bool) -> None
    """validate the selected cloudformation template using boto3 api

    :param profile: Use a different profile for this operation
    :type profile: Union[bool, str], optional
    :param region: Use a different region for this operation
    :type region: Union[bool, str], optional
    :param local: Select a template from local machine
    :type local_path: Union[bool, str], optional
    :param root: Search local file from root directory
    :type root: bool, optional
    :param no_print: Don't print the response, only check excpetion
    :type no_print: bool, optional
    :raises UserError: when input file type is wrong or when the user didn't select a selection in fzf
    """
    try:
        cloudformation = Cloudformation(profile, region)
        if local_path:
            if type(local_path) != str:
                fzf = Pyfzf()
                local_path = fzf.get_local_file(
                    search_from_root=root,
                    cloudformation=True,
                    header="select a cloudformation template to validate",
                )
            check_is_valid(local_path)
            with open(str(local_path), "r") as file_body:
                response = cloudformation.client.validate_template(
                    TemplateBody=file_body.read()
                )
            if not no_print:
                response.pop("ResponseMetadata", None)
                print(json.dumps(response, indent=4, default=str))
    except (InvalidFileType, NoSelectionMade) as e:
        raise UserError(e)
