#!/usr/bin/env python
"""
Written by Nathan Prziborowski
Github: https://github.com/prziborowski

This code is released under the terms of the Apache 2
http://www.apache.org/licenses/LICENSE-2.0.html

The property collector can be used to fetch a subset of properties
for a large amount of objects with fewer round trips that iterating.

This sample shows how it could be used to fetch the power state of
all the VMs and post-process filter on them.

Note the printing vm.name does cause round-trip per-VM, so it could
be extended in a real script/product to fetch the name property as
well.

I used the ViewManager to gather VMs as it seems easier than making
a traverse spec go through all the datacenters to gather VMs that
may also be in sub-folders.

"""
from pyVmomi import vim, vmodl
from tools import cli, service_instance, pchelper

__author__ = 'prziborowski'


def create_filter_spec(vms, prop):
    obj_specs = []
    for vm in vms:
        obj_spec = vmodl.query.PropertyCollector.ObjectSpec(obj=vm)
        obj_specs.append(obj_spec)
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = obj_specs
    prop_set = vmodl.query.PropertyCollector.PropertySpec(all=False)
    prop_set.type = vim.VirtualMachine
    prop_set.pathSet = [prop]
    filter_spec.propSet = [prop_set]
    return filter_spec


def filter_results(result, value):
    vms = []
    for obj in result.objects:
        if obj.propSet[0].val == value:
            vms.append(obj.obj)
    return vms


def main():
    parser = cli.Parser()
    parser.add_custom_argument('--property', default='runtime.powerState',
                               help='Name of the property to filter by')
    parser.add_custom_argument('--value', default='poweredOn', help='Value to filter with')
    args = parser.get_args()
    si = service_instance.connect(args)
    # Start with all the VMs from container, which is easier to write than
    # PropertyCollector to retrieve them.
    content = si.RetrieveContent()
    vms = pchelper.get_all_obj(content, [vim.VirtualMachine])

    prop_collector = content.propertyCollector
    filter_spec = create_filter_spec(vms, args.property)
    options = vmodl.query.PropertyCollector.RetrieveOptions()
    result = prop_collector.RetrievePropertiesEx([filter_spec], options)
    vms = filter_results(result, args.value)
    print("VMs with %s = %s" % (args.property, args.value))
    for vm in vms:
        print(vm.name)


if __name__ == '__main__':
    main()
