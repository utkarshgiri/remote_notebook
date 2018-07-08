import sys
import time
import invoke
import socket
import argparse
import subprocess
import webbrowser
from fabric import Config, Connection

parser = argparse.ArgumentParser()
parser.add_argument('--on', dest='on', required=True)
parser.add_argument('--kill', dest='kill', action='store_const', const=True)
args = parser.parse_args()


client = Connection(host=args.on.split('@')[-1],
                    user=args.on.split('@')[0],
                    forward_agent=True)

if args.kill:
    try:
        client.run('tmux kill-session -t remote_jupyter')
    except:
        print "Nothing to kill"
    sys.exit()
        
try:
    path = '{.stdout}'.format(client.run('source ~/.zshrc; which jupyter-notebook')) 
except invoke.exceptions.UnexpectedExit:
    raise Exception('jupyter-notebook not found')


try:
    client.run('source ~/.zshrc; which tmux')
except invoke.exceptions.UnexpectedExit:
    raise Exception('tmux not found')


remote_notebook_command = '''tmux new-session -d -s remote_jupyter %s '''%(path)

try:
    notebook = client.run(remote_notebook_command)
except invoke.exceptions.UnexpectedExit:
    pass

notebook_list = client.run('source ~/.zshrc; jupyter-notebook list')
lines = "{.stdout}".format(notebook_list)
remote_port = lines.split('localhost:')[-1].split('/')[0]
remote_token = (lines.split("token=")[-1].split("::")[0])
client.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('localhost', 0))
s.listen(1)
local_port = s.getsockname()[1]
s.close()
local_notebook_command = 'ssh -N -f -L localhost:{}:localhost:{} {}'\
                          .format(local_port, remote_port, args.on)

subprocess.call(local_notebook_command, shell=True)

url='http://localhost:{}/?token={}'.format(local_port, remote_token)
webbrowser.open(url=url)
