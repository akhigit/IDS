##############################################################################
# This file contains code for finding the IP and MAC addresses of the        #
# network scanner machine                                                    #
#                                                                            #
# File Name: helper.py                                                       #
# Author: Akhilesh Srivastava                                                #
##############################################################################

import sys, os, socket, ipaddress

import netifaces as nif
from redlock import RedLock


#### Defining locks ####
# For the xml file having the result of the the deep-scan
lock_xml = RedLock("xml_lock")

# For the host_list and json files that are used for the rendering
# the network map
lock_host_json_files = RedLock("host_json_files_lock")


#### Decorator to execute a function only once ####
def run_once(func):
    def wrapper():
        if not wrapper.has_run:
            wrapper.has_run = True
            return func()
    wrapper.has_run = False
    return wrapper


def remove_resource_files():
    """
    Removes previously generated resource files

    Args:
        None

    Returns:
        None

    Raises:
        Nothing
    """
    lock_host_json_files.acquire()
    # Two xml files are used for storing the result of the deep-scan
    if os.path.isfile('static/nmap_raw1.xml'):
        os.remove('static/nmap_raw1.xml') # for manually intiated deep-scan
    if os.path.isfile('static/nmap_raw2.xml'):
        os.remove('static/nmap_raw2.xml') # deep-scan set off by host-discovery

    # stores NmapParser objects representing deep-scanned hosts
    if os.path.isfile('static/hosts_list_file.list'):
        os.remove('static/hosts_list_file.list')

    # stores a json string containing the relevant information about the hosts
    # and the network. This information is used for rendering the network map
    if os.path.isfile('static/json_dictionary.json'):
        os.remove('static/json_dictionary.json')

    # an indicator file used to determine whether or not to combine the results
    # of manully initiated and host-discovery triggered deep-scans. The two
    # results need to be combined when a celery worker finishes a host-discovery
    # triggered deep-scan while another worker still busy with manual scanning
    # misses to discover the said host.
    if os.path.isfile('combine_results_indicator'):
        os.remove('combine_results_indicator')
    lock_host_json_files.release()


@run_once
def get_IP():
    """
    Finds the ip address of the network scanner. Care needs to be taken that
    the device does not have more than 1 wireless interface.

    Args:
        Nothing

    Returns:
        The ip address of the wireless interface used for network scanning.

    Raises:
        Nothing
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('8.8.8.8',53)) # google's public dns
    ip = s.getsockname()[0]
    print 'this is the ip', ip
    s.close()
    return ip


@run_once
def get_host_mac():
    """
    Finds the mac address of the network scanner. Care needs to be taken that
    the device does not have more than 1 wireless interface.

    Args:
        Nothing

    Returns:
        The mac address of the wireless interface used for network scanning.

    Raises:
        IndexError, KeyError
    """
    global ip
    for i in nif.interfaces():
        addrs = nif.ifaddresses(i)
        try:
            if_mac = addrs[nif.AF_LINK][0]['addr']
            if_ip = addrs[nif.AF_INET][0]['addr']
        except (IndexError, KeyError) as e: #ignore ifaces with no MAC or IP
            if_mac = if_ip = None
        if if_ip == ip:
            return if_mac
    return None


#### Finding the ip and mac addresses of the network scanner ####
ip = get_IP()
mac = str(get_host_mac())
