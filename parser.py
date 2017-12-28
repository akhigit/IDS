#import BeautifulSoup
import json
import cPickle as pickle
import os
from netaddr import IPNetwork
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser
from net_config import *
from mongo_ops import *
from setup import *

def get_node_mac(host):
    """
    Takes in a single NMAP XML host as a string.
    Outputs a string containing the node's mac address.
    """

    mac_address = host.find("address").nextSibling
    address = repr(mac_address)
    if 'addrtype="mac"' in address:
        host_id = address.split('\n')[0].split('"')[1]
        return host_id

def get_device_type(ip):
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
    try:
        entry = unicode(entry, 'utf-8')
    except TypeError:
        return entry


def get_open_port_numbers(host):
    """
    Takes in one Beautiful Soup object.
    Returns a list of a host's open ports).
    """
    ports_per_host =[]
    for h in host:
        ports = h.findAll("port")
        for port in ports:
            port_id = check_if_unicode(port["portid"])
            ports_per_host.append(port_id)
        return ports_per_host

def get_ports_services(host):
    """
    Takes in one Beautiful Soup object.
    Returns a list of services running a host's open port(s).
    """
    services_per_host =[]
    for service in host.services:
        port_service = service.service+" "+service.protocol+\
                       " "+repr(service.port)
        services_per_host.append(port_service)
    return services_per_host

def get_ip_address(host):
    """
    Takes in one Beautiful Soup object.
    Returns a string of the IP value.
    """
    for h in host:
        ip = h.address['addr']
        return ip

def get_os_class(host):
    """
    Takes in one Beautiful Soup object.
    Returns a string for an OSMatch value.
    """
    for h in host:
        os_class = h.osclass
        if os_class is not None:
            os_class = str(os_class)
            string_os_class = os_class.split('"')[1].split('"')[0]
            return string_os_class
        else:
            return "No OS class available."

def get_os_match(os_strs):
    """
    Takes in a host object.
    Returns a string for an OSMatch value.
    """
    if len(os_strs) > 1:
        return os_strs[1]
    else:
        return "No OS version available."

def get_os_type(os_strs):
    """
    Takes in a host object.
    Returns a string for an OSType value.
    """
    if len(os_strs) > 2:
        return os_strs[2]
    else:
        return "No OS type available"

def make_dictionaries(hosts):
    node_list = []
    n_dict = {}
    json_blob_dictionary = {}
    node_dictionary = {}

    for h in hosts:
        n_dict = create_nodes_dictionary(h)
        node_list.append(n_dict)
    return node_list


def get_common_hop_dist(ip, hosts):

    """
    function takes a list of hosts.
    Returns a dictionary of indices that share a nw.
    """
    common_hop_dist_dict = {}
    itr = 0

    for h in hosts:
        if not h.is_up():
            hop_dist_key = 'inf'
        else:
            hop_dist_key = h.distance

        # The value of distance for remote
        # nodes is wrongly parsed as 0.
        if (not hop_dist_key and h.address != ip):
            hop_dist_key = 'inf'

        if hop_dist_key in common_hop_dist_dict:
            common_hop_dist_dict[hop_dist_key].append(itr)
        else:
            common_hop_dist_dict[hop_dist_key] = [itr]

        itr += 1
    print common_hop_dist_dict
    return common_hop_dist_dict


def get_all_possible_nw_pairings(hop_dict):

    """
    Takes in a dictionary. Key represents the hop-distance
    and value represents the host-index.
    Returns a list of all possible pairings between hosts.
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
    Takes in all possible pairings of indices that are in
    the same subnet.
    Returns dictionary of sources and targets.
    """

    source_target_dictionary = {}
    links_list = []

    itr = 0

    for pair in index_pairings:
        source = pair[0]
        target = pair[1]

        source_target_dictionary = {"source":source, "target":target}
        links_list.append(source_target_dictionary)

    return links_list

def gen_dict_list_from_file(json_filename):
    dict_list = []
    lines = []
    try:
        with open('feature_dictionary.json', 'r') as json_file:
            for line in json_file:
                lines.append(json.loads(line))

            for data in lines:
                feature_dictionary = {}
                for entry in data:
                    feature_dictionary[str(entry)] = str(data[entry])
                dict_list.append(feature_dictionary)
    except:
        pass
    return dict_list

def fill_missing_entries(node_dict):
    feature_dict_list = gen_dict_list_from_file('feature_dictionary.json')
    if len(feature_dict_list) > 0:
        for feature_dict in feature_dict_list:
            if not feature_dict:
                if node_dict['IP'] == feature_dict['ip']:
                    if node_dict.get('Id') is None:
                        node_dict['Id'] = feature_dict['mac_address']

def create_nodes_dictionary(h):
    node_dictionary = {}
    if h.mac:
        node_dictionary['Id'] = h.mac
    elif h.address == ip: # Nmap does not return MAC address for the localhost
        node_dictionary['Id'] = mac
    else:
        node_dictionary['Id'] = "Not Available"
    node_dictionary['IP'] = h.address
    node_dictionary['OpenPorts'] = h.get_open_ports()
    #node_dictionary['Links'] = [get_os_match(h), get_ports_services(h)]
    node_dictionary['PortServices'] = get_ports_services(h)
    os_strs = str(h.os).split('\n')
    node_dictionary['OSMatch'] =  get_os_match(os_strs)
    node_dictionary['group'] = get_device_type(h.address)
    node_dictionary['OSType'] = get_os_type(os_strs)

    fill_missing_entries(node_dictionary)

    return node_dictionary

def modification_date(filename):
    time_stamp = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

def parse(pathname, mode):
    try:
        print "About to acquired host_json_files lock"
        lock_host_json_files.acquire()
        print "Acquired host_json_files lock"
        host_list = []
        host_list_file = hosts_list_file
        if mode == 'w' or not os.path.isfile(host_list_file):
            xml_parsed = NmapParser.parse_fromfile(pathname)
            new_host_list = xml_parsed.hosts
            if os.path.isfile(host_list_file):
                host_list_file_handle = open(host_list_file, 'rb')
                host_list = pickle.load(open(host_list_file, 'rb'))
                is_new_host = True
                for new_host_address in new_host_list:
                    for host in host_list:
                        if host.address == new_host_address:
                            is_new_host = False
                            break
                    if is_new_host:
                        host_list.append(new_host_address)
                host_list_file_handle.close()
            host_list_file_handle = open(host_list_file, 'wb')
            pickle.dump(host_list, host_list_file_handle, protocol=pickle.HIGHEST_PROTOCOL)
            host_list_file_handle.close()
        elif mode == 'a':
            host_list = pickle.load(open(host_list_file, 'rb'))
            new_host = NmapParser.parse_fromfile(pathname).hosts[0]
            new_host_address = new_host.address
            is_new_host = True
            for host in host_list:
                if host.address == new_host_address:
                    is_new_host = False
                    break
            if is_new_host:
                host_list.append(new_host)
                host_list_file_handle = open(host_list_file, 'w')
                pickle.dump(host_list, host_list_file_handle)
                host_list_file_handle.close()
        else:
            lock_host_json_files.release()
            return

        print host_list
        pairings = get_common_hop_dist(str(ip), host_list)

        pairs = get_all_possible_nw_pairings(pairings)

        links = get_sources_and_targets(pairs)

        json_blob_dictionary = {}
        json_blob_dictionary = {"nodes" : make_dictionaries(host_list), "links" : links}

        json_file_handle = open(hosts_json_file, 'w')
        json.dump(json_blob_dictionary, json_file_handle)
        lock_host_json_files.release()
    except:
        print "host_json_files lock Already Acquired"
