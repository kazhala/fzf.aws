# stop the selected instance
# @params
# $1: instance_id
# $instance_status: instance_status

function stop_instance() {
  local instance_id="$1"
  local instance_status="$2"
  if [[ "$instance_status" == stopped ]]; then
    echo "Instance is already stopped"
  # stpp the instance if it is running
  elif [[ "$instance_status" == running ]]; then
    get_confirmation "Instance will be stopped, continue?"
    if [[ $confirm == 'y' ]]; then
      aws ec2 stop-instances --instance-ids "$instance_id" --output text
    fi
  else
    # exit if instance state is not running or stopped 
    echo "Instance is still $instance_status, please wait"
    exit 1
  fi
}
