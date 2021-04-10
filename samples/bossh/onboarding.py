#!/usr/bin/env python3

from paramiko import SSHClient
import paramiko
import sys
import write_pillar
import create_ifcfg
import suma_actions

def run_cmd(command):
    print(command)
    stdin, stdout, stderr = client.exec_command(command)
    str_stdout = stdout.read().decode("utf8")
    str_stderr = stderr.read().decode("utf8")
    print("STDOUT: %s" % str_stdout)
    print("STDERR: %s" % str_stderr)

# Get return code from command (0 is default for success)
    str_return_code = stdout.channel.recv_exit_status()
    print("Return code: %s" % str_return_code)
    stdin.close()
    stdout.close()
    stderr.close()

def run_cmd_uuid(command):
    print(command)
    stdin, stdout, stderr = client.exec_command(command)
    uuid = stdout.read().decode("utf8").rstrip("\n")
    
    print(uuid)

    stdin.close()
    stdout.close()
    stderr.close()
    return uuid

paramiko.util.log_to_file("bosshv3.log")

username = ""
if len(sys.argv) > 1:
    hostname = sys.argv[1]
    if hostname.find("@") >= 0:
        username, hostname = hostname.split("@")
else:
    hostname = input("Hostname: ")
if len(hostname) == 0:
    print("*** Hostname required.")
    sys.exit(1)
port = 22
if hostname.find(":") >= 0:
    hostname, portstr = hostname.split(":")
    port = int(portstr)

if len(sys.argv) > 2:
    newhostname = sys.argv[2]

if len(sys.argv) > 3:
    conf_file = sys.argv[3]

client = SSHClient()
#client.load_system_host_keys()
#client.load_host_keys('~/.ssh/known_hosts')
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

client.connect(hostname, username=username, password='test')
#client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

run_cmd('systemctl stop salt-minion')

# here we try to delete either given delete_system in suma_config.yaml or the given newhostname on suse manager host. So this script must run on suma host
suma_login = suma_actions.get_login('')
session, key = suma_actions.login_suma(suma_login)
if suma_login['delete_system']:
    suma_actions.find_delete_system(suma_login['delete_system'], session, key)
else:
    suma_actions.find_delete_system(newhostname, session, key)

#sys.exit(0)

cmd1 = "echo " + newhostname + " > /etc/salt/minion_id"
run_cmd(cmd1)
run_cmd('rm /etc/machine-id')
run_cmd('rm /var/lib/dbus/machine-id')
run_cmd('dbus-uuidgen --ensure')
run_cmd('systemd-machine-id-setup')

networks = create_ifcfg.read_config_network_yaml(conf_file, newhostname)

if len(networks) != 0:
    for a, b in networks['nic'].items():
        # set default gateway if default_gw is true
        if b['default_gw']:
            cmd4 = 'echo "default ' + b['gateway'] + ' - ' + a + '" > /etc/sysconfig/network/ifroute-' + a
            run_cmd(cmd4)
            cmd2 = 'echo "' + b['ip'] + ' ' + newhostname + ' ' + newhostname.split(".")[0] + '" >> /etc/hosts'
            run_cmd(cmd2)

        # write ifroute-ethx files if gateway and route are not empty
        if str(b['gateway']) != "" and b['route'] != None:
            print(str(b['gateway']), b['route'])
            cmd_routes = 'echo "' + b['route'] + ' ' + str(b['gateway']) + ' - ' + a + '" > /etc/sysconfig/network/ifroute-' + a
            run_cmd(cmd_routes)
        
        # write ifcfg-ethx files
        #print("a is %s: b is %s" % (a, b))
        conf = create_ifcfg.write_ifcfg_file(a, b)
        #print("conf content is: %s" % conf)
        if conf != "":
            filename = '/etc/sysconfig/network/ifcfg-' + a 
            cmd3 = 'echo "' + conf + '" > ' + filename
            run_cmd(cmd3)

#run_cmd('systemctl start salt-minion')
cmd6 = 'hostnamectl set-hostname ' + newhostname
run_cmd(cmd6)

uuid = run_cmd_uuid("dmidecode | grep -i uuid | awk '{ print $2 }'")

run_cmd('shutdown -r')

pillar_file = "/srv/pillar/change-hostname/init.sls"

pillar_yaml, pillar_file = write_pillar.read_pillar_file(pillar_file, uuid, newhostname)
write_pillar.write_pillar_file(pillar_file, pillar_yaml)

client.close()