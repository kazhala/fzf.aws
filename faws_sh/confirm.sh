# confirmation helper
function get_confirmation() {
  unset confirm
  while [[ "$confirm" != 'y'  && "$confirm" != 'n' ]]
  do
    read -p "Confirm?(y/n): " confirm
  done
}
