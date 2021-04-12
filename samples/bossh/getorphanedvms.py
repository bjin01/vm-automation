#!/usr/bin/env python
"""
This module demonstrates how to find virtual machines that
exist on a datastore, but are not part of the inventory.
This can be useful to find orphaned virtual machines that
are still taking up datastore space, but not currently
being used.

Issues:
    Currently works with Windows based vCenter servers only.
    Still working on vCenter Server Appliance

Example:

      $./getorphanedvms.py -s 10.90.2.10 -u vcenter.svc -p password
"""

import argparse
import urllib.request
import urllib.parse
import base64
from pyVim.connect import Disconnect
from pyVmomi import vmodl, vim
from tools import cli, service_instance


VMX_PATH = []
DS_VM = {}
INV_VM = []


def updatevmx_path():
    """
    function to set the VMX_PATH global variable to null
    """
    global VMX_PATH
    VMX_PATH = []


def url_fix(url_str, charset='utf-8'):
    """
    function to fix any URLs that have spaces in them
    urllib for some reason doesn't like spaces
    function found on internet
    """
    if isinstance(url_str, unicode):
        url_str = url_str.encode(charset, 'ignore')
    scheme, netloc, path, qs, anchor = urllib.parse.urlsplit(url_str)
    path = urllib.parse.quote(path, '/%')
    qs = urllib.parse.quote(qs, ':&=')
    return urllib.parse.urlunsplit((scheme, netloc, path, qs, anchor))


def get_args():
    """
    Supports the command-line arguments listed below.
    function to parse through args for connecting to ESXi host or
    vCenter server function taken from getallvms.py script
    from pyvmomi github repo
    """
    parser = argparse.ArgumentParser(
        description='Process args for retrieving all the Virtual Machines')
    parser.add_argument(
        '-s', '--host', required=True, action='store',
        help='Remote host to connect to')
    parser.add_argument(
        '-o', '--port', type=int, default=443, action='store',
        help='Port to connect on')
    parser.add_argument(
        '-u', '--user', required=True, action='store',
        help='User name to use when connecting to host')
    parser.add_argument(
        '-p', '--password', required=True, action='store',
        help='Password to use when connecting to host')
    args = parser.parse_args()
    return args


def find_vmx(ds_browser, ds_name, datacenter, full_ds_name):
    """
    function to search for VMX files on any datastore that is passed to it
    """
    args = get_args()
    search = vim.HostDatastoreBrowserSearchSpec()
    search.matchPattern = "*.vmx"
    search_ds = ds_browser.SearchDatastoreSubFolders_Task(ds_name, search)
    while search_ds.info.state != "success":
        pass
    # results = search_ds.info.result
    # print(results)

    for sub_folder in search_ds.info.result:
        ds_folder = sub_folder.folderPath
        for file in sub_folder.file:
            try:
                ds_file = file.path
                vm_folder = ds_folder.split("]")
                vm_folder = vm_folder[1]
                vm_folder = vm_folder[1:]
                vmxurl = "https://%s/folder/%s%s?dcPath=%s&dsName=%s" % \
                         (args.host, vm_folder, ds_file, datacenter, full_ds_name)
                VMX_PATH.append(vmxurl)
            except Exception as ex:
                print("Caught exception : " + str(ex))
                return -1


def examine_vmx(dsname):
    """
    function to download any vmx file passed to it via the datastore browser
    and find the 'vc.uuid' and 'displayName'
    """
    args = get_args()
    try:
        for file_vmx in VMX_PATH:
            # print(file_vmx)

            username = args.user
            password = args.password
            request = urllib.request.Request(url_fix(file_vmx))
            base64string = base64.encodestring(
                '%s:%s' % (username, password)).replace('\n', '')
            request.add_header("Authorization", "Basic %s" % base64string)
            result = urllib.request.urlopen(request)
            vmxfile = result.readlines()
            mylist = []
            for a in vmxfile:
                mylist.append(a)
            for b in mylist:
                if b.startswith("displayName"):
                    dn = b
                if b.startswith("vc.uuid"):
                    vcid = b
            uuid = vcid.replace('"', "")
            uuid = uuid.replace("vc.uuid = ", "")
            uuid = uuid.strip("\n")
            uuid = uuid.replace(" ", "")
            uuid = uuid.replace("-", "")
            newdn = dn.replace('"', "")
            newdn = newdn.replace("displayName = ", "")
            newdn = newdn.strip("\n")
            vmfold = file_vmx.split("folder/")
            vmfold = vmfold[1].split("/")
            vmfold = vmfold[0]
            dspath = "%s/%s" % (dsname, vmfold)
            tempds_vm = [newdn, dspath]
            DS_VM[uuid] = tempds_vm

    except Exception as ex:
        print("Caught exception : " + str(ex))


def getvm_info(vm, depth=1):
    """
    print information for a particular virtual machine or recurse
    into a folder with depth protection
    from the getallvms.py script from pyvmomi from github repo
    """
    maxdepth = 10

    # if this is a group it will have children. if it does,
    # recurse into them and then return

    if hasattr(vm, 'childEntity'):
        if depth > maxdepth:
            return
        vmlist = vm.childEntity
        for c in vmlist:
            getvm_info(c, depth+1)
        return
    if hasattr(vm, 'CloneVApp_Task'):
        vmlist = vm.vm
        for c in vmlist:
            getvm_info(c)
        return

    try:
        uuid = vm.config.instanceUuid
        uuid = uuid.replace("-", "")
        INV_VM.append(uuid)
    except Exception as ex:
        print("Caught exception : " + str(ex))
        return -1


def find_match(uuid):
    """
    function takes vc.uuid from the vmx file and the instance uuid from
    the inventory VM and looks for match if no match is found
    it is printed out.
    """
    a = 0
    for temp in INV_VM:
        if uuid == temp:
            a = a+1
    if a < 1:
        print(DS_VM[uuid])


def main():
    """
    function runs all of the other functions. Some parts of this function
    are taken from the getallvms.py script from the pyvmomi gihub repo
    """
    parser = cli.Parser()
    parser.add_optional_arguments(cli.Argument.VM_NAME, cli.Argument.UUID, cli.Argument.PORT_GROUP)
    args = parser.get_args()
    si = service_instance.connect(args)
    try:
        content = si.RetrieveContent()
        datacenter = content.rootFolder.childEntity[0]
        datastores = datacenter.datastore
        vmfolder = datacenter.vmFolder
        vmlist = vmfolder.childEntity
        dsvmkey = []

        # each datastore found on ESXi host or vCenter is passed
        # to the find_vmx and examine_vmx functions to find all
        # VMX files and search them

        for datastore in datastores:
            find_vmx(datastore.browser, "[%s]" % datastore.summary.name,
                     datacenter.name, datastore.summary.name)
            examine_vmx(datastore.summary.name)
            updatevmx_path()

        # each VM found in the inventory is passed to the getvm_info
        # function to get it's instanceuuid

        for vm in vmlist:
            getvm_info(vm)

        # each key from the DS_VM hashtable is added to a separate
        # list for comparison later

        for a in DS_VM.keys():
            dsvmkey.append(a)

        # each uuid in the dsvmkey list is passed to the find_match
        # function to look for a match

        print("The following virtual machine(s) do not exist in the "
              "inventory, but exist on a datastore "
              "(Display Name, Datastore/Folder name):")
        for match in dsvmkey:
            find_match(match)
        Disconnect(si)
    except vmodl.MethodFault as ex:
        print("Caught vmodl fault : " + ex.msg)
        return -1
    except Exception as ex:
        print("Caught exception : " + str(ex))
        return -1

    return 0


# Start program
if __name__ == "__main__":
    main()
