""" Main entry point of the program.

Typical usage example:
    faws <command> --options
"""
import sys
from fzfaws.cform.main import cform
from fzfaws.utils.exceptions import NoCommandFound


def main():
    """Entry function of the fzf.aws module"""

    try:
        # exit if no command found
        if len(sys.argv) < 2:
            raise NoCommandFound()
        available_routes = ['cform', 'ec2', 'keypair', 's3']
        action_command = sys.argv[1]
        if action_command not in available_routes:
            raise NoCommandFound()
        if action_command == 'cform':
            cform(sys.argv[2:])

    # display help message
    # did'n use argparse at the entry level thus creating similar help message
    except NoCommandFound as e:
        print('usage: faws [-h] {cform, ec2, keypair, s3} ...\n')
        print('A better aws cli experience with the help of fzf\n')
        print('positional arguments:')
        print('  {cform,ec2,keypair,s3}\n')
        print('optional arguments:')
        print('  -h, --help            show this help message and exit')
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
