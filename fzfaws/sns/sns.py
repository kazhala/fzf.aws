"""sns wrapper class

Wraps around boto3 client
"""
from fzfaws.utils import Pyfzf, BaseSession
from typing import Union, Optional


class SNS(BaseSession):
    """sns wrapper class wraps around boto3 client

    Centralized class for better control on profile, region
    and much more.

    :param profile: profile to use for this operation
    :type profile: Union[str, bool], optional
    :param region: region to use for this operation
    :type region: Union[str, bool], optional
    """

    def __init__(
        self,
        profile: Optional[Union[str, bool]] = None,
        region: Optional[Union[str, bool]] = None,
    ) -> None:
        super().__init__(profile=profile, region=region, service_name="sns")
        self.arns: list = [""]

    def set_arns(
        self,
        arns: Optional[Union[str, list]] = None,
        empty_allow: bool = False,
        header: Optional[str] = None,
        multi_select: bool = False,
    ) -> None:
        """set the sns arn for operation

        :param arns: arns to init
        :type arns: Union[list, str], optional
        :param empty_allow: allow empty fzf selection
        :type empty_allow: bool, optional
        :param header: header in fzf
        :type header: str, optional
        :param multi_select: allow multi selection in fzf
        :type multi_select: bool, optional
        """
        if not arns:
            fzf = Pyfzf()
            for result in self.get_paginated_result("list_topics"):
                fzf.process_list(result.get("Topics", []), "TopicArn")
            arns = fzf.execute_fzf(
                empty_allow=empty_allow, multi_select=multi_select, header=header
            )
        if type(arns) == str:
            self.arns[0] = str(arns)
        elif type(arns) == list:
            self.arns = list(arns)
