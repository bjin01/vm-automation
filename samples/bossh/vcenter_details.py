#!/usr/bin/env python
# VMware vSphere Python SDK
# Copyright (c) 2008-2021 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Python program for listing the VMs on an ESX / vCenter host
"""

from pyVmomi import vmodl
from pyVmomi import vim

from tools import cli, service_instance, vm


def parse_service_instance(si):
    """
    Print some basic knowledge about your environment as a Hello World
    equivalent for pyVmomi
    """

    content = si.RetrieveContent()
    object_view = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [], True)
    for obj in object_view.view:
        print(obj)
        if isinstance(obj, vim.VirtualMachine):
            vm.print_vm_info(obj)

    object_view.Destroy()
    return 0


def main():
    """
    Simple command-line program for listing the virtual machines on a system.
    """

    parser = cli.Parser()
    args = parser.get_args()

    try:
        si = service_instance.connect(args)

        # ## Do the actual parsing of data ## #
        parse_service_instance(si)

    except vmodl.MethodFault as ex:
        print("Caught vmodl fault : {}".format(ex.msg))
        return -1

    return 0


# Start program
if __name__ == "__main__":
    main()
