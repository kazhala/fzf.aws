"""Contains helper class to set extra arguments for cloudformation."""
from typing import Any, Dict, List, Optional

from PyInquirer import prompt

from fzfaws.cloudformation import Cloudformation
from fzfaws.cloudwatch import Cloudwatch
from fzfaws.iam import IAM
from fzfaws.sns import SNS
from fzfaws.utils import Pyfzf, URLQueryStringValidator, prompt_style


class CloudformationArgs:
    """Helper class to configure extra settings for cloudformation stacks.

    Handles tags, roll back, stack policy, notification, termination protection etc

    :param cloudformation: A instance of Cloudformation
    :type cloudformation: Cloudformation
    """

    def __init__(self, cloudformation: Cloudformation):
        """Construct the instance."""
        self.cloudformation: Cloudformation = cloudformation
        self._extra_args: dict = {}
        self.update_termination: Optional[bool] = None

    def set_extra_args(
        self,
        tags: bool = False,
        rollback: bool = False,
        permissions: bool = False,
        stack_policy: bool = False,
        creation_option: bool = False,
        notification: bool = False,
        update: bool = False,
        search_from_root: bool = False,
        dryrun: bool = False,
    ) -> None:
        """Set extra arguments.

        Used to determine what args to set and acts like a router

        :param tags: configure tags for the stack
        :type tags: bool, optional
        :param rollback: set rollback configuration for the stack
        :type rollback: bool, optional
        :param iam: use a specific iam role for this operation
        :type iam: bool, optional
        :param stack_policy: add stack_policy to the stack
        :type stack_policy: bool, optional
        :param creation_policy: configure creation_policy (termination protection, rollback on failure)
        :type creation_policy: bool, optional
        :param notification: set sns topic to publish
        :type notification: bool, optional
        :param update: determine if is creating stack or updating stack
        :type update: bool, optional
        :param search_from_root: search from root for stack_policy
        :type search_from_root: bool, optional
        :param dryrun: if true, changeset operation and don't add CreationOption or UpdateOption entry
        :type dryrun: bool, optional
        """
        attributes: List[str] = []

        if (
            not tags
            and not rollback
            and not permissions
            and not stack_policy
            and not creation_option
            and not notification
        ):
            choices: List[Dict[str, str]] = [
                {"name": "Tags"},
                {"name": "Permissions"},
                {"name": "Notifications"},
                {"name": "RollbackConfiguration"},
            ]
            if not dryrun:
                choices.append({"name": "StackPolicy"})
            if not dryrun and not update:
                choices.append({"name": "CreationOption"})
            questions: List[Dict[str, Any]] = [
                {
                    "type": "checkbox",
                    "name": "answer",
                    "message": "Select options to configure",
                    "choices": choices,
                }
            ]
            result = prompt(questions, style=prompt_style)
            if not result:
                raise KeyboardInterrupt
            attributes = result.get("answer", [])

        for attribute in attributes:
            if attribute == "Tags":
                tags = True
            elif attribute == "Permissions":
                permissions = True
            elif attribute == "StackPolicy":
                stack_policy = True
            elif attribute == "Notifications":
                notification = True
            elif attribute == "RollbackConfiguration":
                rollback = True
            elif attribute == "CreationOption":
                creation_option = True

        if tags:
            self._set_tags(update)
        if permissions:
            self._set_permissions(update)
        if stack_policy:
            self._set_policy(update, search_from_root)
        if notification:
            self._set_notification(update)
        if rollback:
            self._set_rollback(update)
        if creation_option:
            self._set_creation()

    def _set_creation(self) -> None:
        """Set creation option for stack."""
        questions: List[Dict[str, Any]] = [
            {
                "type": "checkbox",
                "name": "selected_options",
                "message": "Select creation options to configure",
                "choices": [
                    {"name": "RollbackOnFailure"},
                    {"name": "TimeoutInMinutes"},
                    {"name": "EnableTerminationProtection"},
                ],
            },
            {
                "type": "rawlist",
                "name": "rollback",
                "message": "Roll back on failure?",
                "choices": ["True", "False"],
                "when": lambda x: "RollbackOnFailure" in x["selected_options"],
            },
            {
                "type": "input",
                "name": "timeout",
                "message": "Specify number of minutes before timeout",
                "when": lambda x: "TimeoutInMinutes" in x["selected_options"],
            },
            {
                "type": "rawlist",
                "name": "termination",
                "message": "Enable termination protection?",
                "choices": ["True", "False"],
                "when": lambda x: "EnableTerminationProtection"
                in x["selected_options"],
            },
        ]
        result = prompt(questions, style=prompt_style)
        if not result:
            raise KeyboardInterrupt
        if result.get("rollback"):
            self._extra_args["OnFailure"] = (
                "ROLLBACK" if result["rollback"] == "True" else "DO_NOTHING"
            )
        if result.get("timeout"):
            self._extra_args["TimeoutInMinutes"] = int(result["timeout"])
        if result.get("termination"):
            self._extra_args["EnableTerminationProtection"] = (
                True if result["termination"] == "True" else False
            )

    def _set_rollback(self, update: bool = False) -> None:
        """Set rollback configuration for cloudformation.
        
        :param update: show previous values if true
        :type update: bool, optional
        """
        cloudwatch = Cloudwatch(self.cloudformation.profile, self.cloudformation.region)
        header: str = "select a cloudwatch alarm to monitor the stack"
        questions: List[Dict[str, str]] = [
            {"type": "input", "message": "MonitoringTimeInMinutes", "name": "answer"}
        ]
        if update and self.cloudformation.stack_details.get("RollbackConfiguration"):
            header += "\nOriginal value: %s" % self.cloudformation.stack_details[
                "RollbackConfiguration"
            ].get("RollbackTriggers")
            questions[0]["default"] = str(
                self.cloudformation.stack_details["RollbackConfiguration"].get(
                    "MonitoringTimeInMinutes", ""
                )
            )
        cloudwatch.set_arns(empty_allow=True, header=header, multi_select=True)
        print("Selected alarm: %s" % cloudwatch.arns)
        result = prompt(questions, style=prompt_style)
        if not result:
            raise KeyboardInterrupt
        monitor_time = result.get("answer")
        if cloudwatch.arns:
            self._extra_args["RollbackConfiguration"] = {
                "RollbackTriggers": [
                    {"Arn": arn, "Type": "AWS::CloudWatch::Alarm"}
                    for arn in cloudwatch.arns
                ],
                "MonitoringTimeInMinutes": int(monitor_time) if monitor_time else 0,
            }

    def _set_notification(self, update: bool = False) -> None:
        """Set sns arn for notification.

        :param update: show previous values if true
        :type update: bool, optional
        """
        sns = SNS(
            profile=self.cloudformation.profile, region=self.cloudformation.region
        )
        header = "select sns topic to notify"
        if update:
            header += "\nOriginal value: %s" % self.cloudformation.stack_details.get(
                "NotificationARNs"
            )
        sns.set_arns(empty_allow=True, header=header, multi_select=True)
        print("Selected notification: %s" % sns.arns)
        if sns.arns:
            self._extra_args["NotificationARNs"] = sns.arns

    def _set_policy(self, update: bool = False, search_from_root: bool = False) -> None:
        """Set the stack_policy for the stack.

        Used to prevent update on certain resources.

        :param update: determine if stack is updating, if true, set different args
            aws cloudformation takes StackPolicyBody for creation and StackPolicyDuringUpdateBody for update overwrite
        :type update: bool, optional
        :param search_from_root: search files from root
        :type search_from_root: bool, optional
        """
        fzf = Pyfzf()
        file_path: str = str(
            fzf.get_local_file(
                search_from_root=search_from_root,
                json=True,
                empty_allow=True,
                header="select the policy document you would like to use",
            )
        )
        if not update and file_path:
            with open(str(file_path), "r") as body:
                body = body.read()
                self._extra_args["StackPolicyBody"] = body
        elif update and file_path:
            with open(str(file_path), "r") as body:
                body = body.read()
                self._extra_args["StackPolicyDuringUpdateBody"] = body
        print("Selected policy: %s" % file_path)

    def _set_permissions(self, update: bool = False) -> None:
        """Set the iam user for the current stack.

        All operation permissions will be based on this
        iam role. Select None to stop using iam role
        and use current profile permissions.

        :param update: show previous values if true
        :type update: bool, optional
        """
        iam = IAM(profile=self.cloudformation.profile)
        if not update:
            header = (
                "choose an IAM role to explicitly define CloudFormation's permissions\n"
            )
            header += "Note: only IAM role can be assumed by CloudFormation is listed"
            iam.set_arns(header=header, service="cloudformation.amazonaws.com")
        else:
            header = "select a role Choose an IAM role to explicitly define CloudFormation's permissions\n"
            header += "Original value: %s" % self.cloudformation.stack_details.get(
                "RoleARN"
            )
            iam.set_arns(header=header, service="cloudformation.amazonaws.com")
        print("Selected role: %s" % iam.arns[0])
        if iam.arns:
            self._extra_args["RoleARN"] = iam.arns[0]

    def _set_tags(self, update: bool = False) -> None:
        """Set tags for the current stack.

        Tags are in the format of [
            {
                'Key': value,
                'Value': value
            }
        ]

        :param update: determine if is updating the stack, it will show different prompt
        :type update: bool, optional
        """
        print("Tag format should be a URL Query alike string (e.g. foo=boo&name=yes)")

        questions: List[Dict[str, Any]] = [
            {
                "type": "input",
                "message": "Tags",
                "name": "answer",
                "validate": URLQueryStringValidator,
            }
        ]
        if update and self.cloudformation.stack_details.get("Tags"):
            default_tag_value: List[str] = []
            for tag in self.cloudformation.stack_details.get("Tags", []):
                default_tag_value.append(
                    "%s=%s" % (tag.get("Key", ""), tag.get("Value", ""))
                )
            questions[0]["default"] = "&".join(default_tag_value)
        result = prompt(questions, style=prompt_style)
        if not result:
            raise KeyboardInterrupt
        tag_list: List[Dict[str, str]] = []
        for tag in result.get("answer", "").split("&"):
            if tag != "":
                tag_name, tag_value = tag.split("=")
                tag_list.append({"Key": tag_name, "Value": tag_value})
        self._extra_args["Tags"] = tag_list

    @property
    def extra_args(self):
        """Return the extra arguments."""
        return self._extra_args
