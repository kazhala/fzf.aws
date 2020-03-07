#######################################
# terminate the selected instance/instances
# Globals:
#   None
# Arguments:
#   $1: instance_id
#   $2: wait_flag
# Outputs:
#   None
#######################################
function terminate_instance() {
  local instance_id="$1"
  local wait_flag="$2"
  get_confirmation "Instance will be terminated, continue?"
  if [[ "${confirm}" == 'y' ]]; then
    aws ec2 terminate-instances --instance-ids ${instance_id} --output text
    if [[ -n "${wait_flag}" ]]; then
      # wait for instance to be stopped
      echo "Waiting for instance to be terminated"
      aws ec2 wait instance-terminated --instance-ids ${instance_id}
      echo "Instance terminated"
    fi
  fi
}
