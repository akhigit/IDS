##############################################################################
# This file contains code for parsing the XML file generated upon completion #
# of the deep scan, and creates a JSON file used by the front-end for        #
# rendering the network map.                                                 #
#                                                                            #
# File Name: parser.py                                                       #
# Author: Akhilesh Srivastava                                                #
##############################################################################

import os
import json
import cPickle as pickle

from netaddr import IPNetwork
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser

from helper import ip, mac, lock_host_json_files
from mongo_ops import *


def get_node_mac(host):
    """
    Takes in a single NMAP XML host as a string.
    Outputs a string containing the node's mac address.

    Args:
        host(NmapParser object): The object representing a scanned host.

    Returns:
        Mac address of the host.

    Raises:
        Nothing.
    """

    mac_address = host.find("address").nextSibling
    address = repr(mac_address)
    if 'addrtype="mac"' in address:
        host_id = address.split('\n')[0].split('"')[1]
        return host_id

def get_device_type(ip):
    """
    Takes a host's ip address and returns device type information
    (IoT, Non-IoT or N/A when this information is unavailable).

    Args:
        ip(str): IP address of the host.

    Returns:
        Device type identifier, 1 for IoT, 2 for Non-IoT, 3 for N/A.

    Raises:
        Nothing.
    """

    device = devices.find_one({'ip_address':ip})
    if device:
        if device.has_key('IoT'):
            is_IoT = device['IoT']
            if is_IoT:
                return 1
            else:
                return 2
        else:
            return 3
    else:
        return 3

def check_if_unicode(entry):
    """
    Converts a string object to unicode using the 'utf-8'
    encoding scheme and returns the result.

    Args:
        entry(str): The base string to be converted.

    Returns:
        Unicode converted value of the base string.

    Raises:
        TypeError exception if the input is not a valid string,
    """
    try:
        entry = unicode(entry, 'utf-8')
    except TypeError:
        return entry


def get_open_port_numbers(host):
    """
    Takes a host object and returns a list of a host's open ports.

    Args:
        host(NmapParser object): The object representing a scanned host

    Returns:
        A list of open ports

    Raises:
        Nothing
    """

    ports_per_host =[]
    for host in host:
        ports = host.findAll("port")
        for port in ports:
            port_id = check_if_unicode(port["portid"])
            ports_per_host.append(port_id)
        return ports_per_host

def get_ports_services(host):
    """
    Takes a host object and returns a list of a services running on the host.

    Args:
        host(NmapParser object): The object representing a scanned host.

    Returns:
        A list of services running on the host.

    Raises:
        Nothing
    """

    services_per_host =[]
    for service in host.services:
        port_service = service.service+" "+service.protocol+\
                       " "+repr(service.port)
        services_per_host.append(port_service)
    return services_per_host

def get_ip_address(host):
    """
    Takes a host object and returns its IP address.

    Args:
        host(NmapParser object): The object representing a scanned host.

    Returns:
        The host's ip address

    Raises:
        Nothing
    """

    for host in host:
        ip = host.address['addr']
        return ip

def get_os_match(os_strs):
    """
    Takes a list of strings representing different aspects of the OS
    information and returns the OS runing on the host.

    Args:
        os_strs(a list of strings): A list representing different aspects of
        the host's OS information, namely family, type, version, and so on.

    Returns:
        The OS family running on the host.

    Raises:
        Nothing
    """

    if len(os_strs) > 1:
        return os_strs[1]
    else:
        return "No OS version available."


def make_dictionaries(hosts):
    """
    Takes a list of host object and returns a list of dictionaries containing
    relevant information about the hosts

    Args:
        host(NmapParser object): The object representing a scanned host.

    Returns:
        A list of dictionaries where each entry contains all the relevant host
        information such as IP address, MAC address, Open ports and OS.

    Raises:
        Nothing
    """

    node_list = []
    n_dict = {}
    json_blob_dictionary = {}
    node_dictionary = {}

    for host in hosts:
        n_dict = create_nodes_dictionary(host)
        node_list.append(n_dict)
    return node_list


def get_hop_dist_from_scanner(ip, hosts):
    """
    Takes the ip address of the network scanner, a list of host objects
    obtained from the deep scan and returns a dictionary linking hosts
    with their respective hop-distances from the scanner.

    Args:
        ip (str): IP address of the network scanner node
        host (a list of NmapParser object): A list of objects representing the
        deep-scanned hosts.

    Returns:
        A dictionary with hop-distance as the key and a list of hosts having
        that hop-distance as the value

    Raises:
        Nothing
    """

    hop_dist_dict = {}
    iteration = 0

    for host in hosts:
        if not host.is_up():
            hop_dist_key = 'inf'
        else:
            hop_dist_key = host.distance

        """
        The hop distance for remote
        nodes is wrongly calculated as 0.
        """
        if (not hop_dist_key and host.address != ip):
            hop_dist_key = 'inf'

        if hop_dist_key in hop_dist_dict:
            hop_dist_dict[hop_dist_key].append(iteration)
        else:
            hop_dist_dict[hop_dist_key] = [iteration]

        iteration += 1
    print hop_dist_dict
    return hop_dist_dict


def get_all_possible_nw_pairings(hop_dict):
    """
    Takes the hop-distance dictionary created above and returns a list of
    host-pairs that are a hop-distance away.

    Args:
        hop_dict (dict): dictionary with hop-distance as the key and a list of
        hosts having that hop-distance as the value.

    Returns:
        A list of host-paris that are one-hop away from each other.

    Raises:
        Nothing
    """

    pairs = []
    key_list =  hop_dict.keys()
    print "key_list: "+str(key_list)

    if (len(key_list) > 0):
        for host_idx1 in hop_dict[key_list[0]]:
            for host_idx2 in hop_dict[key_list[0]]:
                if (key_list[0] != 'inf' and host_idx1 != host_idx2):
                    pair = host_idx1,host_idx2
                    pairs.append(pair)

    if (len(key_list) > 0):
        key_list_1 = hop_dict.keys()[:-1]
        key_list_2 = hop_dict.keys()[1:]

        for key1,key2 in zip(key_list_1, key_list_2):
            for host_idx1 in hop_dict[key2]:
                for host_idx2 in hop_dict[key2]:
                    if (key1 != 'inf' and key2 != 'inf' and
                        host_idx1 != host_idx2):
                        pair = host_idx1,host_idx2
                        pairs.append(pair)
            for host_idx1 in hop_dict[key1]:
                for host_idx2 in hop_dict[key2]:
                    if (key1 != 'inf' and key2 != 'inf' and
                        host_idx1 != host_idx2):
                        pair = host_idx1,host_idx2
                        pairs.append(pair)

    print pairs

    return pairs


def get_sources_and_targets(index_pairings):
    """
    Takes the list of host-pairs created above and returns a list of
    dictionary where every host of the pair is both a key and a value.

    Args:
        index_pairings (list): list of host-pairs that are a hop away from each
        other.

    Returns:
        A list of dictionaries where every host of the pair is both a key and
        a value. Such a dictionary is needed by the front-end for rendering
        the network map.

    Raises:
        Nothing
    """

    source_target_dictionary = {}
    links_list = []

    for pair in index_pairings:
        source = pair[0]
        target = pair[1]

        source_target_dictionary = {"source":source, "target":target}
        links_list.append(source_target_dictionary)

    return links_list


def create_nodes_dictionary(host):
    """
    Takes a host object and returns a dictionary storing the host information.

    Args:
        host (NmapParser object): The object returning a scanned host

    Returns:
        A dictionary containing the passed host's attributes such as IP address,
        MAC address, OS, open ports and services running on the host.

    Raises:
        Nothing
    """

    node_dictionary = {}
    if host.mac:
        node_dictionary['Id'] = host.mac
    elif host.address == ip: # Nmap doesn't return the localhost's MAC address
        node_dictionary['Id'] = mac
    else:
        node_dictionary['Id'] = "Not Available"
    node_dictionary['IP'] = host.address
    node_dictionary['OpenPorts'] = host.get_open_ports()
    node_dictionary['PortServices'] = get_ports_services(host)
    os_strs = str(host.os).split('\n')
    node_dictionary['OSMatch'] =  get_os_match(os_strs)
    node_dictionary['group'] = get_device_type(host.address)

    return node_dictionary


def update_json_file(hosts_list):
    """
    Takes a list of host objects and creates a json file used for rendering
    the network map on the front-end.

    Args:
        host (NmapParser object): The object returning a scanned host.

    Returns:
        Nothing

    Raises:
        Nothing
    """

    print hosts_list
    pairings = get_hop_dist_from_scanner(str(ip), hosts_list)
    pairs = get_all_possible_nw_pairings(pairings)
    links = get_sources_and_targets(pairs)
    json_blob_dictionary = {}
    json_blob_dictionary = {"nodes" : make_dictionaries(hosts_list), "links" : links}
    json_file_handle = open('static/json_dictionary.json', 'w')
    json.dump(json_blob_dictionary, json_file_handle)
    json_file_handle.close()


def parse(mode):
    """
    Takes the path of the XML created upon completion of the deep scan, an
    argument indicating whether the scanning was manually initiated or
    triggered by a host-discovery event.

    Args:
        mode (str): The argument indicating whether the scanning was manually
                    initiated ("w") or trigggerd by discovery of a
                    host ("a")

    Returns:
        Nothing

    Raises:
        Nothing
    """

    lock_host_json_files.acquire()
    hosts_list = []
    if mode == 'w' or not os.path.isfile('static/hosts_list_file.list'):
        if mode == 'w':
            xml_parsed = NmapParser.parse_fromfile('static/nmap_raw1.xml')
        else:
            xml_parsed = NmapParser.parse_fromfile('static/nmap_raw2.xml')
        new_hosts_list = xml_parsed.hosts
        if os.path.isfile('static/hosts_list_file.list') and \
           os.path.isfile("static/combine_results_indicator"):
            os.remove("static/combine_results_indicator")
            hosts_list = pickle.load(open('static/hosts_list_file.list', 'rb'))
            print "read hosts_list file"
            for new_host in new_hosts_list:
                is_new_host = True
                for host in hosts_list:
                    if host.address == new_host.address:
                        is_new_host = False
                        break
                if is_new_host:
                    hosts_list.append(new_host)
        else:
            hosts_list = new_hosts_list
        hosts_list_file_handle = open('static/hosts_list_file.list', 'w')
        pickle.dump(hosts_list, hosts_list_file_handle,
                    protocol=pickle.HIGHEST_PROTOCOL)
        hosts_list_file_handle.close()
    elif mode == 'a':
        hosts_list = pickle.load(open('static/hosts_list_file.list', 'rb'))
        new_host = NmapParser.parse_fromfile('static/nmap_raw2.xml').hosts[0]
        new_host_address = new_host.address
        is_new_host = True
        for host in hosts_list:
            if host.address == new_host_address:
                is_new_host = False
                break
        if is_new_host:
            open("static/combine_results_indicator", "w").close()
            hosts_list.append(new_host)
            hosts_list_file_handle = open('static/hosts_list_file.list', 'w')
            pickle.dump(hosts_list, hosts_list_file_handle)
            hosts_list_file_handle.close()
    else:
        lock_host_json_files.release()
        return
    update_json_file(hosts_list)
    lock_host_json_files.release()
