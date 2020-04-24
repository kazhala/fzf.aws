import subprocess
import os
from fzfaws.utils.exceptions import NoSelectionMade, EmptyList


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

    def execute_fzf(self, empty_allow=False, print_col=2, preview=None, multi_select=False, header=None):
        """execute fzf and return formated string

        Args:
            empty_allow: bool, determine if empty selection is allowed
            print_col: number, which column to print after selection, starts with 1
                more details about preview, see fzf documentation
                use -1 to print everything except first column, useful when you have filenames with spaces
            preview: string, display preview for each entry, require shell script string
            multi_select: bool, if multi select is allowed
            header: string, display helper information/title
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
        cmd_list = ['fzf', '--ansi', '--expect=ctrl-c']
        cmd_list.append(
            '--bind=alt-a:toggle-all,alt-j:jump,alt-0:top,alt-o:clear-query')
        if header:
            cmd_list.append('--header=%s' % header)

        if multi_select:
            cmd_list.append('--multi')
        else:
            cmd_list.append('--no-multi')

        if preview:
            cmd_list.extend(['--preview', preview])

        try:
            # get the output of fzf and check if ctrl-c is pressed
            selection = subprocess.check_output(
                cmd_list, stdin=fzf_input.stdout)
            self._check_ctrl_c(selection)

            # reopen the pipeline and delete the first line(key information)
            echo_selection = subprocess.Popen(
                ['echo', selection], stdout=subprocess.PIPE)
            if print_col == -1:
                selection_name = subprocess.check_output(
                    ('awk', '{$1=""; print}'), stdin=echo_selection.stdout)
            else:
                selection_name = subprocess.check_output(
                    ('awk', '{print $%s}' % (print_col)), stdin=echo_selection.stdout)

            if not selection_name and not empty_allow:
                raise NoSelectionMade
        except subprocess.CalledProcessError:
            if not empty_allow:
                raise NoSelectionMade
            elif empty_allow:
                if multi_select:
                    return []
                else:
                    return ''

        if multi_select:
            # multi_select would return everything seperate by \n
            return_list = str(selection_name, 'utf-8').strip().splitlines()
            return [item.strip() for item in return_list]
        else:
            # conver the byte to string and remove the empty trailing line
            return str(selection_name, 'utf-8').strip()

    def get_local_file(self, search_from_root=False, cloudformation=False, directory=False, hidden=False, empty_allow=False, multi_select=False, header=None):
        """get local files through fzf

        populate the local files into fzf, if search_from_root is true
        all files would be populated.
        Note: could be extremely slow to seach if fd not installed

        Args:
            search_from_root: bool, whether to search from root dir
            cloudformation: bool, if this is triggered by cloudformation operations
                only json and yaml will be populated
            directory: bool, search directory
            hidden: include hidden files/folders with search using fd
            empty_allow: bool, allow empty selection, if set, use current directory
            header: string, display helper text/title
        Returns:
            the file path of the selected file
        """

        if search_from_root:
            home_path = os.path.expanduser('~')
            os.chdir(home_path)
        if not header and directory and empty_allow:
            header = 'Exit without selection will use %s' % os.getcwd()
        if self._check_fd():
            cmd_list = []
            if directory:
                cmd_list.extend(['fd', '--type', 'd'])
            elif cloudformation:
                cmd_list.extend(
                    ['fd', '--type', 'f', '--regex', r'(yaml|yml|json)$'])
            else:
                cmd_list.extend(['fd', '--type', 'f'])
            if hidden:
                cmd_list.append('-H')
            list_file = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)

        else:
            # set shell=True so that it won't interpret the glob before executing the command
            # TODO: find another way to use shell=False
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
        try:
            cmd_list = ['fzf', '--expect=ctrl-c']
            cmd_list.append(
                '--bind=alt-a:toggle-all,alt-j:jump,alt-0:top,alt-o:clear-query')
            if header:
                cmd_list.append('--header=%s' % header)
            if multi_select:
                cmd_list.append('-m')
            else:
                cmd_list.append('+m')
            selected_file_path = subprocess.check_output(
                cmd_list, stdin=list_file.stdout)
            self._check_ctrl_c(selected_file_path)
            if not empty_allow and not selected_file_path:
                raise NoSelectionMade
        except subprocess.CalledProcessError:
            if not empty_allow:
                raise NoSelectionMade
            elif empty_allow and directory:
                selected_file_path = os.getcwd()
                print('%s will be used' % selected_file_path)
                return selected_file_path
            elif empty_allow:
                return
        if multi_select:
            # multi_select would return everything seperate by \n
            return str(selected_file_path, 'utf-8').strip().splitlines()
        else:
            return str(selected_file_path, 'utf-8').strip()

    def _check_ctrl_c(self, raw_bytes):
        """check if ctrl_c is pressed during fzf invokation

        If ctrl_c is pressed, exit entire program instead of
        keep moving forward

        Args:
            raw_bytes: the raw output of fzf
        """
        check_init = subprocess.Popen(
            ['echo', raw_bytes], stdout=subprocess.PIPE)
        key_press = subprocess.check_output(
            ['head', '-1'], stdin=check_init.stdout)
        if (str(key_press, 'utf-8').strip()) == 'ctrl-c':
            raise KeyboardInterrupt

    def _check_fd(self):
        """check if fd is intalled on the machine"""
        try:
            subprocess.run(['fd', '-V'], stdout=subprocess.DEVNULL)
            return True
        except:
            return False

    def process_list(self, response_list, key_name, *arg_keys, gap=2):
        """process list passed in and formatted for fzf

        processes the list passed into it and prepare the fzf operation
        Note: you will need to invoke fzf.execute_fzf() to pop the fzf

        Args:
            response_list: list, the list to process
            key_name: string, key in response_list to print
            *arg_keys: specify any numbers of key to print
            gap: number, gap between text
        Returns:
            A string which contains the value from response_list[key_name]
        Exceptions:
            EmptyList: when the input list resulted in empty result
        Example:
            list = [{'Name': 1, 'Mame': 2}, {'Name': 2, 'Mame': 3}]
            fzf.process_list(list, 'Name', 'Mame', gap=4)
            fzf.execute_fzf(empty_allow=False)
            if first entry is selected, it will return 1
        """
        for item in response_list:
            self.append_fzf(f"{key_name}: {item.get(key_name)}")
            for arg in arg_keys:
                self.append_fzf(gap*' ')
                self.append_fzf(f"{arg}: {item.get(arg)}")
            self.append_fzf('\n')
        if not self.fzf_string:
            raise EmptyList('Result list was empty, exiting..')
