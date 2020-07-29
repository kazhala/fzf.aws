"""Module contains lambda wrapper class."""
from typing import Any, Dict, List, Union, Optional
from fzfaws.utils import BaseSession, Spinner, Pyfzf


class Lambdaf(BaseSession):
    """Lambda wrapper class to interact with boto3.client('lambda').

    Handles the initialisation of lambda client, selection of lambda
    functions.
    
    :param profile: use a different profile for this opeartion
    :type profile: Union[str, bool], optional
    :param region: use a different region for this operation
    :type region: Union[str, bool], optional
    """

    def __init__(
        self, profile: Union[str, bool] = None, region: Union[str, bool] = None
    ):
        """Construct the instance."""
        super().__init__(profile=profile, region=region, service_name="lambda")
        self.function_name: str = ""
        self.function_detail: Dict[str, str] = {}

    def set_lambdaf(
        self, no_progress: bool = False, header: str = "", all_version: bool = False
    ) -> None:
        """Set the function name for lambda operation.

        :param no_progress: don't show spinner, useful for ls commands
        :type no_progress: bool
        :param header: header to display in fzf header
        :type header: str, optional
        :param all_version: list all versions of all functions
        :type all_version: bool, optional
        """
        with Spinner.spin(
            message="Fetching lambda functions ...", no_progress=no_progress
        ):
            fzf = Pyfzf()
            paginator = self.client.get_paginator("list_functions")
            arguments = {"FunctionVersion": "ALL"} if all_version else {}
            for result in paginator.paginate(**arguments):
                fzf.process_list(
                    result.get("Functions", {}),
                    "FunctionName",
                    "Runtime",
                    "Version",
                    "Description",
                )
        selected_function = fzf.execute_fzf(header=header, print_col=0)
        self.function_detail = fzf.format_selected_to_dict(str(selected_function))
        self.function_name = self.function_detail.get("FunctionName", "")
