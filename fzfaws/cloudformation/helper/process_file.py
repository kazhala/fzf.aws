"""This file contains helper mthod to process yaml/json files"""
import yaml
import json

# make yaml class ignore all undefined tags and keep parsing
# yaml doesn't understand all the !Ref, !FindInMap etc
yaml.SafeLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


def process_yaml_file(path):
    """read yaml file and return the file body"""
    with open(path, "r") as body:
        # read all data into template_body for boto3 param
        body = body.read()
        # load yaml into pythong dict
        formated_body = yaml.safe_load(body)
        return {"body": body, "dictBody": formated_body}


def process_json_file(path):
    """read the json file and return the file body"""
    with open(path, "r") as body:
        # read raw body
        body = body.read()
        formated_body = json.loads(body)
        return {"body": body, "dictBody": formated_body}


def process_yaml_body(file_body):
    """process the yaml body"""
    return yaml.safe_load(file_body)


def process_json_body(file_body):
    """process the json body"""
    return json.loads(file_body)
