# stop the selected instance
# @params
# $1: instance_id
# $2: instance_status

function stop_instance() {
  if [[ "$2" == stopped ]]; then
    echo "Instance is already stopped"
  # stpp the instance if it is running
  elif [[ "$2" == running ]]; then
    get_confirmation
    if [[ $confirm == 'y' ]]; then
      aws ec2 stop-instances --instance-ids "$1" --output text
    fi
  else
    # exit if instance state is not running or stopped 
    echo "Instance is still $2, please wait"
    exit 1
  fi
}
