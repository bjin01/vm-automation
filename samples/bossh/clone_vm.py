#!/usr/bin/env python
"""
Written originally by Dann Bohn modified by Bo Jin
Github: https://github.com/jinbo01
Email: bo.jin@suseconsulting.ch

Clone a VM from template
"""
from pyVmomi import vim
from tools import cli, service_instance, pchelper
import create_ifcfg
import suma_actions
import onboarding
import change_vm_vif_bo


def wait_for_task(task):
    """ wait for a vCenter task to finish """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            print("there was an error")
            print(task.info.error)
            task_done = True
            raise RuntimeError(f"Task failed: {task.info.error}")
        
def get_vm_network_info(newhostname):
    
    networks = dict()
    suma_login = suma_actions.get_suma_config()
    if suma_login['pillar_network']:
        networks = create_ifcfg.read_config_network_yaml(suma_login['pillar_network'], newhostname)
        if "nic" in networks.keys():
            print("list networks content {}".format(networks))
            return networks
        else:
            print("No matching vm in pillar_networks yaml {} found: {}".format(suma_login['pillar_network'], newhostname))
    return

def run_onboarding(vm_name):
    suma_config = suma_actions.get_suma_config()

    if vm_name != "":
        vm_name_split = vm_name.split('.', 2)
        if vm_name_split[0] != "":
            print("in if vm_name_split[0] %s" %vm_name_split[0])
            if "domain" in suma_config.keys():
                vm_name = vm_name_split[0] + "." + suma_config["domain"].lower().strip()
                print("vm_name fqdn is: %s" %vm_name)
            else:
                print("domain is not provided. Only use vm_name as hostname: %s" %vm_name)
        
        onboarding.onboarding(suma_config['clone_vm_ip'], vm_name)
    return

def change_vif_network(si, vm_name, vm_networks):
    vm_network_name = ""
    is_VDS = False
    if vm_networks:
        print("ok, found matching vm")
        if "vmware_network" in vm_networks["nic"]["eth0"].keys():
            vm_network_name = vm_networks["nic"]["eth0"]["vmware_network"]
            print("Set VM eth0 network to {}".format(vm_network_name))
        else:
            print("vmware_network parameter is not defined in {}".format(vm_networks["nic"]["eth0"]))
            return
        if "is_VDS" in vm_networks["nic"]["eth0"].keys() and vm_networks["nic"]["eth0"]["is_VDS"] == True:
            is_VDS = True
        change_vm_vif_bo.change_vif(si, None, vm_name, vm_network_name, is_VDS)
    else:
        print("No matching vm found. Exit.")
   
    return 

def clone_vm(
        si, content, template, vm_name, datacenter_name, vm_folder, datastore_name,
        cluster_name, resource_pool, power_on, datastorecluster_name, opaque_network_name):
    """
    Clone a VM from a template/VM, datacenter_name, vm_folder, datastore_name
    cluster_name, resource_pool, and power_on are all optional.
    """

    # if none git the first one
    datacenter = pchelper.get_obj(content, [vim.Datacenter], datacenter_name)

    if vm_folder:
        destfolder = pchelper.search_for_obj(content, [vim.Folder], vm_folder)
        print("show destfolder {}".format(destfolder))
    else:
        destfolder = datacenter.vmFolder
        print("show destfolder in else: {}".format(destfolder))

    if datastore_name:
        datastore = pchelper.search_for_obj(content, [vim.Datastore], datastore_name)
    else:
        datastore = pchelper.get_obj(
            content, [vim.Datastore], template.datastore[0].info.name)

    # if None, get the first one
    cluster = pchelper.search_for_obj(content, [vim.ClusterComputeResource], cluster_name)
    if not cluster:
        clusters = pchelper.get_all_obj(content, [vim.ResourcePool])
        cluster = list(clusters)[0]

    if resource_pool:
        resource_pool = pchelper.search_for_obj(content, [vim.ResourcePool], resource_pool)
    else:
        resource_pool = cluster.resourcePool

    vmconf = vim.vm.ConfigSpec()

    if datastorecluster_name:
        podsel = vim.storageDrs.PodSelectionSpec()
        pod = pchelper.get_obj(content, [vim.StoragePod], datastorecluster_name)
        podsel.storagePod = pod

        storagespec = vim.storageDrs.StoragePlacementSpec()
        storagespec.podSelectionSpec = podsel
        storagespec.type = 'create'
        storagespec.folder = destfolder
        storagespec.resourcePool = resource_pool
        storagespec.configSpec = vmconf

        try:
            rec = content.storageResourceManager.RecommendDatastores(
                storageSpec=storagespec)
            rec_action = rec.recommendations[0].action[0]
            real_datastore_name = rec_action.destination.name
        except Exception:
            real_datastore_name = template.datastore[0].info.name

        datastore = pchelper.get_obj(content, [vim.Datastore], real_datastore_name)

    # set relospec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = resource_pool

    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = power_on

    if opaque_network_name:
        clonespec.powerOn = False

    # print(f"clonespec.powerOn {clonespec.powerOn}")
    print("cloning VM...")

    task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
    wait_for_task(task)
    print("VM cloned.")

    # read pillar_networks and change vm eth0 network
    vm_networks = get_vm_network_info(vm_name)
    change_vif_network(si, vm_name, vm_networks)

    #onboarding.py is start to run
    print("Staring from here onboarding script is start to run...")
    run_onboarding(vm_name)


def main():
    """
    Let this thing fly
    """
    parser = cli.Parser()
    parser.add_required_arguments(cli.Argument.VM_NAME, cli.Argument.TEMPLATE)
    # if no locationis provided, thefirst available datacenter, datastore, etc. will be used
    parser.add_optional_arguments(cli.Argument.DATACENTER_NAME, cli.Argument.VMFOLDER,
                                  cli.Argument.DATASTORE_NAME, cli.Argument.DATASTORECLUSTER_NAME,
                                  cli.Argument.CLUSTER_NAME, cli.Argument.RESOURCE_POOL,
                                  cli.Argument.POWER_ON, cli.Argument.OPAQUE_NETWORK_NAME)
    args = parser.get_args()
    si = service_instance.connect(args)

    content = si.RetrieveContent()
    template = pchelper.get_obj(content, [vim.VirtualMachine], args.template)
    
    if template:
        clone_vm(
            si, content, template, args.vm_name, args.datacenter_name, args.vm_folder,
            args.datastore_name, args.cluster_name, args.resource_pool, args.power_on,
            args.datastorecluster_name, args.opaque_network_name)
    else:
        print("template not found")


# start this thing
if __name__ == "__main__":
    main()
