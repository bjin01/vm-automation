#!/usr/bin/env python3

from paramiko import SSHClient
import paramiko
import sys
import write_pillar
import create_ifcfg
import suma_actions
import ssh_test

def run_cmd(client, command):
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

def run_cmd_uuid(client, command):
    print(command)
    stdin, stdout, stderr = client.exec_command(command)
    uuid = stdout.read().decode("utf8").rstrip("\n")
    
    print(uuid)

    stdin.close()
    stdout.close()
    stderr.close()
    return uuid

def onboarding(hostname, newhostname, conf_file):
    paramiko.util.log_to_file("bosshv3.log")
    username = ""

    # reading suma and ssh login credentials in.
    suma_login = suma_actions.get_login(conf_file)
    ssh_test.test_ssh(hostname, suma_login)
    
    client = SSHClient()
    #client.load_system_host_keys()
    #client.load_host_keys('~/.ssh/known_hosts')
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(hostname, username=suma_login['ssh-user'], password=suma_login['ssh-password'])
    #client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    run_cmd(client, 'systemctl stop salt-minion')

    # here we try to delete either given delete_system in suma_config.yaml or the given newhostname on suse manager host. So this script must run on suma host
    
    # get VM uuid via dmidecode and will write it out to salt pillar
    uuid = run_cmd_uuid(client, "dmidecode | grep -i uuid | awk '{ print $2 }'")
    
    if suma_login['delete_system']:
        session, key = suma_actions.login_suma(suma_login)
        suma_actions.find_delete_system(suma_login['delete_system'], session, key, uuid=uuid)
        suma_actions.find_delete_system(newhostname, session, key, uuid=uuid)
        suma_actions.suma_logout(session, key)
        
    else:
        session, key = suma_actions.login_suma(suma_login)
        suma_actions.find_delete_system(newhostname, session, key, uuid=uuid)
        suma_actions.suma_logout(session, key)

    #sys.exit(0)

    cmd1 = "echo " + newhostname + " > /etc/salt/minion_id"
    run_cmd(client, cmd1)
    run_cmd(client, 'rm /etc/machine-id')
    run_cmd(client, 'rm /var/lib/dbus/machine-id')
    run_cmd(client, 'dbus-uuidgen --ensure')
    run_cmd(client, 'systemd-machine-id-setup')

    # here we start to assemble ifcfg-ethX files based on the provided yaml conf file.
    if suma_login['pillar_network']:
        networks = create_ifcfg.read_config_network_yaml(suma_login['pillar_network'], newhostname)
        print("list networks content %s" %networks)
    else:
        print("Failed, no pillar_network defined in %s" % conf_file)
        networks = []

    if len(networks) != 0:
        for a, b in networks['nic'].items():
            # set default gateway if default_gw is true
            if b['default_gw']:
                cmd4 = 'echo "default ' + b['gateway'] + ' - ' + a + '" > /etc/sysconfig/network/ifroute-' + a
                run_cmd(client, cmd4)
                cmd2 = 'echo "' + b['ip'] + ' ' + newhostname + ' ' + newhostname.split(".")[0] + '" >> /etc/hosts'
                run_cmd(client, cmd2)

            # write ifroute-ethx files if gateway and route are not empty
            if str(b['gateway']) != "" and b['route'] != None and not b['default_gw']:
                #print(str(b['gateway']), b['route'])
                cmd_routes = 'echo "' + b['route'] + ' ' + str(b['gateway']) + ' - ' + a + '" > /etc/sysconfig/network/ifroute-' + a
                run_cmd(client, cmd_routes)
            
            conf = create_ifcfg.write_ifcfg_file(a, b)
            if conf != "":
                filename = '/etc/sysconfig/network/ifcfg-' + a 
                cmd3 = 'echo "' + conf + '" > ' + filename
                run_cmd(client, cmd3)

    cmd6 = 'hostnamectl set-hostname ' + newhostname
    run_cmd(client, cmd6)


    # to make sure system got renamed correctly and we reboot the system, soft reboot with 3 minutes delay as default
    run_cmd(client, 'shutdown -r')

    # we hardcoded the pillar file here. Not very elegant but it is as it is
    pillar_file = suma_login['pillar_host']

    # compose salt pillar with uuid and newhostname for later usage within salt states.
    pillar_yaml, pillar_file = write_pillar.read_pillar_file(pillar_file, uuid, newhostname)
    write_pillar.write_pillar_file(pillar_file, pillar_yaml)

    client.close()
    return

if __name__ == "__main__":
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
    
    onboarding(hostname, newhostname, conf_file)