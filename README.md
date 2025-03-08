[![Build Status](https://travis-ci.org/vmware/pyvmomi-community-samples.svg?branch=master)](https://travis-ci.org/vmware/pyvmomi-community-samples) 

VMware - SUSE Linux VM clone from template - Automation 
=========================

This project is derived from [pyvmomi-community-samples](https://github.com/vmware/pyvmomi-community-samples) with additional scripts added.

The baisc workflow is to use VMware python API to generate a new Virtual Machine based on VMware Template and register the new VM with predefined individual VM configurations into SUSE Manager / Uyuni.

Based on several customer requirements the scripts have been extend over years.

The latest updated scripts support calling ansible rule-book HTTP Endpoint to trigger additional ansible playbooks to be deployed to new VM.


## Motivation:
Although other possibilities like terraform, salt-cloud, autoyast, ansible etc support similar approach but over the years I found out that many customers still rely on VMware infrastructure and cloning from template is an time efficient way to provision new VMs. 
The VM from template will be __customized__ based on predefined FQDN hostname and IPs etc.

## Main functions:
- Use clone_vm.py to create cloned VM.
- Onece VM is cloned we connect to the VM via ssh and rename it, create ifcfg-ethX files for all defined network interfaces, re-generate SLES machine-id to avoid system registration conflict in SUSE Manager.
- The new VM uuid and new hostname will be written into salt pillar files for further processing within salt.
- After **individualization** of the new VM it will be rebooted
- The script makes an ansible HTTP call to ansible rule-book endpoint to trigger additional playbooks (optional step)
- Once the new VM is rebooted the venv-salt-minion.service is started and registered to SUSE Manager and ansible playbooks can be deployed.

## Requirements on SUSE Manager host:
We need python libraries:
* pyVmomi
* paramiko

In current SUSE Manager 5.0.x releases python3.6 is the version to use.

Both libraries can be installed via rpm or pip3.6 (on SLES15SP6)
```
uyuni-server:/ # rpm -qa | grep paramiko
python3-paramiko-3.4.0-150400.9.3.3.noarch
uyuni-server:/ # rpm -qa | grep pyvmomi
python3-pyvmomi-6.7.3-150200.3.5.5.noarch
```

pip install pyvmomi [pyVmomi](https://pypi.org/project/pyvmomi/) 

pyVmomi is the Python SDK for the VMware vSphere Management API that allows you to rapidly build solutions integrated with VMware ESXi and vCenter Server
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
sudo python3.6 -m pip install --upgrade paramiko
```
To check the installed version of paramiko:
```
sudo python3.6 -m pip list | grep -i paramiko
```
* git clone this repo to your SUSE Manager host
```

mkdir myrepo
cd myrpo
git clone https://github.com/bjin01/vm-automation.git
git remote remove origin
```

## Configuration Files required:

*** Starting SUSE Manager 5.x container is being used. Directories /srv/salt /srv/pillar /etc/salt are persistent volume mounts. If container is removed config files in those directories will not be deleted. ***

Create those files on SUSE Manager (in container of SUSE Manager):
```
touch /root/suma_config.yaml

mkdir -p /srv/pillar/change-hostname
echo "myservers_uuid:" > /srv/pillar/change-hostname/init.sls

mkdir -p /srv/pillar/mynetworks/
touch /srv/pillar/mynetworks/config-network.yaml
```

__Edit /root/suma_config.yaml using the sample [suma_config.yaml](samples/bossh/suma_config.yaml)__

__Edit /srv/pillar/mynetworks/config-network.yaml using the sample [network config yaml](samples/bossh/config-network.yaml)__

## Usage:

You can run below script with input parameters to onboard a NEW VM from template with a given hostname. The hostname can be short or fqdn. All other parameters must be provided from a config file in ```/root/suma_config.yaml``` in yaml format.

Command inside SUSE Manager container:

```
python3.6 /root/vm-automation/samples/bossh/clone_vm.py -s your-vsphere-or-vcenter-host -o <port> -u <userid> --datacenter-name DC1 --cluster-name PROD -v <new-vm-name> --template <Template_Name> --datastore-name <Datastore_Name>
```

The desired NEW system networks need to be specified in a [network config yaml](samples/bossh/config-network.yaml) file which path is defined in /root/suma_config.yaml Look at [sample suma_config](samples/bossh/suma_config.yaml): 
```
python3 exec_script.py <new-hostname>
```
## Steps of VM provisioning automation:
The workflow starts with using ```clone_vm.py``` by cloning a new VM based on template. 
In the VM template the VM has a static IP and hostname configured.
The basic software including venv-salt-minion for using with SUSE Manager are installed.
Systemd venv-salt-minion should be disabled in the Template so that the template VM hostname will not be registering itself at first boot.
SSH daemon must be enabled and running, as well as port for ssh (22) is opened.
The root user is configured with a password.

The pre-configured static IP, root user and password need to be provided and defined in /root/suma_config.yaml

```
suma_host: localhost
suma_user: myuser
suma_password: <PASSWORD>
clone_vm_ip: 192.168.100.24
domain: mydomain.com
delete_system: mytemplate.host.name
ssh-user: root
ssh-password: <PASSWORD>
pillar_host: /srv/pillar/change-hostname/init.sls
pillar_network: /srv/pillar/mynetworks/config-network.yaml
activation_key: 1-sles15sp6
ansible_server: ansible-control-node.mydomain.com
ansible_rulebook_port: 5000
```

```clone_vm_ip``` is the static IP configured in the template VM.
```activation_key``` the activation-key is used to bootstrap the new VM with correct channels from SUSE Manager
```domain``` must be given to complete the hostname as FQDN. Short VM name e.g. myvm will be complemented with myvm.mydomain.com during onboarding.


Once the ```clone_vm.py``` finished cloning the VM with a given name the new VM is booting up and onboarding.py will be utilized to continue connecting the VM via ssh and do other steps. The below code snippet show where I did modification in [clone_vm.py](samples/clone_vm.py)
```
print("cloning VM...")
    #onboarding.py is start to run
    print("Staring from here onboarding script is start to run...")
    run_onboarding(vm_name)
```



