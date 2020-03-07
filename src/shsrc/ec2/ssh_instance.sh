# ssh into the selected ec2 instance
# @params
# $1: instance_status
# $2: instance_key_pem
# $3: instance_ip_address
# $4: pem dir, dir where the key pair is at
# $5: ami username of the ssh instance

function ssh_instance() {
  local instance_status="$1"
  local instance_key_pem="$2"
  local instance_ip_address="$3"
  local key_location="$4"
  local user_name="$5"
  # start the instance if it is stopped
  if [[ "$instance_status" == stopped ]]; then
    echo "Instance is currently stopped, run faws ec2 start to start the instance"
  elif [[ "$instance_status" == running ]]; then
    echo "Instance is running, ready to connect"
    # go to the folder where the key pem files are stored
    cd "$key_location"
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
