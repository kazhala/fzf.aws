"""contains the iam class

Wraps around boto3.client('iam') and handles profile
"""
from fzfaws.utils.session import BaseSession
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.spinner import Spinner


class IAM(BaseSession):
    """wraps around the boto3.client('iam')

    Handles all iam related operations here

    Attributes:
        client: object, boto3 client
        resource: object, boto3 resource
        arns: list, selected iam arns
    """

    def __init__(self, profile=None, region=None):
        super().__init__(profile=profile, region=region, service_name='iam')
        self.arns = []

    def set_arns(self, arn=None, header=None, empty_allow=True, service=None, multi_select=False):
        """set the role arn

        Args:
            arn: list, list of arn to set
            header: string, helper message to display in fzf header
            empty_allow: bool, allow empty selection
            service: string, only display role that could be assumed by this service
            multi_select: bool, allow multi selection
        """
        fzf = Pyfzf()
        spinner = Spinner(message='Fetching iam roles..')
        if not arn:
            try:
                spinner.start()
                paginator = self.client.get_paginator('list_roles')
                for result in paginator.paginate():
                    if service:
                        for role in result.get('Roles', []):
                            statements = role.get(
                                'AssumeRolePolicyDocument', {}).get('Statement', [])
                            for statement in statements:
                                if statement.get('Principal', {}).get('Service', '') == service:
                                    fzf.append_fzf('RoleName: %s  Arn: %s' % (
                                        role.get('RoleName', 'N/A'), role.get('Arn', 'N/A')))
                    else:
                        fzf.process_list(result.get('Roles', []),
                                         'RoleName', 'Arn')
            except:
                spinner.stop()
                spinner.join()
                raise
            spinner.stop()
            spinner.join()
            arns = fzf.execute_fzf(empty_allow=empty_allow,
                                   print_col=4, header=header, multi_select=multi_select)
            if not multi_select:
                arns = [arns]
        self.arns = arns
