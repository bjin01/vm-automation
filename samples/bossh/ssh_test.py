#!/usr/bin/env python3

from paramiko import SSHClient
import paramiko
import sys
import time
import write_pillar
import create_ifcfg
import suma_actions

def test_ssh(hostname, suma_login):
    i = 1
    while i < 12:
        client = SSHClient()
        print "connecting"
        try:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname, username=suma_login['ssh-user'], password=suma_login['ssh-password'])
            print "connected"
            client.close()
            i = 1000000000000
        except paramiko.ssh_exception.NoValidConnectionsError:
            print("OK, the system seems to be not online, retrying... we give after 4 minutes. Hope your VM is started then.%s" %i)
            time.sleep(10)
            i += 1
    return