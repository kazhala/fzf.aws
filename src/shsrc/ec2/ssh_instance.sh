# ssh to selected ec2 instance
# or use to start the instance if the instance is stopped
# @params
# $1: instance_id
# $2: instance_status
# $3: instance_key_pem
# $4: instance_ip_address
# $5: pem dir, dir where the key pair is at
# $6: ami username of the ssh instance

function ssh_instance() {
  local instance_id="$1"
  local instance_status="$2"
  local instance_key_pem="$3"
  local instance_ip_address="$4"
  local key_pem_path="$5"
  local user_name="$6"
  # start the instance if it is stopped
  if [[ "$instance_status" == stopped ]]; then
    get_confirmation "Instance is currently stopped, start instance?"
    if [[ "$confirm" == 'y' ]]; then
      echo "Starting instance now.."
      aws ec2 start-instances --instance-ids "$instance_id" --output text
    fi
  elif [[ "$instance_status" == running ]]; then
    echo "Instance is running, ready to connect"
    # go to the folder where the key pem files are stored
    cd "$key_pem_path"
    # chec if key pem exists
    if [[ -f "$instance_key_pem" ]]; then
      ssh -i "$instance_key_pem" "$user_name"@"$instance_ip_address"
    else
      echo "Key pair not detected in the specified directory"
    fi
  else
    # exit if instance state is not running or stopped 
    echo "Instance is still $instance_status, please wait"
    exit 1
  fi
}
