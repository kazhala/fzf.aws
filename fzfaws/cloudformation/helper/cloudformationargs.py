"""construct args for cloudformation

contains the class to configure extra settings of a cloudformation stack
"""
import subprocess
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.iam.iam import IAM
from fzfaws.sns.sns import SNS
from fzfaws.cloudwatch.cloudwatch import Cloudwatch
from fzfaws.utils.exceptions import NoSelectionMade
from fzfaws.utils.util import get_confirmation


class CloudformationArgs:
    """helper class to configure extra settings for cloudformation stacks

    Handles tags, roll back, stack policy, notification, termination protection etc

    Attributes:
        cloudfomation: Cloudformation class instance
        _extra_args: extra argument
    """

    def __init__(self, cloudfomation):
        """constructior

        Args:
            cloudfomation: Cloudformation class instance
        """
        self.cloudfomation = cloudfomation
        self._extra_args = {}

    def set_extra_args(self, tags=False, rollback=False, permissions=False, stack_policy=False, creation_option=False, notification=False, update=False, search_from_root=False):
        """set extra arguments

        Used to determine what args to set and acts like a router

        Args:
            tags: bool, set tags for the stack
            rollback: bool, set rollback configuration for the stack
            iam: bool, use a specific iam role for this creation
            stack_policy: bool, add stack_policy to the stack
            creation_option: bool, configure creation_policy (termination protection, rollback on failure)
            notification: bool, set sns topic to publish
            update: bool, determine if is creating stack or updating stack
            search_from_root: bool, search from root for stack_policy
        """

        attributes = []
        if not tags and not rollback and not permissions and not stack_policy and not creation_option and not notification:
            fzf = Pyfzf()
            fzf.append_fzf('Tags\n')
            fzf.append_fzf('Permissions\n')
            fzf.append_fzf('StackPolicy\n')
            fzf.append_fzf('Notifications\n')
            fzf.append_fzf('RollbackConfiguration\n')
            fzf.append_fzf('CreationOption\n')
            attributes = fzf.execute_fzf(
                empty_allow=True, print_col=1, multi_select=True, header='Select options to configure')

        for attribute in attributes:
            if attribute == 'Tags':
                tags = True
            elif attribute == 'Permissions':
                permissions = True
            elif attribute == 'StackPolicy':
                stack_policy = True
            elif attribute == 'Notifications':
                notification = True
            elif attribute == 'RollbackConfiguration':
                rollback = True
            elif attribute == 'CreationOption':
                creation_option = True

        if tags:
            self.set_tags(update)
        if permissions:
            self.set_permissions(update)
        if stack_policy:
            self.set_policy(update, search_from_root)
        if notification:
            self.set_notification(update)
        if rollback:
            self.set_rollback(update)
        if creation_option:
            self.set_creation(update)

    def set_creation(self, update=False):
        """set creation option for stack

        Args:
            update: bool, show previous values
        """
        print(80*'-')
        rollback = input('Rollback on failure (default: y)?(y/n): ')
        if rollback.lower() != 'y' and rollback.lower() != 'n':
            self._extra_args['OnFailure'] = 'ROLLBACK'
        elif rollback.lower() == 'y':
            self._extra_args['OnFailure'] = 'ROLLBACK'
        elif rollback.lower() == 'n':
            self._extra_args['OnFailure'] = 'DO_NOTHING'
        timeout = input(
            'Specify number of minutes before stack timeout (default no timeout): ')
        if timeout:
            self._extra_args['TimeoutInMinutes'] = int(timeout)
        termination = input(
            'Prevents stack from accidentally deleted (default: n)?(y/n): ')
        if termination.lower() != 'y' and termination.lower() != 'n':
            self._extra_args['EnableTerminationProtection'] = False
        elif termination.lower() == 'y':
            self._extra_args['EnableTerminationProtection'] = True
        elif termination.lower() == 'n':
            self._extra_args['EnableTerminationProtection'] = False

    def set_rollback(self, update=False):
        """set rollback configuration for cloudformation

        Args:
            update: bool, show previous values
        """
        print(80*'-')
        cloudwatch = Cloudwatch(
            self.cloudfomation.profile, self.cloudfomation.region)
        cloudwatch.set_arns(
            empty_allow=True, header='select a cloudwatch alarm to monitor the stack', multi_select=True)
        print('Selected arns: %s' % cloudwatch.arns)
        monitor_time = input('MonitoringTimeInMinutes(Default: 0): ')
        if cloudwatch.arns:
            self._extra_args['RollbackConfiguration'] = {
                'RollbackTriggers': [{'Arn': arn, 'Type': 'AWS::CloudWatch::Alarm'} for arn in cloudwatch.arns],
                'MonitoringTimeInMinutes': monitor_time if monitor_time else 0
            }

    def set_notification(self, update=False):
        """set sns arn for notification

        Args:
            update: bool, show previous values
        """
        print(80*'-')
        sns = SNS(profile=self.cloudfomation.profile,
                  region=self.cloudfomation.region)
        sns.set_arns(empty_allow=True, header='select a sns topic to notify')
        if sns.arns:
            self._extra_args['NotificationARNs'] = sns.arns

    def set_policy(self, update=False, search_from_root=False):
        """set the stack_policy for the stack

        Used to prevent update on certain resources

        Args:
            update: bool, if during stack update
            search_from_root: bool, search files from root
        """
        print(80*'-')
        fzf = Pyfzf()
        file_path = fzf.get_local_file(search_from_root=search_from_root, cloudformation=True,
                                       empty_allow=True, header='select the policy document you would like to use')
        if not update and file_path:
            with open(file_path, 'r') as body:
                body = body.read()
                self._extra_args['StackPolicyBody'] = body
        elif update and file_path:
            with open(file_path, 'r') as body:
                body = body.read()
                self._extra_args['StackPolicyDuringUpdateBody'] = body

    def set_permissions(self, update=False):
        """set the iam user for the current stack

        All operation permissions will be based on this
        iam role. Select None to stop using iam role
        and use current profile permissions

        Args:
            update: bool, show previous values
        """
        print(80*'-')
        iam = IAM(profile=self.cloudfomation.profile)
        if not update:
            header = 'Choose an IAM role to explicitly define CloudFormation\'s permissions\n'
            header += 'Note: only IAM role can be assumed by CloudFormation is listed'
            iam.set_arn(
                header=header, service='cloudformation.amazonaws.com')
        else:
            header = 'Select a role Choose an IAM role to explicitly define CloudFormation\'s permissions\n'
            header += 'Original value: %s' % self.cloudfomation.stack_details.get(
                'RoleARN', 'N/A')
            iam.set_arn(header=header, service='cloudformation.amazonaws.com')
        if iam.arn:
            self._extra_args['RoleARN'] = iam.arn

    def set_tags(self, update=False):
        """set tags for the current stack

        Tags are in the format of [
            {
                'Key': value,
                'Value': value
            }
        ]

        Args:
            update: bool, determine if is updating the stack
        """
        print(80*'-')
        tag_list = []
        if update:
            print('Skip the value to use previous value')
            print('Enter "deletetag" in any field to remove a tag')
            for tag in self.cloudfomation.stack_details['Tags']:
                tag_key = input(f"Key({tag['Key']}): ")
                if not tag_key:
                    tag_key = tag['Key']
                tag_value = input(f"Value({tag['Value']}): ")
                if not tag_value:
                    tag_value = tag['Value']
                if tag_key == 'deletetag' or tag_value == 'deletetag':
                    continue
                tag_list.append(
                    {'Key': tag_key, 'Value': tag_value})
            print('Enter new tags below')
            print('Skip enter value to stop entering for new tags')
        elif not update:
            print('Tags help you identify your sub resources')
            print('A "Name" tag is suggested to enter at the very least')
            print('Skip enter value to stop entering for tags')
        while True:
            tag_name = input('TagName: ')
            if not tag_name:
                break
            tag_value = input('TagValue: ')
            if not tag_value:
                break
            tag_list.append({'Key': tag_name, 'Value': tag_value})
        if tag_list:
            self._extra_args['Tags'] = tag_list
        elif not tag_list and update:
            self._extra_args['Tags'] = []

    @property
    def extra_args(self):
        return self._extra_args
