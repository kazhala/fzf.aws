# stop the selected instance
# @params
# $1: instance_id
# $2: instance_status
# $3: wait_flag


function stop_instance() {
  local instance_id="$1"
  local instance_status="$2"
  local wait_flag="$3"
  if [[ "$instance_status" == stopped ]]; then
    echo "Instance is already stopped"
  # stpp the instance if it is running
  elif [[ "$instance_status" == running ]]; then
    get_confirmation "Instance will be stopped, continue?"
    if [[ $confirm == 'y' ]]; then
      aws ec2 stop-instances --instance-ids "$instance_id" --output text
      if [[ "$wait_flag" == 'true' ]]; then
        echo "Waiting for instance to be stopped"
        aws ec2 wait instance-stopped --instance-ids "$instance_id"
        echo "Instance stopped"
      fi
    fi
  else
    # exit if instance state is not running or stopped 
    echo "Instance is still $instance_status, please wait"
    exit 1
  fi
}
