import subprocess
import os
import sys
from fzfaws.utils.exceptions import NoSelectionMade, EmptyList
from typing import Optional, Union


class Pyfzf:
    """A simple wrapper class for fzf utilizing subprocess module.

    To create a entry into fzf, use Pyfzf.append_fzf() and pass in the string.
    To create mutiple entries, would require manually pass in \n to seperate each entry.
    For a list of response from boto3, it is recommanded to use the process_list() function.
    """

    def __init__(self) -> None:
        self.fzf_string: str = ""
        if sys.maxsize > 2 ** 32:
            arch = "amd64"
        else:
            arch = "386"

        if sys.platform.startswith("darwin"):
            system = "darwin"
        elif sys.platform.startswith("linux"):
            system = "linux"
        else:
            print("Your system doesn't seem to be compatible with fzfaws")
            print(
                "fzfaws currently is only compatible with python3.5+ on MacOS or Linux"
            )
            exit(1)
        self.fzf_path: str = (
            "fzf"
            if os.getenv("FZFAWS_FZF_EXECUTABLE", "binary") == "system"
            else "%s/../libs/fzf-0.21.1-%s_%s"
            % (os.path.dirname(os.path.abspath(__file__)), system, arch)
        )

    def append_fzf(self, new_string: str) -> None:
        """Append stings to fzf_string

        To have mutiple entries, seperate them by \n
        Example:fzf.append_fzf('hello')
                fzf.append_fzf('\n')
                fzf.append_fzf('world')

        :param new_string: strings to append to fzf entry
        :type new_string: str
        """
        self.fzf_string += new_string

    def execute_fzf(
        self,
        empty_allow: bool = False,
        print_col: int = 2,
        preview: Optional[str] = None,
        multi_select: bool = False,
        header: Optional[str] = None,
    ) -> Union[str, list]:
        """execute fzf and return formated string

        Example:
            fzf = Pyfzf()
            fzf.append_fzf('Hello: hello')
            fzf.append_fzf('\n')
            fzf.append_fzf('World: world')
            fzf.append_fzf('\n')
            print(fzf.execute_fzf(empty_allow=True, print_col=1, preview='cat {}', multi_select=True))
            Above example would return 'Hello:'' if the first entry is selected, print col is 1
            if print_col was 2, 'hello' would be printed

        :param empty_allow: determine if empty selection is allowed
        :type empty_allow: bool, optional
        :param print_col: which column of the result to print (used by awk), -1 print everything except first col
        :type print_col: int, optional
        :param preview: display preview in fzf, e.g.(echo 'hello')
        :type preview: str, optional
        :param multi_select: enable fzf multi selection
        :type multi_select: bool, optional
        :param header: header to display in fzf
        :type header: str, optional
        :raises NoSelectionMade: when user did not make a selection and empty_allow is False
        :return: selected entry from fzf
        :rtype: Union[list, str]
        """

        # remove trailing spaces/lines
        self.fzf_string = str(self.fzf_string).rstrip()
        fzf_input = subprocess.Popen(("echo", self.fzf_string), stdout=subprocess.PIPE)
        cmd_list: list = self._construct_fzf_cmd()
        selection_name: bytes = b""

        if header:
            cmd_list.append("--header=%s" % header)

        if multi_select:
            cmd_list.append("--multi")
        else:
            cmd_list.append("--no-multi")

        if preview:
            cmd_list.extend(["--preview", preview])

        try:
            # get the output of fzf and check if ctrl-c is pressed
            selection = subprocess.check_output(cmd_list, stdin=fzf_input.stdout)
            # if first line contains ctrl-c, exit
            self._check_ctrl_c(selection)

            # reopen the pipeline, first line will be empty if pass previous test
            echo_selection = subprocess.Popen(
                ["echo", selection], stdout=subprocess.PIPE
            )
            if print_col == -1:
                selection_name = subprocess.check_output(
                    ("awk", '{$1=""; print}'), stdin=echo_selection.stdout
                )
            else:
                selection_name = subprocess.check_output(
                    ("awk", "{print $%s}" % (print_col)), stdin=echo_selection.stdout,
                )

            if not selection_name and not empty_allow:
                raise NoSelectionMade("No selection was made")
        except subprocess.CalledProcessError:
            # this exception may happend if user didn't make a selection in fzf
            # thus ending with non zero exit code
            if not empty_allow:
                raise NoSelectionMade("No selection was made")
            elif empty_allow:
                if multi_select:
                    return []
                else:
                    return ""

        if multi_select:
            # multi_select would return everything seperate by \n
            return_list = str(selection_name, "utf-8").strip().splitlines()
            return [item.strip() for item in return_list]
        else:
            # conver the byte to string and remove the empty trailing line
            return str(selection_name, "utf-8").strip()

    def get_local_file(
        self,
        search_from_root: bool = False,
        cloudformation: bool = False,
        directory: bool = False,
        hidden: bool = False,
        empty_allow: bool = False,
        multi_select: bool = False,
        header: Optional[str] = None,
    ) -> Union[str, list]:
        """get local files through fzf

        populate the local files into fzf, if search_from_root is true
        all files would be populated.
        Note: could be extremely slow to seach if fd not installed

        :param search_from_root: search files from root
        :type search_from_root: bool, optional
        :param cloudformation: only search yaml or json
        :type cloudformation: bool, optional
        :param directory: search directory
        :type directory: bool, optional
        :param hidden: search hidden file, only has effect when fd installed
        :type hidden: bool, optional
        :param empty_allow: allow empty selection
        :type empty_allow: bool, optional
        :param multi_select: allow multi selection
        :type multi_select: bool, optional
        :param header: header display in fzf
        :type header: str, optional
        :raises NoSelectionMade: when empty_allow=False and no selection was made
        :return: selected file path or folder path
        :rtype: Union[str, list]
        """

        if search_from_root:
            home_path = os.path.expanduser("~")
            os.chdir(home_path)
        if not header and directory and empty_allow:
            header = "Exit without selection will use %s" % os.getcwd()
        if self._check_fd():
            cmd_list: list = []
            if directory:
                cmd_list.extend(["fd", "--type", "d"])
            elif cloudformation:
                cmd_list.extend(["fd", "--type", "f", "--regex", r"(yaml|yml|json)$"])
            else:
                cmd_list.extend(["fd", "--type", "f"])
            if hidden:
                cmd_list.append("-H")
            list_file = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)

        else:
            # set shell=True so that it won't interpret the glob before executing the command
            # TODO: find another way to use shell=False
            if directory:
                list_file = subprocess.Popen(
                    "find * -type d",
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    shell=True,
                )
            elif cloudformation:
                list_file = subprocess.Popen(
                    (
                        'find * -type f -name "*.json" -o -name "*.yaml" -o -name "*.yml"'
                    ),
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    shell=True,
                )
            else:
                list_file = subprocess.Popen(
                    "find * -type f",
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    shell=True,
                )
        selected_file_path: bytes = b""

        try:
            cmd_list: list = self._construct_fzf_cmd()
            if header:
                cmd_list.append("--header=%s" % header)
            if multi_select:
                cmd_list.append("-m")
            else:
                cmd_list.append("+m")
            selected_file_path = subprocess.check_output(
                cmd_list, stdin=list_file.stdout
            )
            self._check_ctrl_c(selected_file_path)
            if not empty_allow and not selected_file_path:
                raise NoSelectionMade("No selection was made")

        except subprocess.CalledProcessError:
            # subprocess exception will raise when user press ecs to exit fzf
            if not empty_allow:
                raise NoSelectionMade("No selection was made")
            elif empty_allow and directory:
                # return current directory
                curdir = os.getcwd()
                print("%s will be used" % curdir)
                return curdir
            elif empty_allow:
                return [] if empty_allow else ""
        if multi_select:
            # multi_select would return everything seperate by \n
            return str(selected_file_path, "utf-8").strip().splitlines()
        else:
            return str(selected_file_path, "utf-8").strip()

    def _construct_fzf_cmd(self) -> list:
        cmd_list: list = [self.fzf_path, "--ansi", "--expect=ctrl-c"]
        if os.getenv("FZFAWS_FZF_OPTS"):
            cmd_list.extend(os.getenv("FZFAWS_FZF_OPTS").split(" "))
        if os.getenv("FZFAWS_FZF_KEYS"):
            cmd_list.append(os.getenv("FZFAWS_FZF_KEYS"))
        return cmd_list

    def _check_ctrl_c(self, raw_bytes: bytes) -> None:
        """check if ctrl_c is pressed during fzf invokation

        If ctrl_c is pressed, exit entire program instead of
        keep moving forward

        :param raw_bytes: the raw output from fzf subprocess
        :type raw_bytes: bytes
        """
        check_init = subprocess.Popen(["echo", raw_bytes], stdout=subprocess.PIPE)
        key_press = subprocess.check_output(["head", "-1"], stdin=check_init.stdout)
        if (str(key_press, "utf-8").strip()) == "ctrl-c":
            raise KeyboardInterrupt

    def _check_fd(self):
        """check if fd is intalled on the machine
        """
        try:
            subprocess.run(["fd", "-V"], stdout=subprocess.DEVNULL)
            return True
        except:
            return False

    def process_list(self, response_list: list, key_name: str, *arg_keys, gap: int = 2):
        """process list passed in and formatted for fzf

        processes the list passed into it and prepare the fzf operation
        Note: you will need to invoke fzf.execute_fzf() to pop the fzf

        Example:
            list = [{'Name': 1, 'Mame': 2}, {'Name': 2, 'Mame': 3}]
            fzf.process_list(list, 'Name', 'Mame', gap=4)
            fzf.execute_fzf(empty_allow=False)
            if first entry is selected, it will return 1

        :param response_list: list to process
        :type response_list: list
        :param key_name: key_name to search and add into response
        :type key_name: str
        :param gap: gap between each key
        :type gap: int, optional
        :raises EmptyList: when the list is empty and did not get any result
        """
        for item in response_list:
            self.append_fzf("%s: %s" % (key_name, item.get(key_name, "N/A")))
            for arg in arg_keys:
                self.append_fzf(gap * " ")
                self.append_fzf("%s: %s" % (arg, item.get(arg, "N/A")))
            self.append_fzf("\n")
        if not self.fzf_string:
            raise EmptyList("Result list was empty, exiting..")
