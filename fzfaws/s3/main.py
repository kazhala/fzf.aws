"""main entry point for all s3 operations

process raw args passed from __main__.py and route
commands to appropriate sub functions
"""
import argparse
import json
import subprocess


def s3(raw_args):
    print('s3')
