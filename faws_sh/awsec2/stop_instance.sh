# stop the selected instance
# $1 {instance_id}
function stop_instance() {
  aws ec2 stop-instances --instance-ids "$1" --output text
}
