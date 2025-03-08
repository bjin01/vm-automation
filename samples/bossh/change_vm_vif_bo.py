#!/usr/bin/env python
"""
Written by Bo Jin
Github: https://github.com/jinbo01
Email: bo.jin@suseconsulting.ch

This script changes the VM's NiC VMware Network, power off VM, power on VM  
It is used during VM provisioning workflow, mostly from clone_vm.py
"""

from tools import cli, tasks, service_instance, pchelper
from pyVmomi import vim, vmodl
import time

def power_off(si, VM):
    if format(VM.runtime.powerState) == "poweredOn":
        print("Attempting to power off {0}".format(VM.name))
        TASK = VM.PowerOffVM_Task()
        tasks.wait_for_tasks(si, [TASK])
        print("{0}".format(TASK.info.state))
    elif format(VM.runtime.powerState) == "poweredOff":
        print("{0} is already off.".format(VM.name))

    return True

def power_on(si, VM):
    if format(VM.runtime.powerState) == "poweredOff":
        print("Attempting to power on {0}".format(VM.name))
        TASK = VM.PowerOnVM_Task()
        tasks.wait_for_tasks(si, [TASK])
        print("{0}".format(TASK.info.state))
    elif format(VM.runtime.powerState) == "poweredOn":
        print("{0} is already on.".format(VM.name))

    return True

def change_vif(si, uuid=None, vm_name=None, network_name=None, is_VDS=None):
    """
    Simple command-line program for changing network virtual machines NIC.
    """

    try:
        content = si.RetrieveContent()
        vm = None
        if uuid:
            vm = content.searchIndex.FindByUuid(None, uuid, True)
        elif vm_name:
            vm = pchelper.get_obj(content, [vim.VirtualMachine], vm_name)

        if not vm:
            raise SystemExit("Unable to locate VirtualMachine.")

        # This code is for changing only one Interface. For multiple Interface
        # Iterate through a loop of network names.
        device_change = []
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                nicspec = vim.vm.device.VirtualDeviceSpec()
                nicspec.operation = \
                    vim.vm.device.VirtualDeviceSpec.Operation.edit
                nicspec.device = device
                nicspec.device.wakeOnLanEnabled = True

                if is_VDS:
                    nicspec.device.backing = \
                        vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                    nicspec.device.backing.network = \
                        pchelper.get_obj(content, [vim.Network], network_name)
                    nicspec.device.backing.deviceName = network_name
                else:
                    print("see network_name {}".format(network_name))
                    network = pchelper.get_obj(
                        content, [vim.dvs.DistributedVirtualPortgroup], network_name)
                    dvs_port_connection = vim.dvs.PortConnection()
                    dvs_port_connection.portgroupKey = network.key
                    dvs_port_connection.switchUuid = \
                        network.config.distributedVirtualSwitch.uuid
                    nicspec.device.backing = \
                        vim.vm.device.VirtualEthernetCard. \
                        DistributedVirtualPortBackingInfo()
                    nicspec.device.backing.port = dvs_port_connection

                nicspec.device.connectable = \
                    vim.vm.device.VirtualDevice.ConnectInfo()
                nicspec.device.connectable.startConnected = True
                nicspec.device.connectable.allowGuestControl = True
                device_change.append(nicspec)
                break

        config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
        task = vm.ReconfigVM_Task(config_spec)
        tasks.wait_for_tasks(si, [task])
        print("Successfully set network for {} to {}".format(vm_name, network_name))
        print("Power Off {} and wait for 2 seconds".format(vm_name))
        power_off(si, vm)
        time.sleep(2)
        print("Power On {}".format(vm_name))
        power_on(si, vm)

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return False

    return True


# Start program
if __name__ == "__main__":
    parser = cli.Parser()
    parser.add_optional_arguments(
        cli.Argument.UUID, cli.Argument.VM_NAME, cli.Argument.NETWORK_NAME)
    parser.add_custom_argument('--is_VDS',
                               action="store_true",
                               default=False,
                               help='The provided network is in VSS or VDS')
    args = parser.get_args()
    si = service_instance.connect(args)

    change_vif(si, args.uuid, args.vm_name, args.network_name, args.is_VDS)
