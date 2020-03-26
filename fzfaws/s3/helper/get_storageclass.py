"""use fzf to get the storage class

Construct fzf string and call fzf
"""
from fzfaws.utils.pyfzf import Pyfzf


def get_storageclass():
    """get valid storage class

    Returns:
        string, the storage class user selected
        Return empty string when the selection is empty
    """
    print('Select a storage class, esc to use the default storage class')
    class_fzf = Pyfzf()
    class_fzf.append_fzf('STANDARD\n')
    class_fzf.append_fzf('REDUCED_REDUNDANCY\n')
    class_fzf.append_fzf('STANDARD_IA\n')
    class_fzf.append_fzf('ONEZONE_IA\n')
    class_fzf.append_fzf('INTELLIGENT_TIERING\n')
    class_fzf.append_fzf('GLACIER\n')
    class_fzf.append_fzf('DEEP_ARCHIVE\n')
    return class_fzf.execute_fzf(empty_allow=True, print_col=1)

