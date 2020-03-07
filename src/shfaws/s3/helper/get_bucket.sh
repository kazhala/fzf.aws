#######################################
# get a bucket name from s3
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
#######################################
function get_bucket() {
  local bucket=$(aws s3 ls | fzf --exit-0 --select-1 | awk '{print $3}')
  echo "${bucket}"
}
