# get new tags for stacks during update or create
def get_tags():
    tag_list = []
    print('Tags help you identify your sub resources')
    print('A "Name" tag is suggested to enter at the very least')
    print('Skip enter value to stop entering for tags')
    while True:
        tag_name = input('TagName: ')
        if not tag_name:
            break
        tag_value = input('TagValue: ')
        if not tag_value:
            break
        tag_list.append({'Key': tag_name, 'Value': tag_value})
    return tag_list


def update_tags(tags):
    # update existing tags
    new_tags = []
    print('--------------------------------------------------------------------------------')
    print('Update tags')
    print('Skip the value to use previouse value')
    print('Enter delete in both field to remove a tag')
    for tag in tags:
        tag_key = input(f"Key({tag['Key']}): ")
        if not tag_key:
            tag_key = tag['Key']
        tag_value = input(f"Value({tag['Value']}): ")
        if not tag_value:
            tag_value = tag['Value']
        if tag_key == 'delete' and tag_value == 'delete':
            continue
        new_tags.append(
            {'Key': tag_key, 'Value': tag_value})
    return new_tags
