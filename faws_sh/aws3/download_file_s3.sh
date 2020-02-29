# dowload a file from s3
# @params
# $1: operation_cmd cp/mv/rm
# $2: s3 path to upload
# $3: recursive flag
# $4: hidden flag
# $5: search from root flag
# $6: local path

function download_file_s3() {
  local operation_cmd=$1
  local s3_path=$2
  local recursive=$3
  local hidden=$4
  local search_from_root=$5
  local local_path=$6
  # perform from root if flag specified
  [[ "$search_from_root" == 'true' ]] && cd "$HOME"
  if [[ -z "$local_path" ]]; then
    # local_path can be empty, s3 will use current directory
    local_path=$(search_file 'folder' '$hidden')
  fi
  if [[ -z "$local_path" ]]; then
    # if recursive flag, local_path cannot be empty, s3 will give error
    if [[ "$recursive" == 'true' ]]; then
      local_path="$PWD/"
    fi
  fi
  echo "File will be downloaded to directory $PWD"

  # dryrun and get confirmation
  if [[ "$recursive" != 'true' || "$operation_cmd" == 'sync' ]]; then
    aws s3 "$operation_cmd" "s3://$s3_path" "$local_path" --dryrun
  else
    aws s3 "$operation_cmd" "s3://$s3_path" "$local_path" --dryrun --recursive
  fi
  get_confirmation "Confirm?"
  # download from s3
  if [[ "$confirm" == 'y' ]]
  then
    if [[ "$recursive" != 'true' || "$operation_cmd" == 'sync' ]]; then
      aws s3 "$operation_cmd" "s3://$s3_path" "$local_path"
    else
      aws s3 "$operation_cmd" "s3://$s3_path" "$local_path" --recursive
    fi
  fi
  exit 0
}
