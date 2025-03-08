from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

# Disable SSL warnings (optional)
context = ssl._create_unverified_context()

# vCenter credentials
VCENTER_SERVER = "vcenter.example.com"
VCENTER_USER = "administrator@vsphere.local"
VCENTER_PASSWORD = "yourpassword"
VM_NAME = "your-vm-name"
NEW_NETWORK = "Your New Network"

# Connect to vCenter
si = SmartConnect(host=VCENTER_SERVER, user=VCENTER_USER, pwd=VCENTER_PASSWORD, sslContext=context)
content = si.RetrieveContent()

def get_vm(content, vm_name):
    """Find VM by name."""
    for child in content.rootFolder.childEntity:
        if hasattr(child, 'vmFolder'):
            vm_folder = child.vmFolder
            for vm in vm_folder.childEntity:
                if vm.name == vm_name:
                    return vm
    return None

def get_network(content, network_name):
    """Find network by name."""
    for child in content.rootFolder.childEntity:
        if hasattr(child, 'networkFolder'):
            network_folder = child.networkFolder
            for network in network_folder.childEntity:
                if network.name == network_name:
                    return network
    return None

vm = get_vm(content, VM_NAME)
if not vm:
    print(f"VM '{VM_NAME}' not found.")
    Disconnect(si)
    exit()

network = get_network(content, NEW_NETWORK)
if not network:
    print(f"Network '{NEW_NETWORK}' not found.")
    Disconnect(si)
    exit()

# Locate the first network adapter
device_changes = []
for device in vm.config.hardware.device:
    if isinstance(device, vim.vm.device.VirtualEthernetCard):
        # Change backing to new network
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        nic_spec.device = device
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.network = network
        nic_spec.device.backing.deviceName = NEW_NETWORK
        device_changes.append(nic_spec)
        break

if not device_changes:
    print("No network adapter found.")
    Disconnect(si)
    exit()

# Create VM reconfiguration spec
spec = vim.vm.ConfigSpec()
spec.deviceChange = device_changes

# Apply the configuration
task = vm.ReconfigVM_Task(spec)
print("Network change task started. Wait for completion.")

# Disconnect from vCenter
Disconnect(si)
