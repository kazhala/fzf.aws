import boto3

cloudformation = boto3.client('cloudformation')


def delete_stack(stack_name):
    confirm = None
    while confirm != 'y' and confirm != 'n':
        confirm = input(
            f"Are you sure you want to delete the stack '{stack_name}'(y/n): ").lower()
    if confirm == 'n':
        exit()
    else:
        response = cloudformation.delete_stack(StackName=stack_name)
        print(response)
