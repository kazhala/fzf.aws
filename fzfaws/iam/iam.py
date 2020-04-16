"""contains the iam class

Wraps around boto3.client('iam') and handles profile
"""
from fzfaws.utils.session import BaseSession
from fzfaws.utils.pyfzf import Pyfzf


class IAM(BaseSession):
    """wraps around the boto3.client('iam')

    Handles all iam related operations here

    Attributes:
        client: object, boto3 client
        resource: object, boto3 resource
        arn: string, selected iam arn
    """

    def __init__(self, profile=None, region=None):
        super().__init__(profile=profile, region=region, service_name='iam')
        self.arn = None

    def set_arn(self, arn=None, header=None, empty_allow=True, service=None):
        """set the role arn

        Args:
            arn: string, the arn to set
            header: string, helper message to display in fzf header
            empty_allow: bool, allow empty selection
            service: string, only display role that could be assumed by this service
        """
        fzf = Pyfzf()
        if not arn:
            paginator = self.client.get_paginator('list_roles')
            for result in paginator.paginate():
                if service:
                    for role in result.get('Roles', []):
                        statements = role.get(
                            'AssumeRolePolicyDocument', {}).get('Statement', [])
                        for statement in statements:
                            if statement.get('Principal', {}).get('Service', '') == service:
                                print('yes')
                                fzf.append_fzf('RoleName: %s  Arn: %s' % (
                                    role.get('RoleName', 'N/A'), role.get('Arn', 'N/A')))
                else:
                    fzf.process_list(result.get('Roles', []),
                                     'RoleName', 'Arn')
            arn = fzf.execute_fzf(empty_allow=empty_allow,
                                  print_col=4, header=header)
        self.arn = arn
