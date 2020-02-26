# ssh to selected ec2 instance
# @params
# $1: instance_key_pem
# $2: instance_ip_address
# $3: pem dir, dir where the key pair is at

function ssh_instance() {
  echo "Instance is running, ready to connect"
  # go to the folder where the key pem files are stored
  cd "$3"
  if [[ -f "$1" ]]
  then
    # ssh into the instance
    ssh -i "$1" ec2-user@"$2"
  else
    echo "Key pair not detected on this computer"
  fi
}
