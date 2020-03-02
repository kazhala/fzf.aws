# terminate the selected instance
# @params
# $1: instance_id

function terminate_instance() {
  get_confirmation "Instance will be terminated, continue?"
  if [[ "$confirm" == 'y' ]]; then
    aws ec2 terminate-instances --instance-ids "$1" --output text
  fi
}
