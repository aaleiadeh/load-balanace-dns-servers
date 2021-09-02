import binascii
import socket
import argparse
from sys import argv
#All code from here to end of 'getHost' helper method is code from Project 2 with relevant sources cited
def sendmsg(message, address, port): #Referenced code from 'https://routley.io/posts/hand-writing-dns-messages/'
    message = message.replace(" ", "").replace("\n", "")
    serveraddress = (address, port)
    try:
        ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ss.sendto(binascii.unhexlify(message), serveraddress)
        data, _ = ss.recvfrom(4096)
    finally:
        ss.close()
    return binascii.hexlify(data).decode("utf-8")

def urlToHex(msg):
    list = msg.split('.')
    data = []
    for item in list:
        length = len(item)
        data.append(format(length, '02x'))
        for i in item.lower():
            data.append(format(ord(i), '02x'))
    data.append('00 00 01 00 01')
    return ' '.join(data)

def hexToIP(val):
    if val == 'OTHER':
        return val
    list = [val[i:i+2] for i in range(0, len(val), 2)]
    declist = []
    for i in list:
        dec = str(int(i, 16))
        declist.append(dec)
    return '.'.join(declist)

def getHost(hostname):
    header = 'AA AA 01 00 00 01 00 00 00 00 00 00 '  # Used from code shown in recitation
    request = header + urlToHex(hostname)
    requestLength = (len(request.replace(" ", "")))
    #print(request)
    response = sendmsg(request, '1.1.1.1', 53)
    #print(response)
    answer = response[requestLength:]
    #print(answer)

    answerList = []
    ipList = []
    while (answer):
        record = int(answer[4:8])
        answer = answer[20:]
        length = int(answer[0:4], 16)
        answer = answer[4:]

        if record != 1:
            answerList.append('OTHER')
            answer = answer[length * 2:]
            continue

        ip = answer[0:length * 2]
        answerList.append(ip)
        answer = answer[length * 2:]
    for i in answerList:
        ipList.append(hexToIP(i))
    data = ','.join(ipList)
    #print(data)
    return data

parser = argparse.ArgumentParser()
parser.add_argument('port', type=int, help='This is the port to connect to the server on',action='store')
args = parser.parse_args(argv[1:])

try:
    print("Attempting to create server socket")
    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error as err:
    print(err)
    exit()

serveraddress = ('', args.port)
ss.bind(serveraddress)
ss.listen(1)
print("Awaiting Connection")
csocket, caddress = ss.accept()
print("Connection established")
#exit()
dnstable = []
with csocket:
    while True:
        answer = ''
        try:
            data = csocket.recv(512)
        except:
            print("Client closed connection")
            break
        data = data.decode('utf-8')
        if not data:
            break
        print("Received:",data)
        for list in dnstable:
            if data.lower() == list[0].lower():
                answer = ':'.join(list)
                print("Hit:", data)
                break
        if not answer:
            newentry = []
            newentry.append(data)
            newentry.append(getHost(data))
            dnstable.append(newentry)
            answer = ':'.join(newentry)
        try:
            csocket.sendall(answer.encode('utf-8'))
            print("Sent:", answer)
        except:
            print("Client closed connection")
            break