"""This module contains the FileLoader class.

Import this module to process yaml, json files.
"""

import json
import os
from typing import Any, Dict

import yaml
from yaml.error import YAMLError

# make yaml class ignore all undefined tags and keep parsing
# yaml doesn't understand all the !Ref, !FindInMap etc
yaml.SafeLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


class FileLoader:
    """Class used to load yaml/json files.

    FileLoader class is responsible to process yaml or json file or raw file
    stream and format them to dictionary.

    The main use of the class is to load user configuration file and set
    appropriate env variables for other functions in fzfaws to consume.

    :param path: file path to read
    :type path: str, optional
    :param body: body to process
    :type body: str, optional
    """

    def __init__(self, path: str = None, body: str = None) -> None:
        """Construct FileLoader class."""
        if path == None:
            path = ""
        if body == None:
            body = ""
        self.path: str = path
        self.body: str = body

    def process_yaml_file(self) -> Dict[str, Any]:
        """Read yaml file and return the file body.

        :return: a dict containing both raw file str and dictionary
        :rtype: dict
        """
        with open(self.path, "r") as file:
            body = file.read()
            formated_body = yaml.safe_load(body)
            return {"body": body, "dictBody": formated_body}

    def process_json_file(self) -> Dict[str, Any]:
        """Read the json file and return the file body.

        :return: a dict containing both raw file str and dictionary
        :rtype: dict
        """
        with open(self.path, "r") as file:
            body = file.read()
            formated_body = json.loads(body)
            return {"body": body, "dictBody": formated_body}

    def process_yaml_body(self) -> dict:
        """Process the yaml body.

        :return: loaded dictionary
        :rtyrp: dict
        """
        return yaml.safe_load(self.body)

    def process_json_body(self) -> dict:
        """Process the json body.

        :return: loaded dictionary
        :rtyrp: dict
        """
        return json.loads(self.body)

    def load_config_file(self, config_path: str = None) -> None:
        """Load config file into dict.

        process all of the configs and set env variable for run time

        :param config_path: config path, useful for unit testing only
        :type user: str, optional
        """
        if not config_path:
            home = os.path.expanduser("~")
            base_directory = os.getenv("XDG_CONFIG_HOME", "%s/.config" % home)
            config_path = "%s/fzfaws/fzfaws.yml" % base_directory
        if not os.path.isfile(config_path):
            return
        with open(config_path, "r") as file:
            try:
                body = file.read()
                formated_body = yaml.safe_load(body)
                if not formated_body:
                    return
                self._set_fzf_env(formated_body.get("fzf", {}))
                self._set_spinner_env(formated_body.get("spinner", {}))
                self._set_gloable_env(formated_body.get("global", {}))
                if not formated_body.get("services"):
                    return
                else:
                    self._set_ec2_env(formated_body["services"].get("ec2", {}))
                    self._set_s3_env(formated_body["services"].get("s3", {}))
                    self._set_cloudformation_env(
                        formated_body["services"].get("cloudformation", {})
                    )
            except YAMLError as e:
                print("Config file is malformed, please double check your config file")
                print(e)

    def _set_spinner_env(self, spinner_settings: Dict[str, Any]) -> None:
        """Set spinner settings.

        :param spinner_settings: settings for the spinner from the user config
        :type spinner_settings: Dict[str, Any]
        """
        if not spinner_settings:
            return
        if spinner_settings.get("message"):
            os.environ["FZFAWS_SPINNER_MESSAGE"] = spinner_settings["message"]
        if spinner_settings.get("speed"):
            os.environ["FZFAWS_SPINNER_SPEED"] = str(spinner_settings["speed"])
        if spinner_settings.get("pattern"):
            os.environ["FZFAWS_SPINNER_PATTERN"] = spinner_settings["pattern"]

    def _set_cloudformation_env(self, cloudformation_settings: Dict[str, Any]) -> None:
        """Set cloudformation settings.

        :param cloudformation_settings: settins from config file
        :type cloudformation_settings: Dict[str, Any]
        """
        if not cloudformation_settings:
            return
        if cloudformation_settings.get("profile"):
            os.environ["FZFAWS_CLOUDFORMATION_PROFILE"] = cloudformation_settings[
                "profile"
            ]
        if cloudformation_settings.get("region"):
            os.environ["FZFAWS_CLOUDFORMATION_REGION"] = cloudformation_settings[
                "region"
            ]
        if cloudformation_settings.get("default_args"):
            for key, value in cloudformation_settings["default_args"].items():
                os.environ["FZFAWS_CLOUDFORMATION_%s" % key.upper()] = value
        if cloudformation_settings.get("waiter"):
            os.environ["FZFAWS_CLOUDFORMATION_WAITER"] = json.dumps(
                cloudformation_settings.get("waiter", {})
            )

    def _set_s3_env(self, s3_settings: Dict[str, Any]) -> None:
        """Set s3 service settings.

        :param s3_settings: s3 settings from config file
        :type s3_settings: Dict[str, Any]
        """
        if not s3_settings:
            return
        if s3_settings.get("transfer_config"):
            os.environ["FZFAWS_S3_TRANSFER"] = json.dumps(
                s3_settings["transfer_config"]
            )
        if s3_settings.get("profile"):
            os.environ["FZFAWS_S3_PROFILE"] = s3_settings["profile"]
        if s3_settings.get("default_args"):
            for key, value in s3_settings.get("default_args").items():
                os.environ["FZFAWS_S3_%s" % key.upper()] = value

    def _set_ec2_env(self, ec2_settings: Dict[str, Any]) -> None:
        """Set ec2 service settings.

        :param ec2_settings: ec2 settings from config file
        :type ec2_settings: Dict[str, Any]
        """
        if not ec2_settings:
            return
        if ec2_settings.get("keypair"):
            os.environ["FZFAWS_EC2_KEYPAIRS"] = ec2_settings.get("keypair", "")
        if ec2_settings.get("waiter"):
            os.environ["FZFAWS_EC2_WAITER"] = json.dumps(ec2_settings.get("waiter", {}))
        if ec2_settings.get("default_args"):
            for key, value in ec2_settings.get("default_args").items():
                os.environ["FZFAWS_EC2_%s" % key.upper()] = value
        if ec2_settings.get("profile"):
            os.environ["FZFAWS_EC2_PROFILE"] = ec2_settings["profile"]
        if ec2_settings.get("region"):
            os.environ["FZFAWS_EC2_REGION"] = ec2_settings["region"]

    def _set_gloable_env(self, global_settings: Dict[str, Any]) -> None:
        """Set global settings.

        :param global_settings: loaded global seetings from config file
        :type global_settings: Dict[str, Any]
        """
        if not global_settings:
            return
        if global_settings.get("waiter"):
            os.environ["FZFAWS_GLOBAL_WAITER"] = json.dumps(
                global_settings.get("waiter", {})
            )
        if global_settings.get("profile"):
            os.environ["FZFAWS_GLOBAL_PROFILE"] = global_settings["profile"]
        if global_settings.get("region"):
            os.environ["FZFAWS_GLOBAL_REGION"] = global_settings["region"]

    def _set_fzf_env(self, fzf_settings: Dict[str, Any]) -> None:
        """Set env for fzf.

        :param fzf_settings: loaded fzf settings from config file
        :type fzf_settings: Dict[str, Any]
        """
        if not fzf_settings:
            return
        if fzf_settings.get("executable"):
            os.environ["FZFAWS_FZF_EXECUTABLE"] = fzf_settings["executable"]
        if fzf_settings.get("args"):
            os.environ["FZFAWS_FZF_OPTS"] = fzf_settings["args"]
        if fzf_settings.get("keybinds"):
            keybinds: list = []
            for key, value in fzf_settings.get("keybinds").items():
                keybinds.append("%s:%s" % (value, key))
            if keybinds:
                key_args = "--bind=%s" % ",".join(keybinds)
                os.environ["FZFAWS_FZF_KEYS"] = key_args
