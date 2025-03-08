#!/usr/bin/python3
"""
Written by Bo Jin
Github: https://github.com/jinbo01
Email: bo.jin@suseconsulting.ch

Executes VM onboarding via ssh
"""

import yaml
import sys
import onboarding
import suma_actions


def run_onboarding(vm_name):
    suma_config = suma_actions.get_suma_config()

    if vm_name != "":
        vm_name_split = sys.argv[1].split('.', 2)
        if vm_name_split[0] != "":
            print("in if vm_name_split[0] %s" %vm_name_split[0])
            if "domain" in suma_config.keys():
                vm_name = vm_name_split[0] + "." + suma_config["domain"].lower().strip()
                print("vm_name fqdn is: %s" %vm_name)
            else:
                print("domain is not provided. Only use vm_name as hostname: %s" %vm_name)

        onboarding.onboarding(suma_config['clone_vm_ip'], vm_name)
    return

if __name__ == "__main__":
    suma_config = suma_actions.get_suma_config()
    if len(sys.argv) > 1:
        vm_name_split = sys.argv[1].split('.', 2)
        vm_name = vm_name_split[0]
        if vm_name != "":
            #print("in if vm_name_split[0] %s" %vm_name_split[0])
            if "domain" in suma_config.keys():
                vm_name = vm_name_split[0] + "." + suma_config["domain"].lower().strip()
                print("vm_name fqdn is: %s" %vm_name)
            else:
                print("domain is not provided. Only use vm_name as hostname: %s" %vm_name)
    run_onboarding(vm_name)
