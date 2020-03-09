#######################################
# help message to display for faws s3
# Globals:
#   None
# Arguments:
#   $1: operation type
# Outputs:
#   None
#######################################
function usage() {
  local action_command="$1"
  if [[ -z "${action_command}" ]]; then
    echo -e "usage: faws s3 [-h] {upload,download,delete,bucket,presign} ...\n"
    echo -e "perform CRUD operation with cp/mv/rm in s3 bucket interactively"
    echo -e "without positional arguments, it will only print the selected item s3 path\n"
    echo -e "positional arguments:"
    echo -e "  {upload,download,delete,bucket,presign,ls}\n"
    echo -e "optional arguments:"
    echo -e "  -h\t\tshow this help message and exit"
  elif [[ "${action_command}" == 'bucket' ]]; then
    echo -e "usage: faws s3 bucket [-h] [-p] [-m] [-s] [-r] [-i] [-e]\n"
    echo -e "transfer file between buckets\n"
    echo -e "optional arguments:"
    echo -e "  -h\t\tshow this help message and exit"
    echo -e "  -p\t\tspecify a s3 path (bucketName/path) after this flag and skip s3 bucket/path selection"
    echo -e "  -m\t\tuse mv instead of cp command, like cut a file and paste in another bucket"
    echo -e "  -s\t\tuse sync instead of cp command, recursively copies new and updated files from one bucket to another"
    echo -e "  -r\t\toperate recursively, set this flag when manipulating folders"
  elif [[ "${action_command}" == 'delete' ]]; then
    echo -e "usage: faws s3 delete [-h] [-p] [-r]\n"
    echo -e "delete files on a s3 bucket, to delete folder, set -r flag\n"
    echo -e "optional arguments:"
    echo -e "  -h\t\tshow this help message and exit"
    echo -e "  -p PATH\t\tspecify a s3 path (bucketName/path) after this flag and skip s3 bucket/path selection"
    echo -e "  -r\t\toperate recursively, set this flag when manipulating folders"
  elif [[ "${action_command}" == 'ls' ]]; then
    echo -e "usage: faws s3 delete [-h]\n"
    echo -e "list all files in the selected bucket and get the s3 path on selection\n"
    echo -e "optional arguments:"
    echo -e "  -h\t\tshow this help message and exit"
  elif [[ "${action_command}" == 'presign' ]]; then
    echo -e "usage: faws s3 presign [-h] [-p] [-t]\n"
    echo -e "generate a temprary download url for the selected s3 object"
    echo -e "optional arguments:\n"
    echo -e "  -h\t\tshow this help message and exit"
    echo -e "  -p PATH\tspecify a s3 path (bucketName/path) after this flag and skip s3 bucket/path selection"
    echo -e "  -t TIME\tspecify the expire time of the url in seconds, default is 3600s"
  elif [[ "${action_command}" == 'upload' || "${action_command}" == 'download' ]]; then
    echo -e "usage: faws s3 "${action_command}" [-h] [-p] [-P] [-m] [-s] [-r] [-R] [-H]\n"
    echo -e "${action_command} from/to a selected bucket\n"
    echo -e "optional arguments:\n"
    echo -e "  -h\t\tshow this help message and exit"
    echo -e "  -p PATH\tspecify a s3 path (bucketName/path) after this flag and skip s3 bucket/path selection"
    echo -e "         \tE.g. -p bucketname or -p bucketname/path, don't put in the s3:// prefix"
    echo -e "  -P PATH\tspecify a local path for operation"
    echo -e "  -m\t\tuse mv instead of cp command, like cut a file and paste in another location"
    echo -e "  -s\t\tuse sync instead of cp command, recursively copies new and updated files from one directory to another"
    echo -e "  -r\t\toperate recursively, set this flag when manipulating folders"
    echo -e "  -R\t\tsearch local file from root directory, note: very slow if no fd installed"
    echo -e "  -H\t\tInclude hidden folder or directory during local file search"
  fi
}
