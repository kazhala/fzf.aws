#######################################
# download a file from s3
# Globals:
#   None
# Arguments:
#   $1: operation_cmd cp/mv/rm
#   $2: s3 path to download
#   $3: recursive flag
#   $4: hidden flag
#   $5: search from root flag
#   $6: local path
#   $7: wild_pattern
# Outputs:
#   None
#######################################
function download_file_s3() {
  local operation_cmd=$1
  local s3_path=$2
  local recursive=$3
  local hidden=$4
  local search_from_root=$5
  local local_path=$6
  local wild_pattern=$7

  # perform from root if flag specified
  [[ -n "${search_from_root}" ]] && cd "${HOME}"
  if [[ -z "${local_path}" ]]; then
    # local_path can be empty, s3 will use current directory
    local_path=$(search_file 'folder' "${hidden}")
  fi
  if [[ -z "${local_path}" ]]; then
    # if recursive flag, local_path cannot be empty, s3 will give error
    if [[ -n "${recursive}" ]]; then
      local_path="${PWD}/"
    fi
  fi
  echo "File will be downloaded to directory ${PWD}"

  while IFS= read -r line; do
    # dryrun and get confirmation
    # sync doesn't accpet recursive flag, it perform recursive by default
    if [[ -z "${recursive}" || "${operation_cmd}" == 'sync' ]]; then
      aws s3 "${operation_cmd}" "s3://${line}" "${local_path}" --dryrun ${wild_pattern}
    else
      aws s3 "${operation_cmd}" "s3://${line}" "${local_path}" --dryrun --recursive ${wild_pattern}
    fi
  done <<< "${s3_path}"
  get_confirmation "Confirm?"
  while IFS= read -r line; do
    # download from s3
    if [[ "${confirm}" == 'y' ]]
    then
      if [[ -z "${recursive}" || "${operation_cmd}" == 'sync' ]]; then
        aws s3 "${operation_cmd}" "s3://${s3_path}" "${local_path}" ${wild_pattern}
      else
        aws s3 "${operation_cmd}" "s3://${s3_path}" "${local_path}" --recursive ${wild_pattern}
      fi
    fi
  done <<< "${s3_path}"
  exit 0
}
