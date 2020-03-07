#######################################
# get all region from aws ec2
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
#######################################
function get_region() {
  local selected_region=$(aws ec2 describe-regions --output text | awk '{print $4}' | fzf)
  echo "${selected_region}"
}
