"""Contains the main function to validate a given template."""
import json
from typing import Optional, Union

from fzfaws.cloudformation import Cloudformation
from fzfaws.cloudformation.helper.file_validation import check_is_valid
from fzfaws.s3 import S3
from fzfaws.utils import Pyfzf


def validate_stack(
    profile: Optional[Union[str, bool]] = False,
    region: Optional[Union[str, bool]] = False,
    local_path: Union[str, bool] = False,
    root: bool = False,
    bucket: str = None,
    version: Union[str, bool] = False,
    no_print: bool = False,
) -> None:
    """Validate the selected cloudformation template using boto3 api.

    This is also used internally by create_stack and update_stack
    operations.

    :param profile: Use a different profile for this operation
    :type profile: Union[bool, str], optional
    :param region: Use a different region for this operation
    :type region: Union[bool, str], optional
    :param local_path: Select a template from local machine
    :type local_path: Union[bool, str], optional
    :param root: Search local file from root directory
    :type root: bool, optional
    :param bucket: specify a bucket/bucketpath to skip s3 selection
    :type bucket: str, optional
    :param version: use a previous version of the template
    :type version: Union[bool, str], optional
    :param no_print: Don't print the response, only check excpetion
    :type no_print: bool, optional
    """
    cloudformation = Cloudformation(profile, region)

    if local_path:
        if type(local_path) != str:
            fzf = Pyfzf()
            local_path = str(
                fzf.get_local_file(
                    search_from_root=root,
                    cloudformation=True,
                    header="select a cloudformation template to validate",
                )
            )
        check_is_valid(local_path)
        with open(local_path, "r") as file_body:
            response = cloudformation.client.validate_template(
                TemplateBody=file_body.read()
            )
    else:
        s3 = S3(profile, region)
        s3.set_bucket_and_path(bucket)
        if not s3.bucket_name:
            s3.set_s3_bucket(header="select a bucket which contains the template")
        if not s3.path_list[0]:
            s3.set_s3_object()

        check_is_valid(s3.path_list[0])

        if version == True:
            version = s3.get_object_version(s3.bucket_name, s3.path_list[0])[0].get(
                "VersionId", False
            )

        template_body_loacation = s3.get_object_url("" if not version else str(version))
        response = cloudformation.client.validate_template(
            TemplateURL=template_body_loacation
        )

    if not no_print:
        response.pop("ResponseMetadata", None)
        print(json.dumps(response, indent=4, default=str))
