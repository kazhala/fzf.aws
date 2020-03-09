#######################################
# delete a file or folder from s3
# Globals:
#   None
# Arguments:
#   $1: s3 path to upload
#   $2: recursive flag, optional
#   $3: wild_pattern
# Outputs:
#   None
#######################################
function delete_file_s3() {
  local operation_cmd='rm'
  local s3_path=$1
  local recursive=$2
  local wild_pattern=$3

  # dryrun and get confirmation
  if [[ -z "${recursive}" ]]; then
    aws s3 "${operation_cmd}" "s3://${s3_path}" --dryrun ${wild_pattern}
  else
    aws s3 "${operation_cmd}" "s3://${s3_path}" --dryrun --recursive ${wild_pattern}
  fi
  get_confirmation "Confirm?"

  # delete the file
  if [[ "${confirm}" == 'y' ]]; then
    if [[ -z "$recursive" ]]; then
      aws s3 "${operation_cmd}" "s3://${s3_path}" ${wild_pattern}
    else
      aws s3 "${operation_cmd}" "s3://${s3_path}" --recursive ${wild_pattern}
    fi
  fi
  exit 0
}
