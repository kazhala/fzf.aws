# display all instance through fzf and return the selected instance data
# @params
# $1 $selected_region
# $2 $multi_select flag

function get_instance() {
  local selected_instance=''
  local selected_region="$1"
  local multi_select="$2"
  # if there is flag, meaning a region other than default is selected
  # request region specific ec2 or using default region
  if [[ -z "$selected_region" ]]; then
    if [[ -z "$multi_select" ]]; then
      selected_instance=$(aws ec2 describe-instances \
          --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,Tags[?Key==`Name`]|[0].Value,KeyName,PublicDnsName]' \
          --output text | sed 's/\'$'\t/ | /g' | fzf --exit-0 | sed 's/\'$'\s//g' | awk -F '|' '{print $1 " " $2 " " $5 " " $6}')
    else
      selected_instance=$(aws ec2 describe-instances \
          --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,Tags[?Key==`Name`]|[0].Value,KeyName,PublicDnsName]' \
          --output text | sed 's/\'$'\t/ | /g' | fzf --exit-0 -m | sed 's/\'$'\s//g' | awk -F '|' '{print $1 " " $2 " " $5 " " $6}')
    fi
  else
    if [[ -z "$multi_select" ]]; then
      selected_instance=$(aws ec2 describe-instances --region "$selected_region" \
          --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,Tags[?Key==`Name`]|[0].Value,KeyName,PublicDnsName]' \
          --output text | sed 's/\'$'\t/ | /g' | fzf --exit-0 | sed 's/\'$'\s//g' | awk -F '|' '{print $1 " " $2 " " $5 " " $6}')
    else
      selected_instance=$(aws ec2 describe-instances --region "$selected_region" \
          --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType,Tags[?Key==`Name`]|[0].Value,KeyName,PublicDnsName]' \
          --output text | sed 's/\'$'\t/ | /g' | fzf --exit-0 -m | sed 's/\'$'\s//g' | awk -F '|' '{print $1 " " $2 " " $5 " " $6}')
    fi
  fi 
  echo "$selected_instance"
}
