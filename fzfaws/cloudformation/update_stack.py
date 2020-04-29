"""cloudformation update stack operations

perform updates to cloudformation
"""
import json
from fzfaws.cloudformation.helper.file_validation import (
    is_yaml,
    is_json,
    check_is_valid,
)
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cloudformation.helper.process_file import (
    process_yaml_file,
    process_json_file,
)
from fzfaws.cloudformation.cloudformation import Cloudformation
from fzfaws.cloudformation.helper.paramprocessor import ParamProcessor
from fzfaws.s3.s3 import S3
from fzfaws.cloudformation.helper.cloudformationargs import CloudformationArgs
from fzfaws.cloudformation.validate_stack import validate_stack


def update_stack(
    profile=False,
    region=False,
    replace=False,
    local_path=False,
    root=False,
    wait=False,
    extra=False,
    dryrun=False,
    cloudformation=None,
):
    # type: (Union[bool, str], Union[bool, str], bool, Union[bool, str], bool, bool, bool, bool, Cloudformation) -> Union[None, dict]
    """handle the update of cloudformation stacks

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

    # check to use current template or replace current template
    if not replace:
        print("Enter new parameter values, skip to use original value")
        updated_parameters = []
        if "Parameters" in cloudformation.stack_details:
            parameters = cloudformation.stack_details["Parameters"]

            # take new values
            for parameter in parameters:
                parameter_value = input(
                    f'{parameter["ParameterKey"]}({parameter["ParameterValue"]}): '
                )
                if parameter_value == '""' or parameter_value == "''":
                    updated_parameters.append(
                        {
                            "ParameterKey": parameter["ParameterKey"],
                            "ParameterValue": "",
                        }
                    )
                elif not parameter_value:
                    updated_parameters.append(
                        {
                            "ParameterKey": parameter["ParameterKey"],
                            "UsePreviousValue": True,
                        }
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

    else:
        # replace existing template
        # check if the new template should be from local
        if local_path:
            if type(local_path) != str:
                fzf = Pyfzf()
                local_path = fzf.get_local_file(
                    search_from_root=root, cloudformation=True
                )

            # double check file type, ensure yaml or json
            check_is_valid(local_path)

            validate_stack(
                cloudformation.profile,
                cloudformation.region,
                local_path=local_path,
                no_print=True,
            )

            file_data = {}  # type: dict
            if is_yaml(local_path):
                file_data = process_yaml_file(local_path)
            elif is_json(local_path):
                file_data = process_json_file(local_path)

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

        # if no local file flag, get from s3
        else:
            s3 = S3(profile=cloudformation.profile, region=cloudformation.region)
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

            file_data = s3.get_object_data(file_type)
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

            template_body_loacation = s3.get_object_url()

            cloudformation_args = {
                "cloudformation_action": cloudformation.client.update_stack,
                "StackName": cloudformation.stack_name,
                "TemplateURL": template_body_loacation,
                "UsePreviousTemplate": False,
                "Parameters": updated_parameters,
            }

    if extra:
        extra_args.set_extra_args(update=True, search_from_root=root, dryrun=dryrun)
        cloudformation_args.update(extra_args.extra_args)

    if dryrun:
        return cloudformation_args

    response = cloudformation.execute_with_capabilities(**cloudformation_args)

    # update termination protection if applicable
    if extra_args.update_termination:
        cloudformation.client.update_termination_protection(
            EnableTerminationProtection=True
            if extra_args.update_termination == "True"
            else False,
            StackName=cloudformation.stack_name,
        )

    response.pop("ResponseMetadata", None)
    print(json.dumps(response, indent=4, default=str))
    print(80 * "-")
    print("Stack update initiated")

    if wait:
        cloudformation.wait("stack_update_complete", "Wating for stack to be updated..")
        print("Stack updated")
