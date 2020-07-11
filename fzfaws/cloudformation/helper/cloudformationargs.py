"""Contains helper class to set extra arguments for cloudformation."""
from typing import Dict, List, Optional

from fzfaws.cloudformation import Cloudformation
from fzfaws.cloudwatch import Cloudwatch
from fzfaws.iam import IAM
from fzfaws.sns import SNS
from fzfaws.utils import Pyfzf


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
            fzf = Pyfzf()
            fzf.append_fzf("Tags\n")
            fzf.append_fzf("Permissions\n")
            if not dryrun:
                fzf.append_fzf("StackPolicy\n")
            fzf.append_fzf("Notifications\n")
            fzf.append_fzf("RollbackConfiguration\n")
            if not dryrun and not update:
                fzf.append_fzf("CreationOption\n")
            elif not dryrun and update:
                fzf.append_fzf("UpdateOption\n")
            attributes = list(
                fzf.execute_fzf(
                    empty_allow=True,
                    print_col=1,
                    multi_select=True,
                    header="Select options to configure",
                )
            )

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
            elif attribute == "CreationOption" or attribute == "UpdateOption":
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
            self._set_creation(update)

    def _set_creation(self, update: bool = False) -> None:
        """Set creation option for stack.

        :param update: show previous values if update is true
        :type update: bool, optional
        """
        print(80 * "-")
        fzf = Pyfzf()
        if not update:
            fzf.append_fzf("RollbackOnFailure\n")
            fzf.append_fzf("TimeoutInMinutes\n")
        fzf.append_fzf("EnableTerminationProtection\n")
        selected_options: List[str] = list(
            fzf.execute_fzf(
                empty_allow=True,
                print_col=1,
                multi_select=True,
                header="select options to configure",
            )
        )

        for option in selected_options:
            result: str = ""
            if option == "RollbackOnFailure":
                fzf.fzf_string = ""
                fzf.append_fzf("True\n")
                fzf.append_fzf("False\n")
                result = str(
                    fzf.execute_fzf(
                        empty_allow=True,
                        print_col=1,
                        header="Roll back on failue? (Default: True)",
                    )
                )
                if result:
                    self._extra_args["OnFailure"] = (
                        "ROLLBACK" if result == "True" else "DO_NOTHING"
                    )
            elif option == "TimeoutInMinutes":
                message = "Specify number of minutes before stack timeout (Default: no timeout): "
                if update and self.cloudformation.stack_details.get("TimeoutInMinutes"):
                    message = (
                        "Specify number of minutes before stack timeout (Original: %s)"
                        % self.cloudformation.stack_details["TimeoutInMinutes"]
                    )
                timeout = input(message)
                if timeout:
                    self._extra_args["TimeoutInMinutes"] = int(timeout)
            elif option == "EnableTerminationProtection":
                fzf.fzf_string = ""
                fzf.append_fzf("True\n")
                fzf.append_fzf("False\n")
                result = str(
                    fzf.execute_fzf(
                        empty_allow=True,
                        print_col=1,
                        header="%s" "Enable termination protection? (Default: False)"
                        if not update
                        else "Enable termination protection?",
                    )
                )
                if result and not update:
                    self._extra_args["EnableTerminationProtection"] = (
                        True if result == "True" else False
                    )
                elif result and update:
                    self.update_termination = True if result == "True" else False

    def _set_rollback(self, update: bool = False) -> None:
        """Set rollback configuration for cloudformation.
        
        :param update: show previous values if true
        :type update: bool, optional
        """
        print(80 * "-")

        cloudwatch = Cloudwatch(self.cloudformation.profile, self.cloudformation.region)
        header: str = "select a cloudwatch alarm to monitor the stack"
        message: str = "MonitoringTimeInMinutes(Default: 0): "
        if update and self.cloudformation.stack_details.get("RollbackConfiguration"):
            header += "\nOriginal value: %s" % self.cloudformation.stack_details[
                "RollbackConfiguration"
            ].get("RollbackTriggers")
            message = "MonitoringTimeInMinutes(Original: %s): " % self.cloudformation.stack_details[
                "RollbackConfiguration"
            ].get(
                "MonitoringTimeInMinutes"
            )
        cloudwatch.set_arns(empty_allow=True, header=header, multi_select=True)
        print("Selected arns: %s" % cloudwatch.arns)
        monitor_time = input(message)
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
        print(80 * "-")
        sns = SNS(
            profile=self.cloudformation.profile, region=self.cloudformation.region
        )
        header = "select sns topic to notify"
        if update:
            header += "\nOriginal value: %s" % self.cloudformation.stack_details.get(
                "NotificationARNs"
            )
        sns.set_arns(empty_allow=True, header=header, multi_select=True)
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
        print(80 * "-")
        fzf = Pyfzf()
        file_path: str = str(
            fzf.get_local_file(
                search_from_root=search_from_root,
                cloudformation=True,
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

    def _set_permissions(self, update: bool = False) -> None:
        """Set the iam user for the current stack.

        All operation permissions will be based on this
        iam role. Select None to stop using iam role
        and use current profile permissions.

        :param update: show previous values if true
        :type update: bool, optional
        """
        print(80 * "-")
        iam = IAM(profile=self.cloudformation.profile)
        if not update:
            header = (
                "Choose an IAM role to explicitly define CloudFormation's permissions\n"
            )
            header += "Note: only IAM role can be assumed by CloudFormation is listed"
            iam.set_arns(header=header, service="cloudformation.amazonaws.com")
        else:
            header = "Select a role Choose an IAM role to explicitly define CloudFormation's permissions\n"
            header += "Original value: %s" % self.cloudformation.stack_details.get(
                "RoleARN"
            )
            iam.set_arns(header=header, service="cloudformation.amazonaws.com")
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
        print(80 * "-")

        tag_list: List[Dict[str, str]] = []
        if update:
            if self.cloudformation.stack_details.get("Tags"):
                print("Update original tags")
                print("Skip the value to use previous value")
                print('Enter "deletetag" in any field to remove a tag')
                for tag in self.cloudformation.stack_details["Tags"]:
                    tag_key = input("Key(%s): " % tag["Key"])
                    if not tag_key:
                        tag_key = tag["Key"]
                    tag_value = input("Value(%s): " % tag["Value"])
                    if not tag_value:
                        tag_value = tag["Value"]
                    if tag_key == "deletetag" or tag_value == "deletetag":
                        continue
                    tag_list.append({"Key": tag_key, "Value": tag_value})
        print("Enter new tags below")
        print("Enter an empty value to stop entering for new tags")
        while True:
            tag_name: str = input("TagName: ")
            if not tag_name:
                break
            tag_value: str = input("TagValue: ")
            if not tag_value:
                break
            tag_list.append({"Key": tag_name, "Value": tag_value})
        if tag_list:
            self._extra_args["Tags"] = tag_list
        elif not tag_list and update:
            self._extra_args["Tags"] = []

    @property
    def extra_args(self):
        """Return the extra arguments."""
        return self._extra_args
