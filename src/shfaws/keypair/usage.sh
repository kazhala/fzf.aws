# help message for keypair

#######################################
# Help message for keypair
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   None
#######################################
function usage() {
  echo -e "usage: faws keypair [-h] ...\n"
  echo -e "Automate the keypair process after download"
  echo -e "It simply changes the permission of the keypairs in download folder"
  echo -e "And move it to the .ssh folder or any folder specified through faws configure\n"
  echo -e "optional arguments:"
  echo -e "  -h\t\tshow this help message and exit"
}
