#######################################
# display all instance through fzf and return the selected instance data
# Globals:
#   None
# Arguments:
#   $1: $action_command
#   $2: $selected_region
#   $3: $multi_select flag
# Outputs:
#   None
#######################################
function get_instance() {
  local selected_instance=''
  local action_command="$1"
  local selected_region="$2"
  local multi_select="$3"

  # if there is flag, meaning a region other than default is selected
  # request region specific ec2 or using default region
  if [[ -z "${selected_region}" ]]; then
    # set fzf -m flag if multi_select is set
    if [[ -z "${multi_select}" || "${action_command}" == 'ssh' ]]; then
      selected_instance=$(aws ec2 describe-instances \
          --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,Tags[?Key==`Name`]|[0].Value,KeyName,PublicDnsName]' \
          --output text | sed 's/\'$'\t/ | /g' | fzf --exit-0 | sed 's/\'$'\s//g' | awk -F '|' '{print $1 " " $2 " " $5 " " $6}')
    else
      selected_instance=$(aws ec2 describe-instances \
          --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,Tags[?Key==`Name`]|[0].Value,KeyName,PublicDnsName]' \
          --output text | sed 's/\'$'\t/ | /g' | fzf --exit-0 -m | sed 's/\'$'\s//g' | awk -F '|' '{print $1 " " $2 " " $5 " " $6}')
    fi
  else
    if [[ -z "${multi_select}" || "$action_command" == 'ssh' ]]; then
      selected_instance=$(aws ec2 describe-instances --region "${selected_region}" \
          --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,Tags[?Key==`Name`]|[0].Value,KeyName,PublicDnsName]' \
          --output text | sed 's/\'$'\t/ | /g' | fzf --exit-0 | sed 's/\'$'\s//g' | awk -F '|' '{print $1 " " $2 " " $5 " " $6}')
    else
      selected_instance=$(aws ec2 describe-instances --region "${selected_region}" \
          --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,Tags[?Key==`Name`]|[0].Value,KeyName,PublicDnsName]' \
          --output text | sed 's/\'$'\t/ | /g' | fzf --exit-0 -m | sed 's/\'$'\s//g' | awk -F '|' '{print $1 " " $2 " " $5 " " $6}')
    fi
  fi 
  echo "${selected_instance}"
}
