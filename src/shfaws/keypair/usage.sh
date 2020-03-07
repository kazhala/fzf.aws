# help message for keypair

function usage() {
  echo "usage: faws keypair [-h] ...\n"
  echo "Automate the keypair process after download"
  echo "It simply changes the permission of the keypairs in download folder"
  echo "And move it to the .ssh folder or any folder specified through faws configure\n"
  echo "optional arguments:"
  echo "  -h\t\tshow this help message and exit"
}
