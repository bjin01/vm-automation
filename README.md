[![Build Status](https://travis-ci.org/vmware/pyvmomi-community-samples.svg?branch=master)](https://travis-ci.org/vmware/pyvmomi-community-samples) 

VMware VM - clone VM Automation 
=========================

This project is derived from pyvmomi-community-samples with additional scripts added by me.
The added scripts are mainly using ssh modules from python paramiko to execute several steps via ssh remote commands
The scripts must run on SUSE Manager host as the api call to SUSE Manager happens on the local host.

## Motivation:
Although there are other possibilities to automate new VM creation as terraform, salt-cloud, autoyast, cloud-init etc. in particular cases create a VM from template with further specific changes like hostname, fqdn, ip for several ethernet cards etc. need to be done depending on customer needs. The complex requirements could cause hitting bugs in the "standard technologies" where certain config or api is not designed to do so. Therefore I ended up to do my own scripts. 

salt-cloud has been tested but not working properly with pyvmomi so we had to look other alternatives.

## Main functions:
- Use clone_vm.py to create cloned VM.
- Onece VM cloned we have to rename it, create ifcfg files for all network interfaces and delete existing salt-minion from SUSE Manager, re-generate machine-id to avoid system registration conflict.
- finally we also set the vm uuid with the new hostname as salt pillar for further processing with salt.
- renamed system will be rebooted, the new salt-minion key must be accepted on salt-master respective on suse manager host which could be automated with auto-accept or salt reactors.

## Usage:

You can run the below script with given parameter for the NEW cloned VM with a given hostname. The hostname can be short or fqdn. All other parameters must be provided from a config file in ```/root/suma_config.yaml``` in yaml format.

The desired NEW system networks need to be specified in another yaml file which path is defined in /root/suma_config.yaml Look at sample config: 
```
./samples/bossh/config-network.yaml
```

```
python3 exec_script.py hostx.mydomain.io
```
