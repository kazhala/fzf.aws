#######################################
# execute fzf to search the file
# Globals:
#   None
# Arguments:
#   $1: folder/file if folder search folder else search file
#   $2: include hidden file for fd commands?
# Outputs:
#   local_path: local file path
#######################################
function search_file() {
  local file_type=$1
  local hidden=$2
  local exe_fd="$(fd_exists)"
  local local_path=''

  # if fd command exists, use fd otherwise use find
  if [[ "${exe_fd}" -eq 0 ]]
  then
    if [[ "${file_type}" != 'folder' ]]
    then
      # if hidden flag, search for hidden file
      if [[ -z "${hidden}" ]]
      then
        local_path="$(fd --type f | fzf -m --exit-0)"
      else
        local_path="$(fd --type f -H | fzf -m --exit-0)"
      fi
    else
      # if hidden flag, search for hidden dir
      if [[ -z "${hidden}" ]]
      then
        local_path="$(fd --type d | fzf --exit-0)"
      else
        local_path="$(fd --type d -H | fzf --exit-0)"
      fi
    fi
  else
    if [[ "${file_type}" != 'folder' ]]
    then
      local_path="$(find * -type f | fzf -m --exit-0)"
    else
      local_path="$(find * -type d | fzf --exit-0)"
    fi
  fi
  echo "${local_path}"
}

# check if fd exists, if not, use find instead
function fd_exists() {
  fd -V &>/dev/null
  echo "$?"
}
