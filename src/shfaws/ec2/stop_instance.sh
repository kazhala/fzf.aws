# stop the selected instance
# @params
# $1: instance_id
# $3: wait_flag

function stop_instance() {
  local instance_id="$1"
  local wait_flag="$2"
  get_confirmation "Instance will be stopped, continue?"
  if [[ "$confirm" == 'y' ]]; then
    aws ec2 stop-instances --instance-ids $instance_id --output text
    if [[ -n "$wait_flag" ]]; then
      # wait for instance to be stopped
      echo "Waiting for instance to be stopped"
      aws ec2 wait instance-stopped --instance-ids $instance_id
      echo "Instance stopped"
    fi
  fi
}
