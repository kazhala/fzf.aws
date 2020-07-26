# fzf :heart: aws

[![Test](https://github.com/kazhala/fzf.aws/workflows/Test/badge.svg)](https://github.com/kazhala/fzf.aws/actions?query=workflow%3ATest)
[![Lint](https://github.com/kazhala/fzf.aws/workflows/Lint/badge.svg)](https://github.com/kazhala/fzf.aws/actions?query=workflow%3ALint)
[![Travis](https://img.shields.io/travis/com/kazhala/fzf.aws/master?label=Travis&logo=travis)](https://travis-ci.com/github/kazhala/fzf.aws)
[![Coverage](https://img.shields.io/coveralls/github/kazhala/fzf.aws/master?label=Coverage&logo=coveralls)](https://coveralls.io/github/kazhala/fzf.aws?branch=master)
[![AWS CodeBuild](https://codebuild.ap-southeast-2.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoieWdVWHNJMFllT2JyVkZoSCtoNDNlZkVkK3ZsSEIwZDJHMFBFN21KWThsdk04enQxbnExa012Y01ZcVhXTjJOZTBld2lRSStMOXZEQnROQWVIRVpxVGFRPSIsIml2UGFyYW1ldGVyU3BlYyI6IjVTUEdveURkK2lzNTgyUVMiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)](https://github.com/kazhala/fzf.aws/blob/master/cloudformation.yml)

[![Package version](https://img.shields.io/pypi/v/fzfaws?label=PyPI)](https://pypi.org/project/fzfaws/)
[![Python version](https://img.shields.io/pypi/pyversions/fzfaws?label=Python)](https://pypi.org/project/fzfaws/)
[![Platform](https://img.shields.io/badge/Platform-linux%20%7C%20macos-lightgrey)](https://github.com/kazhala/fzf.aws/blob/master/fzfaws/utils/pyfzf.py#L52)
[![Code Lint: pyright](https://img.shields.io/badge/Code%20Lint-pyright-yellow)](https://github.com/microsoft/pyright)
[![Code Style: black](https://img.shields.io/badge/Code%20Style-black-black)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-MIT-green?label=License)](https://opensource.org/licenses/MIT)

**Note: still under development, may have breaking changes and bugs, use it under caution.**

![fzfaws demo](https://github.com/kazhala/gif/blob/master/fzfaws-demo.gif)

## About

`fzfaws` is a python utility to interact with aws on the command line through [fzf](https://github.com/junegunn/fzf) interface. The primary goal of this project
is to enhance the aws command line experience by reducing the number of times to travel between the browser and terminal to search
for aws-cli commands or even aws arn, id etc just for the sake of copy/pasting them for some simple operations.

`fzfaws` is still a young project and will continue to develop to support more services. Table below lists some of the high level view of the supported feature, there
are advanced flags for each individual operations. For example, EC2 ssh instance support tunnelling and most S3 operations take `--version` flag to operate on versioned objects.
Checkout [wiki](https://github.com/kazhala/fzf.aws/wiki) for detailed commands usage.

| Service         | Support                                                                                                                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| EC2             | ssh instance, start instance, stop instance, terminate instance, reboot instance, list instance/vpc related objects information                                                                  |
| S3              | upload files/directories, download files/directories, move objects/directories between buckets, update object attributes, delete objects, generate presign url, list objects/buckets information |
| CloudFormation  | create stack, update stack, create/execute changeset, detect drift, validate template, delete stack, list stack/resources information                                                            |
| Coming soon ... | Coming soon ...                                                                                                                                                                                  |

`fzfaws` is not developed as a replacement tool for `aws-cli` or any alternatives, it should be used in conjunction with them, hence it will not implement solution for all actions.
With that said, feature request are very welcome, I would like to discuss and consider them.

## Requirements

### System

`fzfaws` currently only has support for MacOS and Linux systems. For Windows system support, there will need some work to be done on the
[pyfzf](https://github.com/kazhala/fzf.aws/blob/master/fzfaws/utils/pyfzf.py) module as well as the [ssh_instance](https://github.com/kazhala/fzf.aws/blob/master/fzfaws/ec2/ec2.py)
module, PR welcome. You could always utilise the docker image of `fzfaws` on any system, checkout [wiki](https://github.com/kazhala/fzf.aws/wiki#docker-image) to consult how to use the image.
It should theoretically support Windows WSL, if you are getting error message please let me know.

### Python

`fzfaws` require Python version 3.6+ in order to function properly.

### Optional dependencies

- [aws-cli](https://github.com/aws/aws-cli): `fzfaws` uses `aws-cli` to perform s3 sync operations, only required if you want to use `fzfaws s3 upload --sync`.
- [fd](https://github.com/sharkdp/fd): improve local file search speed, `fzfaws` will use `fd` over `find` if `fd` is installed.

## Install

`fzfaws` comes with `fzf` binary, it doesn't require `fzf` to be installed. Main reason is to allow simple download
procedure even on remote instances.

```sh
pip3 install fzfaws
```

## Usage

Getting started guide and individual service guide are documented in [wiki](https://github.com/kazhala/fzf.aws/wiki).

- [General Usage](https://github.com/kazhala/fzf.aws/wiki)
- [EC2](https://github.com/kazhala/fzf.aws/wiki/EC2)
- [CloudFormation](https://github.com/kazhala/fzf.aws/wiki/CloudFormation)
- [S3](https://github.com/kazhala/fzf.aws/wiki/S3)

## Motivation & Background

`fzfaws` started off as a sets of bash scripts that I wrote to simplify the way I start/stop/terminate/ssh my ec2 instances.
I also implemented s3 functionalities afterwards because I want an easier way to search my bucket.
Later on I also decided to cover CloudFormation because I often need to update my IP parameter in some stacks which
I don't want to do it in aws console. Since I was learning Python, I decided to give it a go in Python because it can process YAML and JSON much easier.
You could find the half bash half Python version in [this](https://github.com/kazhala/fzf.aws/tree/archive/shell-version) branch.

As the scripts grow, I decided to make a dedicated project and re-write everything in Python. It was a great help for me to understand more
about aws and this project definitely took some positive impact (mainly ec2, s3, cloudformation) on my aws certification exams.

It's more of a learning project for me, it is also my first python package and I'm still learning stuff along the way,
some code style/implementation might drastically differ from others, I'm trying my best to refactor everything to align.

Leave a star :)

## Testing

`fzfaws` is fully tested using the unittest module, heavy mocking were implemented to thoroughly test the interaction with aws as well
as the fzf processing. Due to the limited data set on my personal aws account, I couldn't really test how `fzfaws` would
perform under extreme data load, please fire up issues if you face any.

## Related projects

- [aws-fuzzy-finder](https://github.com/pmazurek/aws-fuzzy-finder): A clean and well written project focus on ssh into EC2 instance.

## Credit

- credit to [fzf](https://github.com/junegunn/fzf).
- credit to [boto3](https://github.com/boto/boto3).
- credit to [aws-fuzzy-finder](https://github.com/pmazurek/aws-fuzzy-finder) for it's fzf-binary detection usage.
- credit to [this](https://stackoverflow.com/a/33350380) answer for the method to walk s3 folder.
