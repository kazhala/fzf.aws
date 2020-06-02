"""contains some common helper functions
"""
from typing import Any


def remove_dict_from_list(value: Any, target_list: list, key_name: str) -> list:
    """help function to remove a dict in list

    :param value: value to search for and remove
    :type value: Any
    :param target_list: list that needs to be updated
    :type target_list: list
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


def search_dict_in_list(value: Any, target_list: list, key_name: str) -> dict:
    """helper function to find dict in list based on key values

    :param value: value to search
    :type value: Any
    :param target_list: list to search
    :type target_list: list
    :param name: key name to match
    :type key_name: str
    :return: dict that matched the value
    :rtype: dict
    """
    result = [item for item in target_list if item.get(key_name) == value]
    return result[0] if result else {}


def check_dict_value_in_list(value: Any, target_list: list, key_name: str) -> bool:
    """check if a specific value is in dict

    :param value: value to search
    :type value: Any
    :param target_list: list to search
    :type target_list: list
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
    """get user confirmation

    :param message: message to ask
    :type message: str
    :return: user confirm status
    :rtype: bool
    """
    confirm = None
    while confirm != "y" and confirm != "n":
        confirm = input("%s(y/n): " % message).lower()
    return True if confirm == "y" else False


def get_name_tag(response_item: dict) -> str:
    """get the name tag of the item

    This only specific use for boto3 response that contains name tag

    :param list_item: boto3 respoonse dict
    :type list_item: dict
    :return: name tag
    :rtype: str
    """
    if check_dict_value_in_list("Name", response_item.get("Tags", []), "Key"):
        return search_dict_in_list("Name", response_item.get("Tags", []), "Key").get(
            "Value", "N/A"
        )
    else:
        return "N/A"
