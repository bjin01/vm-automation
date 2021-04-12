#!/usr/bin/env python
#
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
Sample Python program for monitoring property changes to objects of one
or more types
"""

import atexit
import collections
import sys
from pyVmomi import vim, vmodl
from tools import cli, service_instance, serviceutil


def parse_propspec(propspec):
    """
    Parses property specifications.  Returns sequence of 2-tuples, each
    containing a managed object type and a list of properties applicable
    to that type

    :type propspec: collections.Sequence
    :rtype: collections.Sequence
    """

    props = []

    for objspec in propspec:
        if ':' not in objspec:
            raise Exception('property specification \'%s\' does not contain '
                            'property list' % objspec)

        objtype, objprops = objspec.split(':', 1)

        motype = getattr(vim, objtype, None)

        if motype is None:
            raise Exception('referenced type \'%s\' in property specification '
                            'does not exist,\nconsult the managed object type '
                            'reference in the vSphere API documentation' %
                            objtype)

        proplist = objprops.split(',')

        props.append((motype, proplist,))

    return props


def make_wait_options(max_wait_seconds=None, max_object_updates=None):
    waitopts = vmodl.query.PropertyCollector.WaitOptions()

    if max_object_updates is not None:
        waitopts.maxObjectUpdates = max_object_updates

    if max_wait_seconds is not None:
        waitopts.maxWaitSeconds = max_wait_seconds

    return waitopts


def make_property_collector(prop_collector, from_node, props):
    """
    :type prop_collector: pyVmomi.VmomiSupport.vmodl.query.PropertyCollector
    :type from_node: pyVmomi.VmomiSupport.ManagedObject
    :type props: collections.Sequence
    :rtype: pyVmomi.VmomiSupport.vmodl.query.PropertyCollector.Filter
    """

    # Make the filter spec
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()

    # Make the object spec
    traversal = serviceutil.build_full_traversal()

    obj_spec = vmodl.query.PropertyCollector.ObjectSpec(obj=from_node, selectSet=traversal)
    obj_specs = [obj_spec]

    filter_spec.objectSet = obj_specs

    # Add the property specs
    prop_set = []
    for motype, proplist in props:
        prop_spec = \
            vmodl.query.PropertyCollector.PropertySpec(type=motype, all=False)
        prop_spec.pathSet.extend(proplist)
        prop_set.append(prop_spec)

    filter_spec.propSet = prop_set

    try:
        pc_filter = prop_collector.CreateFilter(filter_spec, True)
        atexit.register(pc_filter.Destroy)
        return pc_filter
    except vmodl.MethodFault as ex:
        if ex._wsdlName == 'InvalidProperty':
            print("InvalidProperty fault while creating PropertyCollector filter : %s"
                  % ex.name, file=sys.stderr)
        else:
            print("Problem creating PropertyCollector filter : %s"
                  % str(ex.faultMessage), file=sys.stderr)
        raise


def monitor_property_changes(si, propspec, iterations=None):
    """
    :type si: pyVmomi.VmomiSupport.vim.ServiceInstance
    :type propspec: collections.Sequence
    :type iterations: int or None
    """

    prop_collector = si.content.propertyCollector
    make_property_collector(prop_collector, si.content.rootFolder, propspec)
    waitopts = make_wait_options(30)

    version = ''

    while True:
        if iterations is not None:
            if iterations <= 0:
                print('Iteration limit reached, monitoring stopped')
                break

        result = prop_collector.WaitForUpdatesEx(version, waitopts)

        # timeout, call again
        if result is None:
            continue

        # process results
        for filter_set in result.filterSet:
            for object_set in filter_set.objectSet:
                moref = getattr(object_set, 'obj', None)
                assert moref is not None, \
                    'object moref should always be present in objectSet'

                moref = str(moref).strip('\'')

                kind = getattr(object_set, 'kind', None)
                assert (
                        kind is not None
                        and kind in ('enter', 'modify', 'leave',)), \
                    'objectSet kind must be valid'

                if kind in ('enter', 'modify'):
                    change_set = getattr(object_set, 'changeSet', None)
                    assert (change_set is not None
                            and isinstance(change_set, collections.Sequence)
                            and len(change_set) > 0), \
                        'enter or modify objectSet should have non-empty changeSet'

                    changes = []
                    for change in change_set:
                        name = getattr(change, 'name', None)
                        assert (name is not None), \
                            'changeset should contain property name'
                        val = getattr(change, 'val', None)
                        changes.append((name, val,))

                    print("== %s ==" % moref)
                    print('\n'.join(['%s: %s' % (n, v,) for n, v in changes]))
                    print('\n')
                elif kind == 'leave':
                    print("== %s ==" % moref)
                    print('(removed)\n')

        version = result.version

        if iterations is not None:
            iterations -= 1


def main():
    """
    Sample Python program for monitoring property changes to objects of
    one or more types to stdout
    """

    parser = cli.Parser()
    parser.set_epilog("""
        Example usage:
        waitforupdates.py -k -s vcenter -u root -p vmware -i 1 -P
        VirtualMachine:name,summary.config.numCpu,runtime.powerState,config.uuid -P
        -P Datacenter:name -- This will fetch and print a few VM properties and the
        name of the datacenters
        """)
    parser.add_custom_argument('--iterations', type=int, default=None,
                               action='store',
                               help="""
                               The number of updates to receive before exiting
                               , default is no limit. Must be 1 or more if specified.
                               """)
    parser.add_custom_argument('--propspec', dest='propspec', required=True,
                               action='append',
                               help='Property specifications to monitor, e.g. '
                               'VirtualMachine:name,summary.config. Repetition '
                               'permitted')
    args = parser.get_args()

    if args.iterations is not None and args.iterations < 1:
        parser.print_help()
        print('\nInvalid argument: Iteration count must be omitted or greater than 0',
              file=sys.stderr)
        sys.exit(-1)

    try:
        si = service_instance.connect(args)
        propspec = parse_propspec(args.propspec)

        print("Monitoring property changes.  Press ^C to exit")
        monitor_property_changes(si, propspec, args.iterations)

    except vmodl.MethodFault as ex:
        print("Caught vmodl fault :\n%s" % str(ex), file=sys.stderr)
    except Exception as ex:
        print("Caught exception : " + str(ex), file=sys.stderr)


if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as ex:
        print("Caught exception : " + str(ex), file=sys.stderr)
    except KeyboardInterrupt:
        print("Exiting", file=sys.stderr)
        sys.exit(0)


# vim: set ts=4 sw=4 expandtab filetype=python:
