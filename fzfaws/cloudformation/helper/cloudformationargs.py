"""construct args for cloudformation

contains the class to configure extra settings of a cloudformation stack
"""
from fzfaws.utils.pyfzf import Pyfzf


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

    def set_extra_args(self, tagging=False, rollback=False, iam=False, stack_policy=False, creation_option=False, sns=False, update=False):
        """set extra arguments

        Used to determine what args to set and acts like a router

        Args:
            tagging: bool, set tagging for the stack
            rollback: bool, set rollback configuration for the stack
            iam: bool, use a specific iam role for this creation
            stack_policy: bool, add stack_policy to the stack
            creation_option: bool, configure creation_policy (termination protection, rollback on failure)
            sns: bool, set sns topic to publish
            update: bool, determine if is creating stack or updating stack
        """

        attributes = []
        if not tagging and not rollback and not iam and not stack_policy and not creation_option and not sns:
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
                tagging = True
            elif attribute == 'Permissions':
                iam = True
            elif attribute == 'StackPolicy':
                stack_policy = True
            elif attribute == 'Notifications':
                sns = True
            elif attribute == 'RollbackConfiguration':
                rollback = True
            elif attribute == 'CreationOption':
                creation_option = True

        if tagging:
            self.set_tags(update)

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
        tag_list = []
        if not update:
            print('Tags help you identify your sub resources')
            print('A "Name" tag is suggested to enter at the very least')
            print('Skip enter value to stop entering for tags')
        else:
            print('Enter new tags below')
            print('Skip enter value to stop entering for new tags')
        while True:
            tag_name = input('TagName: ')
            if not tag_name:
                break
            tag_value = input('TagValue: ')
            if not tag_value:
                break
            tag_list.append({'Key': tag_name, 'Value': tag_value})
        self._extra_args['Tags'] = tag_list
