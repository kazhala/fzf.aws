#######################################
# delete a file or folder from s3
# Globals:
#   None
# Arguments:
#   $1: s3 path to upload
#   $2: recursive flag, optional
# Outputs:
#   None
#######################################
function delete_file_s3() {
  local operation_cmd='rm'
  local s3_path=$1
  local recursive=$2

  # dryrun and get confirmation
  if [[ -z "${recursive}" ]]; then
    aws s3 "${operation_cmd}" "s3://${s3_path}" --dryrun
  else
    aws s3 "${operation_cmd}" "s3://${s3_path}" --dryrun --recursive
  fi
  get_confirmation "Confirm?"

  # delete the file
  if [[ "${confirm}" == 'y' ]]; then
    if [[ -z "$recursive" ]]; then
      aws s3 "${operation_cmd}" "s3://${s3_path}"
    else
      aws s3 "${operation_cmd}" "s3://${s3_path}" --recursive
    fi
  fi
  exit 0
}
