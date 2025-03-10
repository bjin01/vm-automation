VMware - SUSE Linux VM clone from template - Automation (2025) with ansible EDA support 
=========================

This project is derived from [pyvmomi-community-samples](https://github.com/vmware/pyvmomi-community-samples) with additional scripts added.

The workflow is to use VMware python API to clone a new Virtual Machine from VMware Template and register the new VM with predefined individual VM configurations into SUSE Manager / Uyuni.

Based on several customer requirements the scripts have been extended over years.

The latest updates support calling ansible rule-book HTTP Endpoint and trigger ansible playbooks deployment to new VM.


## Motivation:
Although other possibilities like terraform, salt-cloud, autoyast, ansible etc. support similar approach but over the years I found out that many customers still rely on VMware infrastructure and cloning from template is an time efficient way to provision new VMs quickly. But cloned VM is static and lacks individual configurations.
The VM from template will be __customized__ based on predefined FQDN hostname and IPs etc.

Software Products required:
* VMWare vCenter vSphere
* SUSE Manager / Uyuni
* salt-master
* python3.6 or higher

## Tested Environement:
```
VMware vCenter 11.6
SUSE Manager 5.0.x
SLE-Micro 5.5
salt-master 3006.0
ansible [core 2.16.5]
ansible host: SLES15SP6
Client System: SLES15SP6
```
```
ansible-rulebook --version
1.1.2
  Executable location = /usr/local/bin/ansible-rulebook
  Drools_jpy version = 0.3.9
  Java home = /usr/lib64/jvm/java-21-openjdk-21
  Java version = 21.0.6
  Python version = 3.11.10 (main, Sep 18 2024, 22:14:32) [GCC]
```

## Main functions:
- Use clone_vm.py to create cloned VM.
- Onece VM is cloned we connect to the VM via ssh and rename it, create ifcfg-ethX files for all defined network interfaces, re-generate SLES machine-id to avoid system registration conflict in SUSE Manager.
- The new VM uuid and new hostname will be written into salt pillar files for further processing within salt.
- After **individualization** of the new VM it will be rebooted
- The script makes an ansible HTTP call to ansible rule-book endpoint to trigger additional playbooks (optional step)
- Once the new VM is rebooted the venv-salt-minion.service is started and registered to SUSE Manager and ansible playbooks can be deployed.

## Requirements on SUSE Manager host:
We need additional python libraries in SUSE Manager container:
* pyVmomi
* paramiko

python3.6 is the version to use in SUSE Manager 5.0.x release 

Both libraries can be installed via rpm 
```
uyuni-server:/ # rpm -qa | grep paramiko
python3-paramiko-3.4.0-150400.9.3.3.noarch
uyuni-server:/ # rpm -qa | grep pyvmomi
python3-pyvmomi-6.7.3-150200.3.5.5.noarch
```

or pip3.6 (on SLES15SP6)
```
zypper install -y python3-pip
```

pip3.6 install pyvmomi [pyVmomi](https://pypi.org/project/pyvmomi/) 

pyVmomi is the Python SDK for the VMware vSphere Management API that allows you to rapidly build solutions integrated with VMware ESXi and vCenter Server
```
sudo pip3.6 install pyvmomi
sudo pip3.6 install --upgrade pyvmomi
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

> [!IMPORTANT]
> ***Starting SUSE Manager 5.x container is being used. Directories /srv/salt /srv/pillar /etc/salt are persistent volume mounts. If container is removed config files in those directories will not be deleted.***

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

## VM Template Requirements:
* In the VM template the VM has a static IP and hostname configured (no dhcp ip)
* The basic software and including venv-salt-minion for SUSE Manager must be installed.
* The template VM has been configured and is successfully registered to a SUSE Manager server. 
* Stop venv-salt-minion.service and delete the template VM from SUSE Manager.
* Delete minion and master key files in template VM /etc/venv-salt-minion/pki/minion/ (new ones will be recreated upon next venv-salt-minion restart)
* Systemd venv-salt-minion.service should be disabled in the Template so that the template VM hostname will not be registering itself into SUSE Manager at first boot.
* SSH daemon must be enabled and running, as well as port for ssh (22) is opened.
* The root user is configured with a password.

## Usage:

You can run below script with input parameters to clone and onboard a NEW VM from template with a given hostname. The hostname can be short or fqdn. All other parameters must be provided from a config file in ```/root/suma_config.yaml``` in yaml format.

Run this command inside SUSE Manager container:

```
python3.6 /root/vm-automation/samples/bossh/clone_vm.py -s your-vsphere-or-vcenter-host -o <port> -u <userid> --datacenter-name DC1 --cluster-name PROD -v <new-vm-name> --template <Template_Name> --datastore-name <Datastore_Name>
```

The desired NEW system networks need to be specified in a [network config yaml](samples/bossh/config-network.yaml) file which path is defined in /root/suma_config.yaml Look at [sample suma_config](samples/bossh/suma_config.yaml): 

## Steps of VM provisioning automation:
The workflow starts with ```clone_vm.py``` by cloning a new VM based on template.
Right after successful VM clone the VM eth0 network card will be changed to the predefined Network given in /srv/pillar/mynetworks/config-network.yaml
VM will be powered on
```clone_vm.py``` will call ```onboarding.py``` to start onboarding process using ssh
```onboarding.py``` will wait until VM is available and try to connect ssh with given user and password from /root/suma_config.yaml
Once connected ```onboarding.py``` will re-create machine-id (because it has old template VM machine-id)
```onboarding.py``` will call ```suma_actions.find_delete_system()``` to delete Template VM if it is still found in SUSE Manager by using SUSE Manager API and salt-key
```onboarding.py``` will write the FQDN hostname into /etc/venv-salt-minion/minion_id
```onboarding.py``` will write activation-key into /etc/venv-salt-minion/minion.d/activation_key.conf
```onboarding.py``` will write
```
autosign_grains: 
  - os_family
``` 
into /etc/venv-salt-minion/minion.d/auto_accept.conf

```onboarding.py``` will generate /etc/sysconfig/network/ifcfg-eth0 and /etc/sysconfig/network/ifroute-eth0 filed based on given data in /srv/pillar/mynetworks/config-network.yaml
```onboarding.py``` will write FQDN with the static IP into /etc/hosts

```onboarding.py``` will execute ```yast dns edit hostname=' + newhostname``` in order to change hostname.
if ansible_server and ansible_rulebook_port are predefined then ```onboarding.py``` will execute 
```
send_post_request(host_new_ip)
```
to call ansible rule-book in order to trigger additional playbooks.
```onboarding.py``` will write new VM uuid and hostname into pillar file /srv/pillar/change-hostname/init.sls
Finally ```onboarding.py``` will reboot the VM.

## sample suma_conf.yaml
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



