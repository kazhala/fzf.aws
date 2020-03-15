"""helper functions for file name validations"""
import re


# check if it is yaml file
def is_yaml(file_name):
    return re.match(r'^.*\.(yaml|yml)$', file_name)


# check if it is json file
def is_json(file_name):
    return re.match(r'^.*\.json$', file_name)


# check if file type is valid cloudformation type
def check_is_valid(file_name):
    if not is_yaml(file_name) and not is_json(file_name):
        print('Selected file is not a valid template file type')
        exit()
