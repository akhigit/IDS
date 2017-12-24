from net_config import *
import shlex
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser

def scan_hosts(filename, available_hosts):
    """
    Runs a deep scan on host(s).

    Args:
        filename (str): The file to write the result of deep scan.
        available_hosts (list): The list of hosts to be deep-scanned.

    Returns:
        Nothing.

    Raises:
        Any exception that occurs while scanning.
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
    """
    Finds hosts in the network.

    Args:
        ip (str): The IP address of the scanner.
        mask (str): The subnet mask signifying the subnet to be scanned.

    Returns:
        A list of hosts that respond to a ping-based fast scan.
        Null if scan fails.

    Raises:
        Nothing
    """

    hosts = []
    nmap_proc = NmapProcess(targets=ip+"/"+mask, options="-F", safe_mode=False)

    if not nmap_proc.run():
        for host in NmapParser.parse(nmap_proc.stdout).hosts:
            if host.is_up():
                hosts.append(host.address)
    else:
        print "Nmap scan failed"

    return hosts
