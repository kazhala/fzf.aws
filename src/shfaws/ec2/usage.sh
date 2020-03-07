#######################################
# help message for ec2
# Globals:
#   None
# Arguments:
#   $1: action_command
# Outputs:
#   None
#######################################
function usage() {
  local action_command="$1"
  if [[ -z "$action_command" ]]; then
    echo -e "usage: faws ec2 [-h] {ssh,stop,terminate,ls,reboot} ...\n"
    echo -e "perform actions on the selected instance\n"
    echo -e "positional arguments:"
    echo -e "  {ssh,stop,terminate,ls,reboot}\n"
    echo -e "optional arguments:"
    echo -e "  -h\t\tshow this help message and exit"
  elif [[ "$action_command" == 'ssh' ]]; then
    echo -e "usage: faws ec2 ssh [-h] [-r] [-p] [-u]\n"
    echo -e "ssh into the selected instance\n"
    echo -e "optional arguments:"
    echo -e "  -h\t\tshow this help message and exit"
    echo -e "  -r\t\tselect a different region rather than using the default region"
    echo -e "  -p PATH\tspecify a different path than config for the location of the key pem file"
    echo -e "  -u NAME\tspecify a different username used to ssh into the instance, default is ec2-user"
  elif [[ "$action_command" == 'reboot' ]]; then
    echo -e "usage: faws ec2 reboot [-h] [-r] [-m]\n"
    echo -e "reboot the selected instance\n"
    echo -e "optional arguments:"
    echo -e "  -h\t\tshow this help message and exit"
    echo -e "  -r\t\tselect a different region rather than using the default region"
    echo -e "  -m\t\tenable multi select and reboot multiple instance at once"
  else
    echo -e "usage: faws ec2 $action_command [-h] [-r] [-w] [-m]\n"
    echo -e "$action_command the selected instance\n"
    echo -e "optional arguments:"
    echo -e "  -h\t\tshow this help message and exit"
    echo -e "  -r\t\tselect a different region rather than using the default region"
    echo -e "  -w\t\tpause the program and wait for instance $action_command complete"
    echo -e "  -m\t\tenable multi select and $action_command multiple instance at once"
  fi
}
