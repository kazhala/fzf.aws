#######################################
# reboot the selected instance
# Globals:
#   None
# Arguments:
#   $1: instance_id
# Outputs:
#   None
#######################################
function reboot_instance() {
  local instance_id="$1"
  local wait_flag="$2"
  get_confirmation "Instance will be rebooted, continue?"
  if [[ "${confirm}" == 'y' ]]; then
    aws ec2 reboot-instances --instance-ids ${instance_id} --output text
    echo "Instance is being placed in the reboot queue"
    echo "It may take aws up to 4mins before it is rebooted, instance will remain in running state"
  fi
}
