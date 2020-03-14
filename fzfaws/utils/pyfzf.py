import subprocess
import os
from fzfaws.utils.exceptions import NoSelectionMade


class Pyfzf:
    """
    Python simple wrapper class for fzf used for fzf.aws, user who uses this class
    will need to pass \n into the append_fzf function inorder to create different entries,
    Currently only supports a few limited operation, reading second column data
    and select local file path, require checks on fd existence
    """

    def __init__(self):
        self.fzf_string = ''

    # add new strings that will be passed into fzf
    # use \n to sperate entries
    def append_fzf(self, new_string):
        self.fzf_string += new_string

    # execute fzf and return formated string
    def execute_fzf(self, empty_allow=False, print_col=2, preview=None, multi_select=False):
        # remove the empty line at the end
        self.fzf_string = str(self.fzf_string).rstrip()
        # piping to fzf and use awk to pick up the second field
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

    # get any local files through fd
    def get_local_file(self, search_from_root):
        if search_from_root:
            home_path = os.environ['HOME']
            os.chdir(home_path)
        if self.check_fd():
            list_file = subprocess.Popen(
                ('fd', '--type', 'f', '--regex', r'(yaml|yml|json)$'), stdout=subprocess.PIPE)
        else:
            list_file = subprocess.Popen(
                ('find * -type f -name "*.json" -o -name "*.yaml" -o -name "*.yml"'),
                stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, shell=True)
        selected_file_path = subprocess.check_output(
            ('fzf'), stdin=list_file.stdout)
        if search_from_root:
            return f"{home_path}/{str(selected_file_path, 'utf-8').rstrip()}"
        else:
            return f"{str(selected_file_path, 'utf-8').rstrip()}"

    def check_fd(self):
        try:
            subprocess.run(['fd', '-V'], stdout=subprocess.DEVNULL)
            return True
        except:
            return False

    # process a list of dict and put into fzf menu
    def process_list(self, response_list, key_name, *arg_keys, multi_select=False, gap=2, empty_allow=True):
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
