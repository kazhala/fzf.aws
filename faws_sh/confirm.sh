# confirmation helper
# @params
# $1: message to show
function get_confirmation() {
  unset confirm
  while [[ "$confirm" != 'y'  && "$confirm" != 'n' ]]
  do
    read -p "$1(y/n): " confirm
  done
}
