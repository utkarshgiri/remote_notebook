import sys
import socket
import argparse
import webbrowser
import subprocess
import invoke
from fabric import Config, Connection

parser = argparse.ArgumentParser()
parser.add_argument('--on', dest='on', required=True)
parser.add_argument('--path', dest='path')
args = parser.parse_args()
on   = args.on
path = args.path

client = Connection(host=on.split('@')[-1], user=on.split('@')[0], forward_agent=True)


command = '''python2 -c 'import socket, sys; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.bind(("localhost", 0)); s.listen(1); port=s.getsockname()[1]; s.close(); print port' '''

remote_port = int("{.stdout}".format(client.run(command)))

if path:
    remote_notebook_command = 'tmux new-session -d -s remote_jupyter "{} --no-browser --port={}"'.format(path, remote_port)
else:
    remote_notebook_command = 'tmux new-session -d -s remote_jupyter "/home/ugiri/miniconda3/bin/jupyter-notebook --no-browser --port={}"'.format(remote_port)

try:
    result = client.run(remote_notebook_command)
except invoke.exceptions.UnexpectedExit:
    result = client.run("/home/ugiri/miniconda3/bin/jupyter-notebook list")
    lines = "{.stdout}".format(result)
    remote_port = int(lines.split("localhost:")[-1].split("/")[0])

result = client.run("/home/ugiri/miniconda3/bin/jupyter-notebook list")
lines = "{.stdout}".format(result)
remote_token = (lines.split("::")[0].split("/")[-1])
client.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('localhost', 0))
s.listen(1)
local_port = s.getsockname()[1]
s.close()
local_notebook_command = 'ssh -N -f -L localhost:{}:localhost:{} {}'.format(local_port, remote_port, on)
subprocess.call(local_notebook_command, shell=True)
webbrowser.open('http://localhost:{}/{}'.format(local_port, remote_token))

