"""Contains cloudformation update stack operation handler."""
import json
from typing import Any, Dict, List, Optional, Union

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
from fzfaws.utils import Pyfzf, FileLoader


def update_stack(
    profile: Optional[Union[str, bool]] = False,
    region: Optional[Union[str, bool]] = False,
    replace: bool = False,
    local_path: Union[str, bool] = False,
    root: bool = False,
    wait: bool = False,
    extra: bool = False,
    bucket: str = None,
    version: Union[str, bool] = False,
    dryrun: bool = False,
    cloudformation: Optional[Cloudformation] = None,
) -> Union[None, dict]:
    """Handle the update of cloudformation stacks.

    This is also used by changeset_stack to create its argument.
    The dryrun and cloudformation argument in the function is only
    used by changeset_stack.

    :param profile: use a different profile for this operation
    :type profile: Union[bool, str], optional
    :param region: use a different region for this operation
    :type region: Union[bool, str], optional
    :param replace: replace the template during update
    :type replace: bool, optional
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
    :param version: use a previous version of the template on s3 bucket
    :type version: Union[str, bool], optional
    :param dryrun: don't update, rather return update information, used for changeset_stack()
    :type dryrun: bool, optional
    :param cloudformation: a cloudformation instance, when calling from changeset_stack(), pass cloudformation in
    :type cloudformation: Cloudformation, optional
    :return: If dryrun is set, return all the update details as dict {'Parameters': value, 'Tags': value...}
    :rtype: Union[None, dict]
    """
    if not cloudformation:
        cloudformation = Cloudformation(profile, region)
        cloudformation.set_stack()

    extra_args = CloudformationArgs(cloudformation)

    if not replace:
        # non replacing update, just update the parameter
        cloudformation_args = non_replacing_update(cloudformation)

    else:
        # replace existing template
        if local_path:
            # template provided in local machine
            if type(local_path) != str:
                fzf = Pyfzf()
                local_path = str(
                    fzf.get_local_file(search_from_root=root, cloudformation=True)
                )
            cloudformation_args = local_replacing_update(
                cloudformation, str(local_path)
            )

        else:
            # template provided in s3
            cloudformation_args = s3_replacing_update(cloudformation, bucket, version)

    if extra:
        extra_args.set_extra_args(update=True, search_from_root=root, dryrun=dryrun)
        cloudformation_args.update(extra_args.extra_args)

    if dryrun:
        return cloudformation_args

    response = cloudformation.execute_with_capabilities(**cloudformation_args)

    # update termination protection if applicable
    if extra_args.update_termination is not None:
        cloudformation.client.update_termination_protection(
            EnableTerminationProtection=extra_args.update_termination,
            StackName=cloudformation.stack_name,
        )

    response.pop("ResponseMetadata", None)
    print(json.dumps(response, indent=4, default=str))
    print(80 * "-")
    print("Stack update initiated")

    if wait:
        cloudformation.wait(
            "stack_update_complete", "Wating for stack to be updated ..."
        )
        print("Stack updated")


def non_replacing_update(cloudformation: Cloudformation) -> Dict[str, Any]:
    """Format the required argument for a non-replacing update for boto3.

    Non-replacing update as in not replacing the template, only
    updating the parameters.

    :param cloudformation: Cloudformation instance
    :type cloudformation: Cloudformation
    :return: formatted argument that's ready to be used by boto3
    :rtype: Dict[str, Any]
    """
    print("Enter new parameter values, skip to use original value")
    updated_parameters: List[Dict[str, Any]] = []
    parameters = cloudformation.stack_details.get("Parameters", [])

    for parameter in parameters:
        parameter_value = input(
            "%s(%s): " % (parameter["ParameterKey"], parameter["ParameterValue"])
        )
        if parameter_value == '""' or parameter_value == "''":
            updated_parameters.append(
                {"ParameterKey": parameter["ParameterKey"], "ParameterValue": "",}
            )
        elif not parameter_value:
            updated_parameters.append(
                {"ParameterKey": parameter["ParameterKey"], "UsePreviousValue": True,}
            )
        else:
            updated_parameters.append(
                {
                    "ParameterKey": parameter["ParameterKey"],
                    "ParameterValue": parameter_value,
                }
            )

    cloudformation_args = {
        "cloudformation_action": cloudformation.client.update_stack,
        "StackName": cloudformation.stack_name,
        "UsePreviousTemplate": True,
        "Parameters": updated_parameters,
    }

    return cloudformation_args


def local_replacing_update(
    cloudformation: Cloudformation, local_path: str
) -> Dict[str, Any]:
    """Format cloudformation argument for a local replacing update.

    Local replacing update as in using a template in the local machine
    to perform stack update.

    Process the new template and also comparing with previous parameter
    value to provide an old value preview.

    :param cloudformation: Cloudformation instance
    :type cloudformation: Cloudformation
    :param local_path: local file path to the template
    :type local_path: str
    :return: formatted argument thats ready to be used by boto3
    :rtype: Dict[str, Any]
    """
    check_is_valid(local_path)

    validate_stack(
        cloudformation.profile,
        cloudformation.region,
        local_path=local_path,
        no_print=True,
    )

    fileloader = FileLoader(path=local_path)
    file_data: Dict[str, Any] = {}
    if is_yaml(local_path):
        file_data = fileloader.process_yaml_file()
    elif is_json(local_path):
        file_data = fileloader.process_json_file()

    # process params
    if "Parameters" in file_data["dictBody"]:
        paramprocessor = ParamProcessor(
            cloudformation.profile,
            cloudformation.region,
            file_data["dictBody"]["Parameters"],
            cloudformation.stack_details.get("Parameters"),
        )
        paramprocessor.process_stack_params()
        updated_parameters = paramprocessor.processed_params
    else:
        updated_parameters = []

    cloudformation_args = {
        "cloudformation_action": cloudformation.client.update_stack,
        "StackName": cloudformation.stack_name,
        "TemplateBody": file_data["body"],
        "UsePreviousTemplate": False,
        "Parameters": updated_parameters,
    }

    return cloudformation_args


def s3_replacing_update(
    cloudformation: Cloudformation, bucket: Optional[str], version: Union[str, bool]
) -> Dict[str, Any]:
    """Format argument for a replacing updating through providing template on s3.

    Read the template from s3, comparing parameter names with the original stack
    to provide a preview of value if possible.

    :param cloudformation: Cloudformation instance
    :type cloudformation: Cloudformation
    :param bucket: bucket path, if set, skip fzf selection
    :type bucket: str, optional
    :param version: whether to use a versioned template in s3
    :type version: Union[str, bool]
    :return: formatted argument thats ready to be used by boto3
    :rtype: Dict[str, Any]
    """
    s3 = S3(profile=cloudformation.profile, region=cloudformation.region)
    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket()
    if not s3.path_list[0]:
        s3.set_s3_object()

    check_is_valid(s3.path_list[0])

    if version == True:
        version = s3.get_object_version(s3.bucket_name, s3.path_list[0])[0].get(
            "VersionId", False
        )

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

    file_data: Dict[str, Any] = s3.get_object_data(file_type)
    if "Parameters" in file_data:
        paramprocessor = ParamProcessor(
            cloudformation.profile,
            cloudformation.region,
            file_data["Parameters"],
            cloudformation.stack_details.get("Parameters"),
        )
        paramprocessor.process_stack_params()
        updated_parameters = paramprocessor.processed_params
    else:
        updated_parameters = []

    template_body_loacation = s3.get_object_url("" if not version else str(version))

    cloudformation_args = {
        "cloudformation_action": cloudformation.client.update_stack,
        "StackName": cloudformation.stack_name,
        "TemplateURL": template_body_loacation,
        "UsePreviousTemplate": False,
        "Parameters": updated_parameters,
    }

    return cloudformation_args
