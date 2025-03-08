"""
Written by Bo Jin
Github: https://github.com/jinbo01
Email: bo.jin@suseconsulting.ch

A test script to list existing networks from VMWare vCenter
"""
from pyVmomi import vim
from tools import cli, tasks, service_instance, pchelper

def list_networks(content):
    networks = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.Network], True)
    for network in networks.view:
        print("Network: {}".format(network.name))

if __name__ == "__main__":
    parser = cli.Parser()

    args = parser.get_args()
    si = service_instance.connect(args)
    content = si.RetrieveContent()
    list_networks(content)