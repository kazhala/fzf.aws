# create/view changeset of the cloudformations stakcs
import boto3


def changeset_stack(args, stack_name, stack_details):
    print(stack_name)
