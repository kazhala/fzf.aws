"""ssh into the instance

perform ssh operation
"""
from fzfaws.ec2.ec2 import EC2


def ssh_instance(args):
    """function to handle ssh operation intot the ec2 instance

    Args:
        args: argparse args
    Returns:
        None
    """
    ec2 = EC2()
    ec2.get_ec2_region()
    ec2.get_ec2_instance()
    print(ec2.instance)
