# common helper function to search for local file or local directory
# @params
# $1: folder/file if folder search folder else search file
# $2: include hidden file for fd commands?

# execute fzf to search the file
function search_file() {
  local file_type=$1
  local hidden=$2
  local exe_fd=$(fd_exists)
  local local_path=''

  # if fd command exists, use fd otherwise use find
  if [[ "$exe_fd" -eq 0 ]]
  then
    if [[ "$file_type" != 'folder' ]]
    then
      # if hidden flag, search for hidden file
      if [[ "$hidden" != 'true' ]]
      then
        local_path=$(fd --type f | fzf)
      else
        local_path=$(fd --type f -H | fzf)
      fi
    else
      # if hidden flag, search for hidden dir
      if [[ "$hidden" != 'true' ]]
      then
        local_path=$(fd --type d | fzf) 
      else
        local_path=$(fd --type d -H | fzf)
      fi
    fi
  else
    if [[ "$file_type" != 'folder' ]]
    then
      local_path=$(find * -type f | fzf)
    else
      local_path=$(find * -type d | fzf)
    fi
  fi
  echo "$local_path"
}

# check if fd exists, if not, use find instead
function fd_exists() {
  fd -V &>/dev/null
  echo "$?"
}
