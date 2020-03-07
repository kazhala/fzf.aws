#######################################
# confirmation helper
# Globals:
#   ${confirm}: y/n the result of the confirmation
# Arguments:
#   $1: message to show
# Outputs:
#   None
#######################################
function get_confirmation() {
  unset confirm
  while [[ "${confirm}" != 'y'  && "${confirm}" != 'n' ]]
  do
    read -p "$1(y/n): " confirm
  done
}
