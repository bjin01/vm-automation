#!/usr/bin/python

import yaml
import os
import xmlrpclib

def get_login(path):
    
    if path == "":
        path = os.path.join(os.environ["HOME"], "suma_config.yaml")
    print(path)
    with open(path) as f:
        #print(path)
        login = yaml.load_all(f, Loader=yaml.FullLoader)
        for a in login:
            login = a

    return login

def login_suma(login):
    MANAGER_URL = "http://"+ login['suma_host'] +"/rpc/api"
    MANAGER_LOGIN = login['suma_user']
    MANAGER_PASSWORD = login['suma_password']

    session_client = xmlrpclib.Server(MANAGER_URL, verbose=0)
    session_key = session_client.auth.login(MANAGER_LOGIN, MANAGER_PASSWORD)
    return session_client, session_key

def find_delete_system(systemname, session, key):
    try:
        systemlist = session.system.listSystems(key)
    except:
        print("get system list failed.")
    if len(systemlist) > 0:
        for i in systemlist:
            if systemname in i['name']:
                print("found existing system that will be deleted. %s" % i['name'])
                try:
                    session.system.deleteSystem(key, i['id'])
                except:
                    print("delete system failed: %s" % i['name'])
    session.auth.logout(key)
    return


