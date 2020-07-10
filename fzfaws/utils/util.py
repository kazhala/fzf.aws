"""This module contains some common helper functions."""
import os
from typing import Any, Dict, Generator, List, Optional, Union


def remove_dict_from_list(
    value: Any, target_list: List[Dict[str, Any]], key_name: str
) -> List[Dict[str, Any]]:
    """Remove a dict in list.

    :param value: value to search for and remove
    :type value: Any
    :param target_list: list that needs to be updated
    :type target_list: List[Dict[str, Any]]
    :param key_name: key to match the value
    :type key_name: str
    :return: updated list
    :rtype: list
    """
    return_list = target_list[:]
    for item in target_list:
        if item.get(key_name) == value:
            return_list.remove(item)
    return return_list


def search_dict_in_list(
    value: Any,
    target_list: Union[List[Dict[str, Any]], Generator[Dict[str, Any], None, None]],
    key_name: str,
) -> Dict[str, Any]:
    """Find dict in list based on key values.

    :param value: value to search
    :type value: Any
    :param target_list: list of dict to search
    :type target_list: Union[List[Dict[str, Any]], Generator[Dict[str, Any], None, None]]
    :param name: key name to match
    :type key_name: str
    :return: dict that matched the value
    :rtype: dict
    """
    result = [item for item in target_list if item.get(key_name) == value]
    return result[0] if result else {}


def check_dict_value_in_list(
    value: Any, target_list: List[Dict[str, Any]], key_name: str
) -> bool:
    """Check if a specific value is in a list of dict.

    :param value: value to search
    :type value: Any
    :param target_list: list to search
    :type target_list: List[Dict[str, Any]]
    :param name: key name to match
    :type key_name: str
    :return: a bool indicate whether contains or not
    :rtype: bool
    """
    for item in target_list:
        if item.get(key_name) == value:
            return True
    return False


def get_confirmation(message: str) -> bool:
    """Get user confirmation.

    :param message: message to ask
    :type message: str
    :return: user confirm status
    :rtype: bool
    """
    confirm = None
    while confirm != "y" and confirm != "n":
        confirm = input("%s(y/n): " % message).lower()
    return True if confirm == "y" else False


def get_name_tag(response_item: Dict[str, Any]) -> Optional[str]:
    """Get the name tag of the item.

    This is only specificilly used for boto3 response that contains name tag.

    :param list_item: boto3 respoonse dict
    :type list_item: Dict[str, Any]
    :return: name tag
    :rtype: Optional[str]
    """
    if check_dict_value_in_list("Name", response_item.get("Tags", []), "Key"):
        return search_dict_in_list("Name", response_item.get("Tags", []), "Key").get(
            "Value"
        )
    else:
        return None


def get_default_args(action_command: str, curr_args: List[Any]) -> List[Any]:
    """Prepend the user config default args to arg list of fzfaws.

    User could specify default args in config file and fileloader
    would process and put them in env. This function is used
    to retrieve those env and prepend the arg list so that user
    could still override their default args.

    :param curr_args: current argument list
    :type curr_args: List[Any]
    :return: processed arg list
    :rtype: List[Any]
    """
    if len(curr_args) < 1:
        return curr_args
    action_subcommand = curr_args[0]
    action_options = curr_args[1:]
    default_args = os.getenv(
        "FZFAWS_%s_%s" % (action_command.upper(), action_subcommand.upper())
    )
    if not default_args:
        return curr_args
    else:
        return [action_subcommand] + default_args.split() + action_options
