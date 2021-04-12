#!/usr/bin/env python3

import yaml
import os
from xmlrpc.client import ServerProxy, Error
import salt.config
import salt.wheel

def get_login(path):
    
    if path == "":
        path = os.path.join(os.environ["HOME"], "suma_config.yaml")
    with open(path) as f:
        login = yaml.load_all(f, Loader=yaml.FullLoader)
        for a in login:
            login = a

    return login

def login_suma(login):
    MANAGER_URL = "http://"+ login['suma_host'] +"/rpc/api"
    MANAGER_LOGIN = login['suma_user']
    MANAGER_PASSWORD = login['suma_password']
    SUMA = "http://" + login['suma_user'] + ":" + login['suma_password'] + "@" + login['suma_host'] + "/rpc/api"
    with ServerProxy(SUMA) as session_client:

    #session_client = xmlrpclib.Server(MANAGER_URL, verbose=0)
        session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
    return session_client, session_key

def find_delete_system(systemname, session, key, uuid=""):
    try_delete_minion = True
    try:
        systemlist = session.system.listSystems(key)
    except:
        print("get system list failed.")
    if len(systemlist) > 0:
        for i in systemlist:
            if uuid != "":
                uuid = uuid.replace("-", "")
                ret_uuid = session.system.getUuid(key, i['id'])
                
                if uuid.strip('-') in ret_uuid:
                    try:
                        session.system.deleteSystem(key, i['id'])
                        print("Found existing VM uuid. It will be deleted: %s %s" % (uuid, i['name']))
                    except:
                        print("delete system failed: %s" % i['name'])
                    try_delete_minion = False
                
            elif systemname in i['name']:
                print("found existing system that will be deleted. %s" % i['name'])
                try:
                    session.system.deleteSystem(key, i['id'])
                except:
                    print("delete system failed: %s" % i['name'])
                try_delete_minion = False
    
    if try_delete_minion:
        delete_salt_minion(systemname)        
    return

def suma_logout(session, key):
    session.auth.logout(key)
    return


def delete_salt_minion(minion_name):
    opts = salt.config.master_config('/etc/salt/master.d/susemanager.conf')
    wheel = salt.wheel.WheelClient(opts)
    minion_pre_list = wheel.cmd('key.list', ['pre'])
    
    if len(minion_pre_list['minions_pre']) > 0:
        for p in minion_pre_list['minions_pre']:
            if minion_name in p:
                p_dict = {
                    'minions_pre': [
                        p,
                    ],
                }
                print("Deleting minion from pending key accept: %s" % p_dict)
                wheel.cmd_async({'fun': 'key.delete_dict', 'match': p_dict})

    minion_denied_list = wheel.cmd('key.list', ['denied'])
    if len(minion_denied_list['minions_denied']) > 0:
        for p in minion_denied_list['minions_denied']:
            if minion_name in p:
                p_dict = {
                    'minions_denied': [
                        p,
                    ],
                }
                print("Deleting minion from denied key: %s" % p_dict)
                wheel.cmd_async({'fun': 'key.delete_dict', 'match': p_dict})
    
    minion_rejected_list = wheel.cmd('key.list', ['rejected'])
    if len(minion_rejected_list['minions_rejected']) > 0:
        for p in minion_rejected_list['minions_rejected']:
            if minion_name in p:
                p_dict = {
                    'minions_rejected': [
                        p,
                    ],
                }
                print("Deleting minion from rejected key: %s" % p_dict)
                wheel.cmd_async({'fun': 'key.delete_dict', 'match': p_dict})