# help message for ec2
# @params
# $1: action_command

function usage() {
  local action_command="$1"
  if [[ -z "$action_command" ]]; then
    echo "usage: faws ec2 [-h] {ssh,stop,terminate,ls,reboot} ...\n"
    echo "perform actions on the selected instance\n"
    echo "positional arguments:"
    echo "  {ssh,stop,terminate,ls,reboot}\n"
    echo "optional arguments:"
    echo "  -h\t\tshow this help message and exit"
  elif [[ "$action_command" == 'ssh' ]]; then
    echo "usage: faws ec2 ssh [-h] [-r] [-p] [-u]\n"
    echo "ssh into the selected instance\n"
    echo "optional arguments:"
    echo "  -h\t\tshow this help message and exit"
    echo "  -r\t\tselect a different region rather than using the default region"
    echo "  -p PATH\tspecify a different path than config for the location of the key pem file"
    echo "  -u NAME\tspecify a different username used to ssh into the instance, default is ec2-user"
  elif [[ "$action_command" == 'reboot' ]]; then
    echo "usage: faws ec2 reboot [-h] [-r] [-m]\n"
    echo "reboot the selected instance\n"
    echo "optional arguments:"
    echo "  -h\t\tshow this help message and exit"
    echo "  -r\t\tselect a different region rather than using the default region"
    echo "  -m\t\tenable multi select and reboot multiple instance at once"
  else
    echo "usage: faws ec2 $action_command [-h] [-r] [-w] [-m]\n"
    echo "$action_command the selected instance\n"
    echo "optional arguments:"
    echo "  -h\t\tshow this help message and exit"
    echo "  -r\t\tselect a different region rather than using the default region"
    echo "  -w\t\tpause the program and wait for instance $action_command complete"
    echo "  -m\t\tenable multi select and $action_command multiple instance at once"
  fi
}
