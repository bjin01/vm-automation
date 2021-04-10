import base64
import sys
import paramiko
import base64
from binascii import hexlify
import getpass
import os

#key = paramiko.RSAKey(data=base64.b64decode(b'AAA...'))
client = paramiko.SSHClient()
#client.get_host_keys().add('ssh.example.com', 'ssh-rsa', key)

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

if hostname.find(":") >= 0:
    hostname, portstr = hostname.split(":")
    port = int(portstr)

default_path = os.path.join(os.environ["HOME"], ".ssh", "id_rsa")
default_pubkey_path = os.path.join(os.environ["HOME"], ".ssh", "id_rsa.pub")
path = ""
if len(sys.argv) > 2:
    path = sys.argv[2]
if path == "":
    path = default_path

print(path)
try:
    key = paramiko.RSAKey.from_private_key_file(path)
except paramiko.PasswordRequiredException:
    password = getpass.getpass("RSA key password: ")
    key = paramiko.RSAKey.from_private_key_file(path, password)

print(username, hostname, key)

client.connect(hostname, username=username, key_filename=default_pubkey_path)
stdin, stdout, stderr = client.exec_command('ls')
for line in stdout:
    print('... ' + line.strip('\n'))
client.close()