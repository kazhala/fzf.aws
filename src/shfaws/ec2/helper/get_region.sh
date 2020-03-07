# get all region from aws ec2
function get_region() {
  local selected_region=$(aws ec2 describe-regions --output text | awk '{print $4}' | fzf)
  echo "$selected_region"
}
