"""Contains the function to create cloudformation stack."""
import json
from typing import Any, Dict, Optional, Union

from fzfaws.cloudformation import Cloudformation
from fzfaws.cloudformation.helper.cloudformationargs import CloudformationArgs
from fzfaws.cloudformation.helper.file_validation import (
    check_is_valid,
    is_json,
    is_yaml,
)
from fzfaws.cloudformation.helper.paramprocessor import ParamProcessor
from fzfaws.cloudformation.validate_stack import validate_stack
from fzfaws.s3 import S3
from fzfaws.utils import FileLoader, Pyfzf
from fzfaws.utils.exceptions import NoNameEntered


def create_stack(
    profile: Union[str, bool] = False,
    region: Union[str, bool] = False,
    local_path: Union[str, bool] = False,
    root: bool = False,
    wait: bool = False,
    extra: bool = False,
    bucket: str = None,
    version: Union[str, bool] = False,
) -> None:
    """Handle the creation of the cloudformation stack.

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
    :param bucket: specify a bucket/bucketpath to skip s3 selection
    :type bucket: str, optional
    :param version: use a previous version of the template
    :type version: Union[bool, str], optional
    :raises NoNameEntered: when the new stack receive empty string as stack_name
    """
    cloudformation = Cloudformation(profile, region)

    if local_path:
        if type(local_path) != str:
            fzf = Pyfzf()
            local_path = str(
                fzf.get_local_file(search_from_root=root, cloudformation=True)
            )
        cloudformation_args = construct_local_creation_args(
            cloudformation, str(local_path)
        )
    else:
        cloudformation_args = construct_s3_creation_args(
            cloudformation, bucket, version
        )

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
        cloudformation.stack_name = cloudformation_args["StackName"]
        cloudformation.wait(
            "stack_create_complete", "Waiting for stack to be ready ..."
        )
        print("Stack created")


def construct_local_creation_args(
    cloudformation: Cloudformation, local_path: str
) -> Dict[str, Any]:
    """Construct cloudformation create argument for local file.

    Perform fzf search on local files json/yaml and then use validate_stack to
    validate stack through boto3 API before constructing the argument.

    :param cloudformation: Cloudformation instance
    :type cloudformation: Cloudformation
    :param local_path: local file path
    :type local_path: str
    :return: return the constructed args thats ready for use with boto3
    :rtype: Dict[str, Any]
    """
    # validate file type, has to be either yaml or json
    check_is_valid(local_path)

    validate_stack(
        cloudformation.profile,
        cloudformation.region,
        local_path=local_path,
        no_print=True,
    )

    stack_name: str = input("StackName: ")
    if not stack_name:
        raise NoNameEntered("No stack name entered")

    fileloader = FileLoader(path=local_path)
    file_data: Dict[str, Any] = {}
    if is_yaml(local_path):
        file_data = fileloader.process_yaml_file()
    elif is_json(local_path):
        file_data = fileloader.process_json_file()

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

    return cloudformation_args


def construct_s3_creation_args(
    cloudformation: Cloudformation, bucket: Optional[str], version: Union[str, bool]
) -> Dict[str, Any]:
    """Construct cloudformation argument for template in s3.

    Retrieve the template from s3 bucket and validate and process the content in it
    then return the ready to use cloudformation argument for boto3.

    :param cloudformation: Cloudformation instance
    :type cloudformation: Cloudformation
    :param bucket: bucket name
    :type bucket: 
    :return: return the formated cloudformation argument thats ready to use by boto3
    :rtype: Dict[str, Any]
    """
    s3 = S3(cloudformation.profile, cloudformation.region)
    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket(header="select a bucket which contains the template")
    if not s3.path_list[0]:
        s3.set_s3_object()

    # check file type is yaml or json
    check_is_valid(s3.path_list[0])

    # if version is requested but not set through cmd line, get user to select a version
    if version == True:
        version = s3.get_object_version(s3.bucket_name, s3.path_list[0])[0].get(
            "VersionId", False
        )

    # validate the template through boto3
    validate_stack(
        cloudformation.profile,
        cloudformation.region,
        bucket="%s/%s" % (s3.bucket_name, s3.path_list[0]),
        version=version if version else False,
        no_print=True,
    )

    file_type: str = ""
    if is_yaml(s3.path_list[0]):
        file_type = "yaml"
    elif is_json(s3.path_list[0]):
        file_type = "json"

    stack_name: str = input("StackName: ")
    if not stack_name:
        raise NoNameEntered("No stack name entered")

    file_data: dict = s3.get_object_data(file_type)
    if "Parameters" in file_data:
        paramprocessor = ParamProcessor(
            cloudformation.profile, cloudformation.region, file_data["Parameters"]
        )
        paramprocessor.process_stack_params()
        create_parameters = paramprocessor.processed_params
    else:
        create_parameters = []

    template_body_loacation: str = s3.get_object_url(
        version="" if not version else str(version)
    )
    cloudformation_args = {
        "cloudformation_action": cloudformation.client.create_stack,
        "StackName": stack_name,
        "TemplateURL": template_body_loacation,
        "Parameters": create_parameters,
    }

    return cloudformation_args
