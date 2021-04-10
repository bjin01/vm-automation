#!/usr/bin/env python3

import yaml

def read_config_network_yaml(filepath, hostname):
    with open(filepath) as f:
        confs = yaml.load_all(f, Loader=yaml.FullLoader)
        empty = []
        for conf in confs:
            for _, v in conf.items():
                for x, y in v.items():
                    if hostname in x:
                        print(x, "->", y, '\n')
                        return y
                    else:
                        return empty

def write_ifcfg_file(nic, nic_details):
    
    template = """BOOTPROTO='static'
IPADDR='{ip}/{subnetmask}'
PREFIXLEN='{subnetmask}'
STARTMODE='auto'
USERCONTROL='no'""" 
    context = {
    "ip":nic_details['ip'], 
    "subnetmask":nic_details['subnetmask']
    } 
    #ifcfg_file = "ifcfg-" + nic
    #print(template.format(**context))
    """ with open(ifcfg_file, 'w') as f:
        f.write(template.format(**context)) """
    return template.format(**context)

if __name__ == "__main__":
    import sys
    networks = read_config_network_yaml(sys.argv[1], sys.argv[2])
    result = []
    if len(networks) != 0:
        for a, b in networks['nic'].items():

            conf = write_ifcfg_file(a, b)
            result.append(conf)
            """ print(a, ' -> ', end='')
            for c, d in b.items():
                print("\t%s: %s" %(c, d)) """
    print(result)
        