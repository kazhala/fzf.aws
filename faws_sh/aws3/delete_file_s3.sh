# delete a file or folder from s3
# @params
# $1: s3 path to upload
# $2: recursive flag, optional

function delete_file_s3() {
  local operation_cmd='rm'
  local s3_path=$1
  local recursive=$2
  if [[ "$recursive" != 'true' ]]
  then
    aws s3 "$operation_cmd" "s3://$s3_path" --dryrun
  else
    aws s3 "$operation_cmd" "s3://$s3_path" --dryrun --recursive
  fi
  get_confirmation "Confirm?"
  if [[ "$confirm" == 'y' ]]
  then
    if [[ -z "$recursive" ]]
    then
      aws s3 "$operation_cmd" "s3://$s3_path"
    else
      aws s3 "$operation_cmd" "s3://$s3_path"
    fi
  fi
  exit 0
}
