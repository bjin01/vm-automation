#!/usr/bin/env python3

import yaml
import os
from xmlrpc.client import ServerProxy, Error
import salt.config
import salt.wheel
import subprocess


def delete_minion(minion_name):

    cmd = ["salt-key", "-q", "-y", "-d", minion_name]

    try:
        # Run the command and capture output (Python 3.6 compatible)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        print("Output:\n", result.stdout)
        if result.stderr:
            print("Error:\n", result.stderr)

    except Exception as e:
        print("An error occurred:", str(e))
    return True

