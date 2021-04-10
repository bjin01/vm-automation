#!/usr/bin/env python3

import yaml
import sys

def read_pillar_file(pillar_file, uuid, hostname):
    uuid = uuid.rstrip('\n')
    if pillar_file == "":
        pillar_file = "/srv/pillar/change-hostname/init.sls"
    
    with open(pillar_file) as f:
        pillars = yaml.load_all(f, Loader=yaml.FullLoader)

        for pillar in pillars:
            for _, v in pillar.items():
                v[uuid] = hostname
                #print(k, "->", v)
        return pillar, pillar_file


def write_pillar_file(pillar_file, pillar_yaml):
    with open(pillar_file, 'w') as f:
        yaml.dump(pillar_yaml, f)
    print("pillar file has been updated: %s %s" %(pillar_file, pillar_yaml))
        #print(data)

""" pillar_file = ""
uuid = ""
hostname = "" """

""" if len(sys.argv) > 1:
    pillar_file = sys.argv[1]
else:
    pillar_file = ""

if len(sys.argv) > 2:
    uuid = sys.argv[2]
else:
    uuid = ""

if len(sys.argv) > 3:
    hostname = sys.argv[3]
else:
    hostname = ""
    
pillar_yaml, pillar_file = read_pillar_file(pillar_file, uuid, hostname)
write_pillar_file(pillar_file, pillar_yaml) """
