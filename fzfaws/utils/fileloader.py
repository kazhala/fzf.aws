"""file loader class

Used for processing yaml/json files
"""
import yaml
import json
import os
from typing import Optional

from yaml.error import YAMLError

# make yaml class ignore all undefined tags and keep parsing
# yaml doesn't understand all the !Ref, !FindInMap etc
yaml.SafeLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


class FileLoader:
    """used to load yaml/json files

    :param path: file path to read
    :type path: str, optional
    :param body: body to process
    :type body: str, optional
    """

    def __init__(self, path: Optional[str] = None, body: Optional[str] = None) -> None:
        if path == None:
            path = ""
        if body == None:
            body = ""
        self.path: str = path
        self.body: str = body

    def process_yaml_file(self) -> dict:
        """read yaml file and return the file body

        :return: a dict containing both raw file str and dictionary
        :rtype: dict
        """
        with open(self.path, "r") as file:
            body = file.read()
            formated_body = yaml.safe_load(body)
            return {"body": body, "dictBody": formated_body}

    def process_json_file(self) -> dict:
        """read the json file and return the file body

        :return: a dict containing both raw file str and dictionary
        :rtype: dict
        """
        with open(self.path, "r") as file:
            body = file.read()
            formated_body = json.loads(body)
            return {"body": body, "dictBody": formated_body}

    def process_yaml_body(self) -> dict:
        """process the yaml body

        :return: loaded dictionary
        :rtyrp: dict
        """
        return yaml.safe_load(self.body)

    def process_json_body(self) -> dict:
        """process the json body

        :return: loaded dictionary
        :rtyrp: dict
        """
        return json.loads(self.body)

    def load_config_file(self) -> None:
        """load config file into dict

        process all of the configs and set env variable for run time
        """
        if self.path:
            config_path = self.path
        else:
            home = os.path.expanduser("~")
            base_directory = os.getenv("XDG_CONFIG_HOME", "%s/.config" % home)
            config_path = "%s/fzfaws/fzfaws.yml" % base_directory
        if not os.path.isfile(config_path):
            return
        with open(config_path, "r") as file:
            try:
                body = file.read()
                formated_body = yaml.safe_load(body)
                self._set_fzf_env(formated_body.get("fzf", {}))
            except YAMLError as e:
                print("Config file is malformed, please double check your config file")
                print(e)

    def _set_fzf_env(self, fzf_settings: dict) -> None:
        """set env for fzf

        :param fzf_settings: loaded fzf settings from config file
        :type fzf_settings: dict
        """
        if not fzf_settings:
            return
        os.environ["FZFAWS_FZF_EXECUTABLE"] = fzf_settings.get("executable", "")
        os.environ["FZFAWS_FZF_OPTS"] = fzf_settings.get("args", "")
        keybinds: list = []
        for key, value in fzf_settings.get("keybinds", {}).items():
            keybinds.append("%s:%s" % (value, key))
        if keybinds:
            key_args = "--bind=%s" % ",".join(keybinds)
            os.environ["FZFAWS_FZF_KEYS"] = key_args
