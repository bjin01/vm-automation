[![Build Status](https://travis-ci.org/vmware/pyvmomi-community-samples.svg?branch=master)](https://travis-ci.org/vmware/pyvmomi-community-samples) 

VMware VM - clone VM Automation 
=========================

This project is derived from pyvmomi-community-samples with additional scripts added by me.

Main function:
- Use clone_vm.py to create cloned VM.
- One VM cloned we have to rename it and add additional networks and re-generate machine-id
- finally we also set the vm uuid with the new hostname as salt pillar for further processing.
- renamed system will be rebooted, the new salt-minion key must be accepted on salt-master respective on suse manager host.

