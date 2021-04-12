#!/usr/bin/env python
"""
Written by Gaël Berthaud-Müller
Github : https://github.com/blacksponge

This code is released under the terms of the Apache 2
http://www.apache.org/licenses/LICENSE-2.0.html

Example code for using the task scheduler.
"""

from datetime import datetime, timedelta
from tools import cli, service_instance
from pyVmomi import vim
from pyVim import connect


def main():
    parser = cli.Parser()
    parser.add_required_arguments(cli.Argument.MINUTES, cli.Argument.VM_NAME)
    parser.add_optional_arguments(cli.Argument.POWER_ON)
    args = parser.get_args()
    try:
        date_time = datetime.now() + timedelta(minutes=int(args.minutes))
        # dt = datetime.strptime(args.date, '%d/%m/%Y %H:%M')
    except ValueError:
        print('Unrecognized date format')
        return -1

    si = service_instance.connect(args)

    view = si.content.viewManager.CreateContainerView(si.content.rootFolder,
                                                      [vim.VirtualMachine],
                                                      True)
    vms = [vm for vm in view.view if vm.name == args.vm_name]

    if not vms:
        print('VM not found')
        connect.Disconnect(si)
        return -1
    vm = vms[0]

    spec = vim.scheduler.ScheduledTaskSpec()
    spec.name = 'PowerOff vm %s' % args.vm_name
    spec.description = ''
    spec.scheduler = vim.scheduler.OnceTaskScheduler()
    spec.scheduler.runAt = date_time
    spec.action = vim.action.MethodAction()
    if args.power_on:
        spec.action.name = vim.VirtualMachine.PowerOn
        spec.name = 'PowerOn vm %s' % args.vm_name + str(datetime.now())
    else:
        spec.action.name = vim.VirtualMachine.PowerOff
        spec.name = 'PowerOff vm %s' % args.vm_name + str(datetime.now())
    spec.enabled = True

    if si.content.scheduledTaskManager.CreateScheduledTask(vm, spec) is not None:
        print('Scheduled Task Successfully')
    return 0


if __name__ == "__main__":
    main()
