# reboot the selected instance
# @params
# $1: instance_id

function reboot_instance() {
  local instance_id="$1"
  local wait_flag="$2"
  get_confirmation "Reboot instance?"
  if [[ "$confirm" == 'y' ]]; then
    aws ec2 reboot-instances --instance-ids "$instance_id" --output text
    echo "Instance is being placed in the reboot queue"
  fi
}
