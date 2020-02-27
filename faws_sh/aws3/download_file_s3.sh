# dowload a file from s3
# TODO: should make local home folder available?
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
  [[ "$search_from_root" == 'true' ]] && cd "$HOME"
  if [[ -z "$local_path" ]]; then
    local_path=$(search_file 'folder' '$hidden')
  fi
  if [[ -z "$local_path" ]]; then
    echo "File will be downloaded to directory $PWD"
    if [[ "$recursive" == 'true' ]]; then
      local_path="$PWD/"
    fi
  fi
  if [[ "$recursive" != 'true' ]]
  then
    aws s3 "$operation_cmd" "s3://$s3_path" "$local_path" --dryrun
  else
    aws s3 "$operation_cmd" "s3://$s3_path" "$local_path" --dryrun --recursive
  fi
  get_confirmation "Confirm?"
  # upload to s3
  if [[ "$confirm" == 'y' ]]
  then
    if [[ "$recursive" != 'true' ]]
    then
      aws s3 "$operation_cmd" "s3://$s3_path" "$local_path"
    else
      aws s3 "$operation_cmd" "s3://$s3_path" "$local_path" --recursive
    fi
  fi
  exit 0
}
