import sys, socket, select, ipaddress, psutil
from subprocess import *
import os
import netifaces as nif

def get_IP():
    'Finds and returns the local IP address as dotted-quad ints on my host computer.'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # google public dns
    s.connect(('8.8.8.8',53))
    ip = s.getsockname()[0]
    print 'this is the ip', ip
    s.close()
    return ip

def get_host_mac():
    'Returns a list of MACs for interfaces that have given IP, returns None if not found'
    global ip
    for i in nif.interfaces():
        addrs = nif.ifaddresses(i)
        try:
            if_mac = addrs[nif.AF_LINK][0]['addr']
            if_ip = addrs[nif.AF_INET][0]['addr']
        except (IndexError, KeyError) as e: #ignore ifaces that dont have MAC or IP
            if_mac = if_ip = None
        if if_ip == ip:
            return if_mac
    return None


ip = get_IP()
mac = str(get_host_mac())
