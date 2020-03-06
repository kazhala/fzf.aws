# terminate the selected instance
# @params
# $1: instance_id

function terminate_instance() {
  local instance_id="$1"
  get_confirmation "Instance will be terminated, continue?"
  if [[ "$confirm" == 'y' ]]; then
    aws ec2 terminate-instances --instance-ids "$instance_id" --output text
  fi
}
