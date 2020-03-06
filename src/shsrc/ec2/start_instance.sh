# start the selected instance
# @params
# $1: instance_id
# $2: instance_status
# $3: wait flag

function start_instance() {
  local instance_id="$1"
  local instance_status="$2"
  local wait_flag="$3"
  if [[ "$instance_status" == stopped ]]; then
    get_confirmation "Instance is currently stopped, start instance?"
    if [[ "$confirm" == 'y' ]]; then
      echo "Starting instance now.."
      aws ec2 start-instances --instance-ids "$instance_id" --output text
      if [[ "$wait_flag" == 'true' ]]; then
        echo "Waiting for instance to be ready.."
        aws ec2 wait instance-running --instance-ids "$instance_id"
        echo "Instance is ready, run faws ec2 ssh to connect"
      fi
    fi
  elif [[ "$instance_status" == running ]]; then
    echo "Instance already running, run faws ec2 ssh to connect"
  else
    # exit if instance state is not running or stopped 
    echo "Instance is still $instance_status, please wait"
    exit 1
  fi
}
