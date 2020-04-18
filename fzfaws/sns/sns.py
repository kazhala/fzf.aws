"""sns wrapper class

Wraps around boto3 client
"""
from fzfaws.utils.session import BaseSession
from fzfaws.utils.pyfzf import Pyfzf


class SNS(BaseSession):
    """sns wrapper class wraps around boto3 client

    Centralized class for better control on profile, region
    and much more.

    Attributes:
        region: region for the operation
        profile: profile to use for the operation
        client: initialized boto3 client with region and profile in use
        resource: initialized boto3 resource with region and profile in use
        arns: list of selected SNS arns
    """

    def __init__(self, profile=None, region=None):
        super().__init__(profile=profile, region=region, service_name='sns')
        self.arns = []

    def set_arns(self, arns=None, empty_allow=False, header=None):
        """set the sns arn for operation

        Args:
            arns: list, list of arns to init
            empty_allow: bool, allow empty selection
            header: string, header to display in fzf
        """
        if not arns:
            fzf = Pyfzf()
            paginator = self.client.get_paginator('list_topics')
            for result in paginator.paginate():
                fzf.process_list(result.get('Topics', []), 'TopicArn')
            self.arns = fzf.execute_fzf(
                empty_allow=empty_allow, multi_select=True, header=header)
