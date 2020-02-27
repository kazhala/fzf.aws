
# get local file path
# @params
# $1: 'folder', search for folder instead of file
function get_local_file() {
  # if not specifed through the -P path flag
  # search local files
  if [[ -z "$path_to_file" ]]
  then
    # if root flag specifed, go to root and search
    if [[ ! -z "$search_from_root" ]]
    then
      cd "$HOME"
    fi
    # popup fzf to select a file or dir based on flags
    # search for folders if parameter specifed
    if [[ "$1" != 'folder' ]]
    then
      search_file
    else
      search_file 'folder'
    fi
    # exit if no file selected
    [[ -z "$path_to_file" ]] && exit 1
    if [[ ! -z "$search_from_root" ]]
    then
      path_to_file="$HOME/$path_to_file"
    fi
  fi
}

# execute fzf to search the file
function search_file() {
  exe_fd=$(fd_exists)
  if [[ "$exe_fd" -eq 0 ]]
  then
    if [[ "$1" != 'folder' ]]
    then
      # if hidden flag, search for hidden file
      if [[ -z "$hidden" ]]
      then
        path_to_file=$(fd --type f | fzf)
      else
        path_to_file=$(fd --type f -H | fzf)
      fi
    else
      # if hidden flag, search for hidden dir
      if [[ -z "$hidden" ]]
      then
        path_to_file=$(fd --type d | fzf) 
      else
        path_to_file=$(fd --type d -H | fzf)
      fi
    fi
  else
    if [[ "$1" != 'folder' ]]
    then
      path_to_file=$(find * -type f | fzf)
    else
      path_to_file=$(find * -type d | fzf)
    fi
  fi
}
