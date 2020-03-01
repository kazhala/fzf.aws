# help message to display for aws3
# @params
# $1: operation type

# help message
function usage() {
  local operation_type="$1"
  if [[ -z "$operation_type" ]]; then
    echo "usage: aws3 [-h] {upload,download,delete,bucket,presign} ...\n"
    echo "perform CRUD operation with cp/mv/rm in s3 bucket interactively"
    echo "without positional arguments, it will only print the selected item s3 path\n"
    echo "positional arguments:"
    echo "  {upload,download,delete,bucket,presign}\n"
    echo "optional arguments:"
    echo "  -h\t\tshow this help message and exit"
  elif [[ "$operation_type" == 'bucket' ]]; then
    echo "usage: aws3 bucket [-h] [-p] [-m] [-s] [-r]\n"
    echo "transfer file between buckets\n"
    echo "optional arguments:"
    echo "  -h\t\tshow this help message and exit"
    echo "  -p\t\tspecify a s3 path (bucketName/path) after this flag and skip s3 bucket/path selection"
    echo "  -m\t\tuse mv instead of cp command, like cut a file and paste in another bucket"
    echo "  -s\t\tuse sync instead of cp command, recursively copies new and updated files from one bucket to another"
    echo "  -r\t\toperate recursively, set this flag when manipulating folders"
  elif [[ "$operation_type" == 'delete' ]]; then
    echo "usage: aws3 delete [-h] [-p] [-r]\n"
    echo "delete files on a s3 bucket, to delete folder, set -r flag\n"
    echo "optional arguments:"
    echo "  -h\t\tshow this help message and exit"
    echo "  -p\t\tspecify a s3 path (bucketName/path) after this flag and skip s3 bucket/path selection"
    echo "  -r\t\toperate recursively, set this flag when manipulating folders"
  elif [[ "$operation_type" == 'upload' || "$operation_type" == 'download' ]]; then
    echo "usage: aws3 upload [-h] [-p] [-P] [-m] [-s] [-r] [-R] [-H]\n"
    echo "$operation_type from/to a selected bucket\n"
    echo "optional arguments:\n"
    echo "  -h\tshow this help message and exit"
    echo "  -p\tspecify a s3 path (bucketName/path) after this flag and skip s3 bucket/path selection"
    echo "  \tE.g. -p bucketname or -p bucketname/path, don't put in the s3:// prefix"
    echo "  -P\tspecify a local path for operation"
    echo "  -m\tuse mv instead of cp command, like cut a file and paste in another location"
    echo "  -s\tuse sync instead of cp command, recursively copies new and updated files from one directory to another"
    echo "  -r\toperate recursively, set this flag when manipulating folders"
    echo "  -R\tsearch local file from root directory, note: very slow if no fd installed"
    echo "  -H\tInclude hidden folder or directory during local file search"
  fi
}
