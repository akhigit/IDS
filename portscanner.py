##############################################################################
# This file contains code for network/device scanning                        #
#                                                                            #
# File Name: portscanner.py                                                  #
# Author: Akhilesh Srivastava                                                #
##############################################################################

import shutil
import os

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser

from helper import ip, lock_xml


def scan_hosts(filename, available_hosts, task_id):
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

    extended_filename = filename + str(task_id)
    try:
        print 'About to start scan!'
        nmap_proc = \
        NmapProcess(targets=available_hosts,
                    options="-PN -n -T4 -O -oX "+extended_filename, safe_mode=False)
    except:
        print("Exception raised while scanning!")

    if nmap_proc.run():
        print "Nmap scan failed!!"

    lock_xml.acquire()
    shutil.copy2(extended_filename, filename)
    os.remove(extended_filename)
    lock_xml.release()

    print "Nmap scanning finished!!"


def list_hosts(mask):
    """
    Finds hosts in the network.

    Args:
        mask (str): The subnet mask signifying the subnet to be scanned.

    Returns:
        A list of hosts that respond to a ping-based fast scan.
        Null if scan fails.

    Raises:
        Nothing
    """

    global ip
    hosts = []
    nmap_proc = NmapProcess(targets=ip+"/"+mask, options="-F", safe_mode=False)

    if not nmap_proc.run():
        for host in NmapParser.parse(nmap_proc.stdout).hosts:
            if host.is_up():
                hosts.append(host.address)
    else:
        print "Nmap scan failed"

    return hosts
