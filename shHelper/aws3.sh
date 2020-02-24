# aws3 helper functions

function get_local_file() {
  if [[ -z "$path_to_file" ]]
  then
    if [[ ! -z "$search_from_root" ]]
    then
      cd "$HOME"
    fi
    # popup fzf to select a file or dir based on flags
    if [[ "$1" != 'folder' ]]
    then
      if [[ -z "$hidden" ]]
      then
        path_to_file=$(fd --type f | fzf)
      else
        path_to_file=$(fd --type f -H | fzf)
      fi
    else
      if [[ -z "$hidden" ]]
      then
        path_to_file=$(fd --type d | fzf) 
      else
        path_to_file=$(fd --type d -H | fzf)
      fi
    fi
    # exit if no file selected
    [[ -z "$path_to_file" ]] && exit 1
    if [[ ! -z "$search_from_root" ]]
    then
      path_to_file="$HOME/$path_to_file"
    fi
  fi
}
