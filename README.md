# fzf :heart: aws

[![unittest](https://github.com/kazhala/fzf.aws/workflows/Test/badge.svg)](https://github.com/kazhala/fzf.aws/actions?query=workflow%3ATest)
[![lint](https://github.com/kazhala/fzf.aws/workflows/Lint/badge.svg)](https://github.com/kazhala/fzf.aws/actions?query=workflow%3ALint)
[![codebuild](https://codebuild.ap-southeast-2.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoieWdVWHNJMFllT2JyVkZoSCtoNDNlZkVkK3ZsSEIwZDJHMFBFN21KWThsdk04enQxbnExa012Y01ZcVhXTjJOZTBld2lRSStMOXZEQnROQWVIRVpxVGFRPSIsIml2UGFyYW1ldGVyU3BlYyI6IjVTUEdveURkK2lzNTgyUVMiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)](https://github.com/kazhala/fzf.aws/blob/master/cloudformation.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![package version](https://img.shields.io/pypi/v/fzfaws)](https://pypi.org/project/fzfaws/)
[![python version](https://img.shields.io/pypi/pyversions/fzfaws)](https://pypi.org/project/fzfaws/)
[![platform](https://img.shields.io/badge/platform-linux%20%7C%20macos-lightgrey)](https://github.com/kazhala/fzf.aws/blob/master/fzfaws/utils/pyfzf.py#L52)
[![license](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)

`fzfaws` is a python utility to interact with aws on the command line through [fzf](https://github.com/junegunn/fzf) interface. The primary goal of this project
is to enhance the experience while interacting with aws on the command line by reducing the number of times to travel between the browser and terminal to search
for aws-cli commands or even aws arn, id etc just for the sake of copy/pasting them for some simple operations.

**Note: still under development, expect breaking changes and bugs.**

![fzfaws demo](https://github.com/kazhala/gif/blob/master/fzfaws-demo.gif)
