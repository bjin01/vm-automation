"""
Written by Bo Jin
Github: https://github.com/jinbo01
Email: bo.jin@suseconsulting.ch

A test script to become familar with original VMware python SDK
"""
import requests
import urllib3
import sys, os
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter_client import VM

import getpass
from pprint import pprint
import argparse

session = requests.session()

# Disable cert verification for demo purpose. 
# This is not recommended in a production environment.
session.verify = False

# Disable the secure connection warning for demo purpose.
# This is not recommended in a production environment.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# password = getpass.getpass(prompt='Enter vCenter password: ')

# Connect to a vCenter Server using username and password
# Parse command line arguments
parser = argparse.ArgumentParser(description='vCenter VM search tool')
parser.add_argument('-s', '--server', required=True, help='vCenter server address')
parser.add_argument('-u', '--username', required=True, help='vCenter username')
parser.add_argument('-p', '--password', help='vCenter password')
args = parser.parse_args()

# Get password from environment variable or prompt if not provided
password = args.password or os.getenv('VCENTER_PASSWORD')
if not password:
    password = getpass.getpass(prompt='Enter vCenter password: ')

# Connect to a vCenter Server using username and password
vsphere_client = create_vsphere_client(server=args.server, username=args.username, password=password, session=session)

# List all VMs inside the vCenter Server
# all_vms = vsphere_client.vcenter.VM.list()


vm_name = input("Enter the VM name to search: ")
names = set([vm_name])
try:
    vms = vsphere_client.vcenter.VM.list(VM.FilterSpec(names=names))
except:
    print("failed to find it.")
    sys.exit(1)

if len(vms) == 0:
    print("VM with name ({}) not found".format(vm_name))
    sys.exit(1)

print(vms)
vm = vms[0].name
state = vms[0].power_state
print("Found VM '{}': {}".format(vm, state.lower()))
