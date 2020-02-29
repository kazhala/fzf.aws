# generate a presign url for the given s3 object
# @params
# $1: s3 object path
# $2: expires_in passed by user

function presign_url_s3() {
  local s3_path="$1"
  local expires_in="$2"
  if [[ -n "$expires_in" ]] && [ "$expires_in" -eq "$expires_in" ] 2>/dev/null
  then
    if [[ "$expires_in" -eq 0 ]]; then
      aws s3 presign "s3://$s3_path"
    else
      aws s3 presign "s3://$s3_path" --expires-in "$expires_in"
    fi
  else
    echo "number specified by [-U number] is not a number, please specify [0-9]"
    echo "using 0 will use the default timeout 3600s [-U 0]"
  fi
}
