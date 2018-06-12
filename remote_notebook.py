import sys
import socket
import paramiko
import argparse
import webbrowser
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--on', dest='on', required=True)
parser.add_argument('--via', dest='via')

args = parser.parse_args()
on   = args.on
via  = args.via

sock = None

if via:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.load_system_host_keys()
    client.connect(hostname=via.split('@')[-1], username=via.split('@')[0])

    transport = client.get_transport()
    sock = transport.open_channel("direct-tcpip", (on.split('@')[-1], 22), (via.split('@')[-1], 22))
else:
    sock = None

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.load_system_host_keys()
client.connect(hostname=on.split('@')[-1], username=on.split('@')[0], sock=sock)

command = '''python2 -c 'import socket, sys; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.bind(("localhost", 0)); s.listen(1); port=s.getsockname()[1]; s.close(); print port' '''
stdin, stdout, stderr = client.exec_command(command)
remote_port = int(stdout.readlines()[0])


#check jupyter availability
stdin, stdout, stderr = client.exec_command("which jupyter-notebook")
if "not found" in stderr.read():
    raise FileExistsError("jupyter not found")

try:
    remote_notebook_command = 'tmux new-session -d -s remote_jupyter "jupyter-notebook --no-browser --port={}"'.format(remote_port)

    stdin, stdout, stderr = client.exec_command(remote_notebook_command)
    error_message = stderr.read()    
    
    if "not found" in error_message:
        raise FileNotFoundError("tmux not found")
    
    if "duplicate" in error_message:
        raise ValueError("Session Already exists")

except ValueError:
    stdin, stdout, stderr = client.exec_command("jupyter-notebook list")
    lines = stdout.readlines()
    print lines
    remote_port = int(lines[1].split("localhost:")[-1].split("/")[0])
    print remote_port
client.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('localhost', 0))
s.listen(1)
local_port = s.getsockname()[1]
s.close()

local_notebook_command = 'ssh -N -f -L localhost:{}:localhost:{} {}'.format(local_port, remote_port, on)
subprocess.call(local_notebook_command, shell=True)
webbrowser.open('http://localhost:{}'.format(local_port))

