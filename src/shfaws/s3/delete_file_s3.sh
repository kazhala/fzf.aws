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

  while IFS= read -r line; do
    # dryrun and get confirmation
    if [[ -z "${recursive}" ]]; then
      aws s3 "${operation_cmd}" "s3://${line}" --dryrun ${wild_pattern}
    else
      aws s3 "${operation_cmd}" "s3://${line}" --dryrun --recursive ${wild_pattern}
    fi
  done <<< "${s3_path}"

  get_confirmation "Confirm?"

  while IFS= read -r line; do
    # delete the file
    if [[ "${confirm}" == 'y' ]]; then
      if [[ -z "$recursive" ]]; then
        aws s3 "${operation_cmd}" "s3://${line}" ${wild_pattern}
      else
        aws s3 "${operation_cmd}" "s3://${line}" --recursive ${wild_pattern}
      fi
    fi
  done <<< "${s3_path}"
  exit 0
}

