from net_config import *
import shlex
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser

def scan_hosts(filename, available_hosts):
    """
    Available hosts: iterable of hostnames (names or IP addresses) that respond to a network.
    Returns iterable of open port numbers, possible os, devices for each available host.
    """
    try:
        print 'About to start scan!'
        nmap_proc = \
        NmapProcess(targets=available_hosts,
                    options="-PN -n -T4 -O -oX "+filename, safe_mode=False)
    except:
        print("Exception raised while scanning!")

    if nmap_proc.run():
        print "Nmap scan failed!!"
    print "Nmap scanning finished!!"

def list_hosts(ip, mask):

    hosts = []
    nmap_proc = NmapProcess(targets=ip+"/"+mask, options="-F", safe_mode=False)

    if not nmap_proc.run():
        for host in NmapParser.parse(nmap_proc.stdout).hosts:
            if host.is_up():
                hosts.append(host.address)
    else:
        print "Nmap scan failed"

    return hosts
