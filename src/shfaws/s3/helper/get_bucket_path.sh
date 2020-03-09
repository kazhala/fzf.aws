#######################################
# get the subdirectory path in the bucket to upload
# Globals:
#   None
# Arguments:
#   $1: bucket name
#   $2: action_command
#   $3: recursive_flag
# Outputs:
#   None
#######################################
function get_bucket_path() {
  local path="$1"
  local action_command="$2"
  local recursive="$3"

  # if download/delete and not recursive, get all files in s3
  # if recursive flag, we want the folder name instead of the file name
  if [[ "${action_command}" != 'upload' && -z "${recursive}" ]]; then
    local selected_path=$(aws s3 ls "$path" --recursive | fzf -m --exit-0 | awk -v bucket="${path}" '{print bucket "/" $4}')
    [[ -z "${selected_path}" ]] && return
    echo "${selected_path}"
  else
    # display options through fzf for better expereince and control
    local option="interactively: interactively select path through s3\n"
    option="${option}root: operate in bucket root\n"
    option="${option}input: manully input the path/name\n"
    option="${option}append: interactively select a path and then input a new path/name to append"
    # get the selected option
    local selected_option=$( echo -e "${option}" | \
        fzf | sed 's/://' | awk '{print $1}')
    # exit if no selection
    [[ -z "${selected_option}" ]] && return

    if [[ "${selected_option}" == 'interactively' || "${selected_option}" == 'append' ]]; then
      # interactively selected path
      while true
      do
        # grep PRE is filtering the folder in s3, remove all files entry
        selected_path=$(aws s3 ls "${path}" | grep PRE | \
          sed 's/^.*PRE/PRE/g' | fzf --exit-0 | awk '{print $2}')
        # append / on first iteration
        if [[ "${path}" == "$1" ]]
        then
          path="${path}/"
        fi
        [[ -z "${selected_path}" ]] && break
        path="${path}${selected_path}"
      done
      # if append option, ask user to append path
      if [[ "${selected_option}" == 'append' ]]; then
        read -p "Input the new path to append(newname or newpath/): " append_path
        path="${path}${append_path}"
      fi
    elif [[ "${selected_option}" == 'input' ]]
    then
      read -p "Input the path(newname or newpath/): " new_path
      path="${path}/${new_path}"
    fi
    echo "${path}"
  fi
}
