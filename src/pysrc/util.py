# common helper functions for cform
import re


# check if it is yaml file
def is_yaml(file_name):
    return re.match(r'^.*\.(yaml|yml)$', file_name)


# check if it is json file
def is_json(file_name):
    return re.match(r'^.*\.json$', file_name)


# helper function to remove a dict in list
def remove_dict_from_list(value, target_list, key_name):
    return_list = target_list
    for item in target_list:
        if item[key_name] == value:
            return_list.remove(item)
    return return_list


# helper function to find dict in list based on key values
def search_dict_in_list(value, target_list, name):
    return [item for item in target_list if item[name] == value][0]


def get_confirmation(message):
    confirm = None
    while confirm != 'y' and confirm != 'n':
        confirm = input(message).lower()
    return confirm
