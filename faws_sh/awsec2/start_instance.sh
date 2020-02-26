# start the selected instance
# @params
# $1 {instance_id}
mydir="${0%/*}"
source "$mydir"/faws_sh/confirm.sh

function start_instance() {
  echo "Instance is currently stopped, start instance?"
  get_confirmation
  if [[ "$confirm" == 'y' ]]
  then
    echo "Starting instance now.."
    aws ec2 start-instances --instance-ids "$1" --output text
  fi
}
