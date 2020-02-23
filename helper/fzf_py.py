import subprocess
import os


class fzf_py:
    def __init__(self):
        self.fzf_string = ''

    def append_fzf(self, new_string):
        self.fzf_string += new_string

    def execute_fzf(self):
        # remove the empty line at the end
        self.fzf_string = str(self.fzf_string).rstrip()
        # piping to fzf and use awk to pick up the second field
        fzf_input = subprocess.Popen(
            ('echo', self.fzf_string), stdout=subprocess.PIPE)
        selection = subprocess.Popen(
            ('fzf'), stdin=fzf_input.stdout, stdout=subprocess.PIPE)
        selection_name = subprocess.check_output(
            ('awk', '{print $2}'), stdin=selection.stdout)

        if not selection_name:
            raise Exception('Empty selection, exiting..')

        # conver the byte to string and remove the empty trailing line
        return str(selection_name, 'utf-8').rstrip()

    def get_local_file(self):
        home_path = os.environ['HOME']
        os.chdir(home_path)
        list_file = subprocess.Popen(
            ('fd', '--type', 'f'), stdout=subprocess.PIPE)
        selected_file_path = subprocess.check_output(
            ('fzf'), stdin=list_file.stdout)
        return f"{home_path}/{str(selected_file_path, 'utf-8')}"
