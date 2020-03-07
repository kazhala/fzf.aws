#######################################
# stop the selected instance/instances
# Globals:
#   None
# Arguments:
#   $1: instance_id
#   $2: wait_flag
#   $3: stop_hibernate
# Outputs:
#   None
#######################################
function stop_instance() {
  local instance_id="$1"
  local wait_flag="$2"
  local stop_hibernate="$3"
  get_confirmation "Instance will be stopped, continue?"
  if [[ "${confirm}" == 'y' ]]; then
    if [[ -z "${stop_hibernate}" ]]; then
      aws ec2 stop-instances --instance-ids ${instance_id} --output text
    else
      aws ec2 stop-instances --hibernate --instance-ids ${instance_id} --output text
    fi

    if [[ -n "${wait_flag}" ]]; then
      # wait for instance to be stopped
      echo "Waiting for instance to be stopped"
      aws ec2 wait instance-stopped --instance-ids ${instance_id}
      echo "Instance stopped"
    fi
  fi
}
