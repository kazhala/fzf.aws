# common helper functions for awscform
import re


# check if it is yaml file
def is_yaml(file_name):
    return re.match(r'^.*\.(yaml|yml)$', file_name)


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


# get new tags for stacks during update or create
def get_stack_tags():
    tag_list = []
    print('Tags help you identify your sub resources')
    print('A "Name" tag is suggested to enter at the very least')
    print('Skip enter value to stop entering for tags')
    while True:
        tag_name = input('TagName: ')
        if not tag_name:
            break
        tag_value = input('TagValue: ')
        if not tag_value:
            break
        tag_list.append({'Key': tag_name, 'Value': tag_value})
    return tag_list
