#!/usr/bin/env bash
#
# set up test environment, get mock keys into aws profile

[[ ! -d "$HOME"/.aws ]] && mkdir "$HOME"/.aws
[[ -f "$HOME"/.aws/credentials ]] && rm "$HOME"/.aws/credentials
[[ -f "$HOME"/.aws/config ]] && rm "$HOME"/.aws/config
export AWS_DEFAULT_REGION="ap-southeast-2"

cat << EOF > "$HOME"/.aws/credentials
[default]
aws_access_key_id = 111111111"
aws_secret_access_key = 111111111"
[root]
aws_access_key_id = 111111111"
aws_secret_access_key = 111111111"
EOF

cat << EOF > "$HOME"/.aws/config
[default]
region = ap-southeast-2
[root]
region = ap-southeast-2
EOF
