#!/usr/bin/python3

import os
import sys
import onboarding
import suma_actions


def run_onboarding(vm_name):
    conf_file = "/root/suma_config.yaml"

    if vm_name != "":
        vm_name_split = sys.argv[1].split('.', 2)
        if vm_name_split[0] != "":
            print("in if vm_name_split[0] %s" %vm_name_split[0])
            vm_name = vm_name_split[0] + ".engel.int"
        else:
            vm_name = sys.argv[1] + ".engel.int"
        print("vm_name fqdn is: %s" %vm_name)
        suma_login = suma_actions.get_login(conf_file)
        onboarding.onboarding(suma_login['clone_vm_ip'], vm_name, conf_file)
    return

if __name__ == "__main__":
    if len(sys.argv) > 1:
        vm_name_split = sys.argv[1].split('.', 2)
        if vm_name_split[0] != "":
            print("in if vm_name_split[0] %s" %vm_name_split[0])
            vm_name = vm_name_split[0] + ".engel.int"
        else:
            vm_name = sys.argv[1] + ".engel.int"
    run_onboarding(vm_name)