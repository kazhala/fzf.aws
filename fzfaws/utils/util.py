# common helper functions


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


# check if a specific value in dict
def check_dict_value_in_list(value, target_list, name):
    for item in target_list:
        if item.get(name) == value:
            return True
    return False


def get_confirmation(message):
    confirm = None
    while confirm != 'y' and confirm != 'n':
        confirm = input("%s(y/n): " % message).lower()
    return True if confirm == 'y' else False


def get_name_tag(list_item):
    """get the name tag of the item"""
    if 'Tags' in list_item and check_dict_value_in_list('Name', list_item['Tags'], 'Key'):
        return search_dict_in_list(
            'Name', list_item['Tags'], 'Key')['Value']
    else:
        return 'N/A'
