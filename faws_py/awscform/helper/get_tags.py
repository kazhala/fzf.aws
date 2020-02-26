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
