# terminate the selected instance
# @params
# $1: instance_id

function terminate_instance() {
  echo "Instance will be terminated"
  aws ec2 terminate-instances --instance-ids "$1" --dry-run
  get_confirmation
  if [[ "$confirm" == 'y' ]]; then
    aws ec2 terminate-instances --instance-ids "$1"
  fi
}
