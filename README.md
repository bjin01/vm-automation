[![Build Status](https://travis-ci.org/vmware/pyvmomi-community-samples.svg?branch=master)](https://travis-ci.org/vmware/pyvmomi-community-samples) 

VMware VM - clone VM Automation 
=========================

This project is derived from [pyvmomi-community-samples](https://github.com/vmware/pyvmomi-community-samples) with additional scripts added by me.
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

## Requirements on SUSE Manager host:
* install the latest python module pyvmomi using pip. [pyVmomi](https://pypi.org/project/pyvmomi/) is the Python SDK for the VMware vSphere API that allows you to manage ESX, ESXi, and vCenter.
```
sudo pip install pyvmomi
sudo pip install --upgrade pyvmomi
```
To check pyvmomi version that is installed on your system:
```
sudo python3.6 -m pip list | grep -i pyvmomi
```

* install the latest python module [paramiko](https://pypi.org/project/paramiko/) for remote command execution via ssh
```
sudo python3 -m pip install --upgrade paramiko
```
To check the installed version of paramiko:
```
sudo python3 -m pip list | grep -i paramiko
```
* git clone this repo to your SUSE Manager host
```
mkdir myrepo
cd myrpo
git clone https://github.com/bjin01/vm-automation.git
git remote remove origin
```
* Create those files:
```
mkdir -p /srv/pillar/change-hostname
echo "myservers_uuid:" > /srv/pillar/change-hostname/init.sls

mkdir -p /srv/pillar/mynetworks/
touch /srv/pillar/mynetworks/config-network.yaml
```
__Edit /srv/pillar/mynetworks/config-network.yaml using the sample [network config yaml](samples/bossh/config-network.yaml)__

## Usage:

You can run the below script with given parameter for the NEW cloned VM with a given hostname. The hostname can be short or fqdn. All other parameters must be provided from a config file in ```/root/suma_config.yaml``` in yaml format.

The desired NEW system networks need to be specified in a [network config yaml](samples/bossh/config-network.yaml) file which path is defined in /root/suma_config.yaml Look at [sample suma_config](samples/bossh/suma_config.yaml): 
```
python3 exec_script.py <new-hostname>
```
## Logic of the automation:
The workflow starts with using ```clone_vm.py``` deploying a new VM based on template. 
In the VM template the VM was prepared with the desired network interfaces in the desired LAN or VLAN segments. The eth0 is preconfigured with a static ip.
The template VM has SLES15SP2 with base, enhanced base pattern installed. Certain binaries e.g. curl, wget, dmidecode need to be installed. SSH daemon of course as well as opened the ports for ssh (22) and salt-minion ports (4505 4506 tcp).
The root user is configured with a password.

Once the ```clone_vm.py``` finished cloning the VM with a given name the new VM is booting up and my script start to run. The below code snippet show where I did modification in [clone_vm.py](samples/clone_vm.py)
```
print("cloning VM...")
    #onboarding.py is start to run
    print("Staring from here onboarding script is start to run...")
    run_onboarding(vm_name)
```
## Testing:
For test purpose without creating new cloned VM you can simply run below command on SUSE Manager from the directory where the repo resides.
First check in ```/root/suma_config.yaml``` the parameter clone_vm_ip is set to the ip of the VM that is reachable. This IP is used for the ssh connection. Then the new hostname and network definitions will be set. The network definition (eth0, eth1, ...) must be pre-defined in [network config yaml](samples/bossh/config-network.yaml)


```
...
clone_vm_ip: 192.168.122.223
...
```
```
python3 exec_script.py <newhostname.domain.com>
```
If you use a new hostname that does not exist in config-network.yaml then the targeted host will be renamed but without generating ifcfg-ethX and other network files. So network will not be changed, only host renaming will happen.

