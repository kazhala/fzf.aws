"""This module contains the iam wrapper class."""
from typing import List, Optional, Union

from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.session import BaseSession
from fzfaws.utils.spinner import Spinner


class IAM(BaseSession):
    """The iam wrapper class handles the operation around iam.

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
        """Construct the iam instance."""
        super().__init__(profile=profile, region=region, service_name="iam")
        self.arns: List[str] = [""]

    def set_arns(
        self,
        arns: Optional[Union[List[str], str]] = None,
        header: Optional[str] = None,
        empty_allow: bool = True,
        service: Optional[str] = None,
        multi_select: bool = False,
    ) -> None:
        """Set the role arn for further operations.

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
        if arns is None:
            fzf = Pyfzf()
            with Spinner.spin(message="Fetching iam roles.."):
                paginator = self.client.get_paginator("list_roles")
                for result in paginator.paginate():
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
                                        % (role.get("RoleName"), role.get("Arn"),)
                                    )
                    else:
                        fzf.process_list(result.get("Roles", []), "RoleName", "Arn")
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
