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

    def set_arn(self, arn=None, header=None):
        fzf = Pyfzf()
        if not arn:
            paginator = self.client.get_paginator('list_roles')
            for result in paginator.paginate():
                fzf.process_list(result.get('Roles', []),
                                 'RoleName', 'Arn')
            arn = fzf.execute_fzf(empty_allow=True, print_col=4, header=header)
        self.arn = arn
