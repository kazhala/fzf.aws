#######################################
# generate a presign url for the given s3 object
# Globals:
#   None
# Arguments:
#   $1: s3 object path
#   $2: expires_in passed by user
# Outputs:
#   None
#######################################
function presign_url_s3() {
  local s3_path="$1"
  local expires_in="$2"

  # using single bracket to test -eq to make sure string not convert to zero
  # want error to apper in this case
  if [[ -n "${expires_in}" ]] && [ "${expires_in}" -eq "${expires_in}" ] 2>/dev/null
  then
    while IFS= read -r line; do
      # if 0, use default timeout 3600seconds
      if [[ "${expires_in}" -eq 0 ]]; then
        aws s3 presign "s3://${line}"
      else
        aws s3 presign "s3://${line}" --expires-in "${expires_in}"
      fi
    done <<< "${s3_path}"
  else
    echo "number specified by [-U number] is not a number, please specify [0-9]"
    echo "using 0 will use the default timeout 3600s [-U 0]"
  fi
}
