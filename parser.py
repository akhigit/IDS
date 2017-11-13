import BeautifulSoup
import json
import os
from netaddr import IPNetwork
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser

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

def get_group_number_from_name(name):
    if "iPhone" in name:
        return 1
    elif "Linux" in name:
        return 2
    elif "Microsoft Windows" in name:
        return 3
    elif "Apple Mac OS X" in name:
        return 4
    else:
        return 5

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
        if not h.is_up():
            continue
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
            continue;

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


def create_nodes_dictionary(h):
    node_dictionary = {}

    node_dictionary['Id'] = h.mac
    node_dictionary['IP'] = h.address
    node_dictionary['OpenPorts'] = h.get_open_ports()
    #node_dictionary['Links'] = [get_os_match(h), get_ports_services(h)]
    node_dictionary['PortServices'] = get_ports_services(h)
    os_strs = str(h.os).split('\n')
    node_dictionary['OSMatch'] =  get_os_match(os_strs)
    node_dictionary['group'] = get_group_number_from_name(
                                node_dictionary['OSMatch'])
    node_dictionary['OSType'] = get_os_type(os_strs)

    return node_dictionary

def get_links(hosts):
    links_list = []
    for h in hosts:
        link = create_nodes_dictionary(h)['Links']
        links_list.append(link)
    return links_list


def modification_date(filename):
    time_stamp = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)


def main(ip, pathname):
    print "Nmap parsing started!!"
    xml_parsed = NmapParser.parse_fromfile(pathname)

    pairings = get_common_hop_dist(str(ip), xml_parsed.hosts)

    pairs = get_all_possible_nw_pairings(pairings)

    links = get_sources_and_targets(pairs)

    json_blob_dictionary = {}
    json_blob_dictionary = {"nodes" : make_dictionaries(xml_parsed.hosts), "links" : links}


    file_output = open("static/json_dictionary.json", "w")
    json.dump(json_blob_dictionary, file_output)


if __name__ == '__main__':
    main("static/nmap_raw.xml")
