"""cloudforation create stack operation

create cloudformation stack through both s3 bucket url or local file upload
"""
import json
from fzfaws.cloudformation.helper.file_validation import (
    is_yaml,
    is_json,
    check_is_valid,
)
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cloudformation.helper.process_file import (
    process_json_file,
    process_yaml_file,
)
from fzfaws.utils.exceptions import NoNameEntered
from fzfaws.cloudformation.cloudformation import Cloudformation
from fzfaws.cloudformation.helper.paramprocessor import ParamProcessor
from fzfaws.s3.s3 import S3
from fzfaws.cloudformation.helper.cloudformationargs import CloudformationArgs
from fzfaws.cloudformation.validate_stack import validate_stack


def create_stack(
    profile=False, region=False, local_path=False, root=False, wait=False, extra=False
):
    # type: (Union[bool, str], Union[bool, str], Union[bool, str], bool, bool, bool) -> None
    """handle the creation of the cloudformation stack

    :param profile: use a different profile for this operation
    :type profile: Union[bool, str], optional
    :param region: use a different region for this operation
    :type region: Union[bool, str], optional
    :param local_path: Select a template from local machine
    :type local_path: Union[bool, str], optional
    :param root: Search local file from root directory
    :type root: bool, optional
    :param wait: wait for stack to be completed before exiting the program
    :type wait: bool, optional
    :param extra: configure extra options for the stack, (tags, IAM, termination protection etc..)
    :type extra: bool, optional
    :raises NoNameEntered: when the new stack receive empty string as stack_name
    """

    cloudformation = Cloudformation(profile, region)

    # local flag specified
    if local_path:
        if type(local_path) != str:
            fzf = Pyfzf()
            local_path = fzf.get_local_file(search_from_root=root, cloudformation=True)

        # validate file type
        check_is_valid(local_path)

        validate_stack(
            cloudformation.profile,
            cloudformation.region,
            local_path=local_path,
            no_print=True,
        )

        stack_name = input("StackName: ")
        if not stack_name:
            raise NoNameEntered("No stack name entered")

        file_data = {}  # type: dict
        if is_yaml(local_path):
            file_data = process_yaml_file(local_path)
        elif is_json(local_path):
            file_data = process_json_file(local_path)

        # get params
        if "Parameters" in file_data["dictBody"]:
            paramprocessor = ParamProcessor(
                cloudformation.profile,
                cloudformation.region,
                file_data["dictBody"]["Parameters"],
            )
            paramprocessor.process_stack_params()
            create_parameters = paramprocessor.processed_params
        else:
            create_parameters = []

        cloudformation_args = {
            "cloudformation_action": cloudformation.client.create_stack,
            "StackName": stack_name,
            "TemplateBody": file_data["body"],
            "Parameters": create_parameters,
        }

    # if no local file flag, get from s3
    else:
        s3 = S3(cloudformation.profile, cloudformation.region)
        s3.set_s3_bucket()
        s3.set_s3_object()

        check_is_valid(s3.bucket_path)

        validate_stack(
            cloudformation.profile,
            cloudformation.region,
            bucket="%s/%s" % (s3.bucket_name, s3.bucket_path),
            no_print=True,
        )

        file_type = ""  # type: str
        if is_yaml(s3.bucket_path):
            file_type = "yaml"
        elif is_json(s3.bucket_path):
            file_type = "json"

        stack_name = input("StackName: ")
        if not stack_name:
            raise NoNameEntered("No stack name entered")

        file_data = s3.get_object_data(file_type)  # type: dict
        if "Parameters" in file_data:
            paramprocessor = ParamProcessor(
                cloudformation.profile, cloudformation.region, file_data["Parameters"]
            )
            paramprocessor.process_stack_params()
            create_parameters = paramprocessor.processed_params
        else:
            create_parameters = []

        template_body_loacation = s3.get_object_url()
        cloudformation_args = {
            "cloudformation_action": cloudformation.client.create_stack,
            "StackName": stack_name,
            "TemplateURL": template_body_loacation,
            "Parameters": create_parameters,
        }

    if extra:
        extra_args = CloudformationArgs(cloudformation)
        extra_args.set_extra_args(search_from_root=root)
        cloudformation_args.update(extra_args.extra_args)
    response = cloudformation.execute_with_capabilities(**cloudformation_args)

    response.pop("ResponseMetadata", None)
    print(json.dumps(response, indent=4, default=str))
    print(80 * "-")
    print("Stack creation initiated")

    if wait:
        cloudformation.stack_name = stack_name
        cloudformation.wait("stack_create_complete", "Waiting for stack to be ready..")
        print("Stack created")
