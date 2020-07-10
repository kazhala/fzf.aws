"""The module contains the sns wrapper class."""
from typing import Optional, Union, List

from fzfaws.utils import BaseSession, Pyfzf, Spinner


class SNS(BaseSession):
    """The sns wrapper class to interacte with boto3.

    Inherite from BaseSession to better control profile, region.

    At the moment is still just a helper class to other
    class like Cloudformation.

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
        """Construct the sns class."""
        super().__init__(profile=profile, region=region, service_name="sns")
        self.arns: list = [""]

    def set_arns(
        self,
        arns: Optional[Union[str, List[str]]] = None,
        empty_allow: bool = False,
        header: Optional[str] = None,
        multi_select: bool = False,
    ) -> None:
        """Set the sns arn for other operations.

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
            with Spinner.spin(message="Fetching sns topics ..."):
                paginator = self.client.get_paginator("list_topics")
                for result in paginator.paginate():
                    fzf.process_list(result.get("Topics", []), "TopicArn")
            arns = fzf.execute_fzf(
                empty_allow=empty_allow, multi_select=multi_select, header=header
            )
        if type(arns) == str:
            self.arns[0] = str(arns)
        elif type(arns) == list:
            self.arns = list(arns)
