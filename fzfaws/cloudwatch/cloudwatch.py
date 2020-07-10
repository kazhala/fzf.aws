"""Contains wrapper class to interacte with cloudwatch."""
from typing import Optional, Union

from fzfaws.utils import BaseSession, Pyfzf, Spinner


class Cloudwatch(BaseSession):
    """Cloudwatch wrapper class.

    Handles all operation related to cloudwatch.

    At the moment is still just a helper class to other
    class like Cloudformation.

    :param profile: profile to use for this operation
    :type profile: Union[bool, str]
    :param region: region to use for this operation
    :type region: Union[bool, str]
    """

    def __init__(
        self,
        profile: Optional[Union[str, bool]] = None,
        region: Optional[Union[str, bool]] = None,
    ) -> None:
        """Construct the Cloudwatch instance."""
        super().__init__(profile=profile, region=region, service_name="cloudwatch")
        self.arns: list = [""]

    def set_arns(
        self,
        arns: Optional[Union[str, list]] = None,
        empty_allow: bool = False,
        header: Optional[str] = None,
        multi_select: bool = False,
    ) -> None:
        """Set cloudwatch arns for further operations.

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
            with Spinner.spin(message="Fetching cloudwatch alarms ..."):
                paginator = self.client.get_paginator("describe_alarms")
                for result in paginator.paginate():
                    if result.get("CompositeAlarms"):
                        fzf.process_list(result["CompositeAlarms"], "AlarmArn")
                    if result.get("MetricAlarms"):
                        fzf.process_list(result["MetricAlarms"], "AlarmArn")
            arns = fzf.execute_fzf(
                empty_allow=empty_allow, multi_select=multi_select, header=header
            )
        if type(arns) == str:
            self.arns[0] = str(arns)
        elif type(arns) == list:
            self.arns = list(arns)
