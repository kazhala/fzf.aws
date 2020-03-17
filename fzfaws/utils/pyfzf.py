import subprocess
import os
from fzfaws.utils.exceptions import NoSelectionMade


class Pyfzf:
    """A simple wrapper class for fzf utilizing subprocess module.

    To create a entry into fzf, use Pyfzf.append_fzf() and pass in the string.
    To create mutiple entries, would require manually pass in \n to seperate each entry.
    For a list of response from boto3, it is recommanded to use the process_list() function.

    Attributes:
        fzf_string: the string that will be passed into fzf in subprocess
    """

    def __init__(self):
        self.fzf_string = ''

    def append_fzf(self, new_string):
        """Append stings to fzf_string

        To have mutiple entries, seperate them by \n

        Args:
            new_string: string, string to add to fzf
        Example:
            fzf.append_fzf('hello')
            fzf.append_fzf('\n')
            fzf.append_fzf('world')
        """
        self.fzf_string += new_string

    def execute_fzf(self, empty_allow=False, print_col=2, preview=None, multi_select=False):
        """execute fzf and return formated string

        Args:
            empty_allow: bool, determine if empty selection is allowed
            print_col: number, which column to print after selection, starts with 1
                more details about preview, see fzf documentation
            preview: string, display preview for each entry, require shell script string
            multi_select: bool, if multi select is allowed
        Returns:
            return the string value of the selected entry, depending ont the print_col
        Example:
            fzf = Pyfzf()
            fzf.append_fzf('Hello: hello')
            fzf.append_fzf('\n')
            fzf.append_fzf('World: world')
            fzf.append_fzf('\n')
            print(fzf.execute_fzf(empty_allow=True, print_col=1, preview='cat {}', multi_select=True))
            Above example would return 'Hello:'' if the first entry is selected, print col is 1
            if print_col was 2, 'hello' would be printed
        """
        # remove the empty line at the end
        self.fzf_string = str(self.fzf_string).rstrip()
        fzf_input = subprocess.Popen(
            ('echo', self.fzf_string), stdout=subprocess.PIPE)
        if not preview:
            if not multi_select:
                selection = subprocess.Popen(
                    ('fzf'), stdin=fzf_input.stdout, stdout=subprocess.PIPE)
            else:
                selection = subprocess.Popen(
                    ('fzf', '-m'), stdin=fzf_input.stdout, stdout=subprocess.PIPE)
        else:
            if not multi_select:
                selection = subprocess.Popen(
                    ('fzf', '--preview', preview), stdin=fzf_input.stdout, stdout=subprocess.PIPE)
            else:
                selection = subprocess.Popen(
                    ('fzf', '-m', '--preview', preview), stdin=fzf_input.stdout, stdout=subprocess.PIPE)
        selection_name = subprocess.check_output(
            ('awk', '{print $%s}' % (print_col)), stdin=selection.stdout)

        if not selection_name and not empty_allow:
            raise NoSelectionMade('Empty selection, exiting..')

        if multi_select:
            # multi_select would return everything seperate by \n
            return str(selection_name, 'utf-8').splitlines()
        else:
            # conver the byte to string and remove the empty trailing line
            return str(selection_name, 'utf-8').rstrip()

    def get_local_file(self, search_from_root=False, cloudformation=False, directory=False):
        """get local files through fzf

        populate the local files into fzf, if search_from_root is true
        all files would be populated.
        Note: could be extremely slow to seach if fd not installed

        Args:
            search_from_root: bool, whether to search from root dir
            cloudformation: bool, if this is triggered by cloudformation operations
                only json and yaml will be populated
        Returns:
            the file path of the selected file
        """
        if search_from_root:
            home_path = os.path.expanduser('~')
            os.chdir(home_path)
        if self._check_fd():
            if directory:
                list_file = subprocess.Popen(
                    ('fd', '--type', 'd'), stdout=subprocess.PIPE)
            elif cloudformation:
                list_file = subprocess.Popen(
                    ('fd', '--type', 'f', '--regex', r'(yaml|yml|json)$'), stdout=subprocess.PIPE)
            else:
                list_file = subprocess.Popen(
                    ('fd', '--type', 'f'), stdout=subprocess.PIPE)
        else:
            if directory:
                list_file = subprocess.Popen(
                    'find * -type d', stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, shell=True)
            elif cloudformation:
                list_file = subprocess.Popen(
                    ('find * -type f -name "*.json" -o -name "*.yaml" -o -name "*.yml"'),
                    stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, shell=True)
            else:
                list_file = subprocess.Popen(
                    'find * -type f', stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, shell=True)
        selected_file_path = subprocess.check_output(
            ('fzf'), stdin=list_file.stdout)
        if search_from_root:
            if directory:
                return f"{str(selected_file_path, 'utf-8').rstrip()}"
            else:
                return f"{home_path}/{str(selected_file_path, 'utf-8').rstrip()}"
        else:
            return f"{str(selected_file_path, 'utf-8').rstrip()}"

    def _check_fd(self):
        """check if fd is intalled on the machine"""
        try:
            subprocess.run(['fd', '-V'], stdout=subprocess.DEVNULL)
            return True
        except:
            return False

    def process_list(self, response_list, key_name, *arg_keys, multi_select=False, gap=2, empty_allow=True):
        """process list passed in and formatted into fzf

        processes the list passed into it and print the key_name and *arg_keys into
        the fzf menu and return the selected value

        Args:
            response_list: list, the list to process
            key_name: string, key in response_list to print
            *arg_keys: specify any numbers of key to print
            multi_select: bool, allow multi_select
            gap: number, gap between text
            empty_allow: bool, if empty selection is allowed
        Returns:
            A string which contains the value from response_list[key_name]
        Example:
            list = [{'Name': 1, 'Mame': 2}, {'Name': 2, 'Mame': 3}]
            print(fzf.process_list(list, 'Name', 'Mame', gap=4))
            if first entry is selected, it will return 1
        """
        for item in response_list:
            self.append_fzf(f"{key_name}: {item[key_name]}")
            for arg in arg_keys:
                self.append_fzf(gap*' ')
                self.append_fzf(f"{arg}: {item[arg]}")
            self.append_fzf('\n')
        if multi_select:
            return self.execute_fzf(empty_allow=empty_allow, multi_select=True)
        else:
            return self.execute_fzf(empty_allow=empty_allow)
