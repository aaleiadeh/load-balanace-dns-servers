import socket
import argparse
from sys import argv
import hashlib

def loadbalance(hostname):
    return (hashlib.md5(hostname.encode('utf-8')).digest()[0]%2)


parser = argparse.ArgumentParser()
parser.add_argument('lsport', type=int, help='This is the port to connect to the LSserver on',action='store')
parser.add_argument('ts1domain', type=str, help='This is the domain name or ip address of the ts1server',action='store')
parser.add_argument('ts1port', type=int, help='This is the port to connect to the ts1server on',action='store')
parser.add_argument('ts2domain', type=str, help='This is the domain name or ip address of the ts2server',action='store')
parser.add_argument('ts2port', type=int, help='This is the port to connect to the ts2server on',action='store')
args = parser.parse_args(argv[1:])

try:
    print("Creating Sockets")
    lssocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("LS Server socket created")
    ts1socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("TS1 Client socket created")
    ts2socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("TS2 Client socket created")
except socket.error as err:
    print(err)
    exit()

print("Awaiting Connecting")
serveraddress = ('', args.lsport)
lssocket.bind(serveraddress)
lssocket.listen(1)
csocket, caddress = lssocket.accept()
print("Connection Established")

ts1address = (args.ts1domain, args.ts1port)
ts2address = (args.ts2domain, args.ts2port)
ts1socket.connect(ts1address)
ts2socket.connect(ts2address)
ts1socket.settimeout(5)
ts2socket.settimeout(5)
with csocket:
    while True:
        data = csocket.recv(512)
        data = data.decode('utf-8')
        if not data:
            break

        balance = loadbalance(data)
        response = ''
        if(balance):#uses TS1
            try:
                ts1socket.sendall(data.encode('utf-8'))
                response = ts1socket.recv(512)
                response = response.decode('utf-8')
                if (response.split(':')[0] != data):#TS delay causes mismatch because of previous query. Retry
                    print("TS1 Mismatch: " + response.split(':')[0] + ':' + data)
                    ts1socket.sendall(data.encode('utf-8'))
                    response = ts1socket.recv(512)
                    response = response.decode('utf-8')
            except:#TS1 Timeout, try TS2
                try:
                    ts2socket.sendall(data.encode('utf-8'))
                    response = ts2socket.recv(512)
                    response = response.decode('utf-8')
                    if (response.split(':')[0] != data):
                        print("TS2 Mismatch: " + response.split(':')[0] + ':' + data)
                        ts2socket.sendall(data.encode('utf-8'))
                        response = ts2socket.recv(512)
                        response = response.decode('utf-8')
                except:#Both Timeout
                    response = data + " - Error:HOST NOT FOUND"
        else:#uses TS2
            try:
                ts2socket.sendall(data.encode('utf-8'))
                response = ts2socket.recv(512)
                response = response.decode('utf-8')
                if (response.split(':')[0] != data):
                    print("TS1 Mismatch: " + response.split(':')[0] + ':' + data)
                    ts2socket.sendall(data.encode('utf-8'))
                    response = ts2socket.recv(512)
                    response = response.decode('utf-8')
            except:
                try:
                    ts1socket.sendall(data.encode('utf-8'))
                    response = ts1socket.recv(512)
                    response = response.decode('utf-8')
                    if (response.split(':')[0] != data):
                        print("TS2 Mismatch: " + response.split(':')[0] + ':' + data)
                        ts1socket.sendall(data.encode('utf-8'))
                        response = ts1socket.recv(512)
                        response = response.decode('utf-8')
                except:
                    response = data + " - Error:HOST NOT FOUND"
        response = response.split(':')[1]
        if (response == "OTHER"):
            response = data + " - Error:HOST NOT FOUND"
        csocket.sendall(response.encode('utf-8'))
        print("Sent IP of " + data + " to Client:", response)

ts1socket.close()
ts2socket.close()