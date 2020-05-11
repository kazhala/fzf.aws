"""contains the iam class

Wraps around boto3.client('iam') and handles profile
"""
from fzfaws.utils.session import BaseSession
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.spinner import Spinner
from typing import Union, Optional, List


class IAM(BaseSession):
    """Handles all iam related operations here

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
        """construtor
        """
        super().__init__(profile=profile, region=region, service_name="iam")
        self.arns: List[str] = [""]

    def set_arns(
        self,
        arns: Optional[Union[List, str]] = None,
        header: Optional[str] = None,
        empty_allow: Optional[bool] = True,
        service: Optional[str] = None,
        multi_select: Optional[bool] = False,
    ) -> None:
        """set the role arn

        :param arns: list of arn to set
        :type arns: list, optional
        :param header: helper message to display in fzf header
        :type header: str, optional
        :param empty_allow: allow empty selection
        :type empty_allow: bool, optional
        :param service: only display role that could be assumed by this service
        :type service: str, optional
        :param multi_select: allow multi selection
        :type multi_select: bool, optional
        """
        try:
            fzf = Pyfzf()
            spinner = Spinner(message="Fetching iam roles..")
            if arns is None:
                spinner.start()
                for result in self.get_paginated_result("list_roles"):
                    if service:
                        for role in result.get("Roles", []):
                            statements = role.get("AssumeRolePolicyDocument", {}).get(
                                "Statement", []
                            )
                            for statement in statements:
                                if (
                                    statement.get("Principal", {}).get("Service", "")
                                    == service
                                ):
                                    fzf.append_fzf(
                                        "RoleName: %s  Arn: %s"
                                        % (
                                            role.get("RoleName", "N/A"),
                                            role.get("Arn", "N/A"),
                                        )
                                    )
                    else:
                        fzf.process_list(result.get("Roles", []), "RoleName", "Arn")
                spinner.stop()
                arns = fzf.execute_fzf(
                    empty_allow=empty_allow,
                    print_col=4,
                    header=header,
                    multi_select=multi_select,
                )
            if type(arns) == str:
                self.arns[0] = str(arns)
            elif type(arns) == list:
                self.arns = list(arns)
        except:
            Spinner.clear_spinner()
            raise
