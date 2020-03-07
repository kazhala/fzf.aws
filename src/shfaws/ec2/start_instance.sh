#######################################
# start the selected instance/instances
# Globals:
#   None
# Arguments:
#   $1: instance_id
#   $2: wait flag
# Outputs:
#   None
#######################################
function start_instance() {
  local instance_id="$1"
  local wait_flag="$2"
  get_confirmation "Instance will be started, continue?"
  if [[ "${confirm}" == 'y' ]]; then
    echo "Starting instance now.."
    aws ec2 start-instances --instance-ids ${instance_id} --output text
    if [[ -n "${wait_flag}" ]]; then
      echo "Waiting for instance to be ready.."
      aws ec2 wait instance-running --instance-ids ${instance_id}
      echo "Instance is ready, run faws ec2 ssh to connect"
    fi
  fi
}
