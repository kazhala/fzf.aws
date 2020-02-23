import subprocess


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
