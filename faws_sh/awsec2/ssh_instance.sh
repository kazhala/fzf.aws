# ssh to selected ec2 instance
# or use to start the instance if the instance is stopped
# @params
# $1: instance_id
# $2: instance_status
# $3: instance_key_pem
# $4: instance_ip_address
# $5: pem dir, dir where the key pair is at

function ssh_instance() {
  # start the instance if it is stopped
  if [[ "$2" == stopped ]]; then
    get_confirmation "Instance is currently stopped, start instance?"
    if [[ "$confirm" == 'y' ]]; then
      echo "Starting instance now.."
      aws ec2 start-instances --instance-ids "$1" --output text
    fi
  elif [[ "$2" == running ]]; then
    echo "Instance is running, ready to connect"
    # go to the folder where the key pem files are stored
    cd "$5"
    # chec if key pem exists
    if [[ -f "$3" ]]; then
      ssh -i "$3" ec2-user@"$4"
    else
      echo "Key pair not detected on this computer"
    fi
  else
    # exit if instance state is not running or stopped 
    echo "Instance is still $2, please wait"
    exit 1
  fi
}
