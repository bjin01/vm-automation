import base64
import paramiko
key = paramiko.RSAKey(filename="/root/.ssh/id_rsa")
client = paramiko.SSHClient()
client.get_host_keys().add('192.168.122.153', 'ssh-rsa', key)
client.connect('192.168.122.153', username='root', password='test')
stdin, stdout, stderr = client.exec_command('ls')
for line in stdout:
    print('... ' + line.strip('\n'))
client.close()