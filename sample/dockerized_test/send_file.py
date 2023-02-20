# ----- sender.py ------

# !/usr/bin/env python

from socket import *
import sys
import os
import argparse


def sendFile(filename, addr):
    s = socket(AF_INET, SOCK_DGRAM)
    s.sendto(file_name, addr)

    f = open(file_name, "rb")
    data = f.read(buf)
    while (data):
        if (s.sendto(data, addr)):
            print("sending ...")
            data = f.read(buf)
    s.close()
    f.close()


OPOT_CONTROLLER_IP = os.environ['OPOT_CONTROLLER_IP']
NETWORK_IP = os.environ['NETWORK_IP']
endpoint = f'http://{OPOT_CONTROLLER_IP}:8080/api/v2/'
PATH_CREATE = 'pot/controller/path'
PATH_DESTROY = 'pot/controller/path/{uuid}'

parser = argparse.ArgumentParser(description='opot_sdk')
parser.add_argument('path', metavar='path', help="File with the path in json format.")
parser.add_argument('file', metavar='file', help="File to send.")
t = parser.parse_args()



addr = (host, port)

