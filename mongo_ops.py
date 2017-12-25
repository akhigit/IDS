from pymongo import MongoClient
from pprint import pprint

client = MongoClient(connect=False, host="mongodb://IRTLab:iotsecurity@irtcluster-shard-00-00-j79ga.mongodb.net:27017,irtcluster-shard-00-01-j79ga.mongodb.net:27017,irtcluster-shard-00-02-j79ga.mongodb.net:27017/test?ssl=true&replicaSet=IRTCluster-shard-0&authSource=admin")
db = client['traffic-db']
devices = db['devices']

def is_endpt_domain(device, endpt):
    domains = device['domains']
    for domain in domains:
        if endpt in domain['ips']:
            return True
    return False

def update_device_endpts(mac_address, endpt):
    device = devices.find_one({'mac_address': mac_address})
    is_domain = is_endpt_domain(device, endpt)
    endpts = device['endpts']
    if not endpt in endpts and not is_domain:
        endpts.append(endpt)
        devices.update({'mac_address': mac_address}, {'$set':{'endpts': endpts}})

def update_device_domains(mac_address, domain_dict):
    device = devices.find_one({'mac_address': mac_address})
    domains = device['domains']
    for domain in domains:
        if domain['domain'] == domain_dict['domain'] and domain['ips'] != domain_dict['ips']:
            domain['ips'] = domain_dict['ips']
    devices.update({'mac_address': mac_address}, {'$set':{'domains': domains}})

    if not domain_dict in domains:
        domains.append(domain_dict)
        devices.update({'mac_address': mac_address}, {'$set':{'domains': domains}})

def add_device(device):
    devices.insert_one(device)

def update_device(device):
    #ip address from dhcp
    devices.update({'mac_address': device['mac_address']}, {'$set':{'ip_address': device['ip_address']}})

def check_endpt_valid(mac_address, endpt):
    device = devices.find_one({'mac_address': mac_address})
    endpts = device['endpts']
    if not endpt in endpts:
        return False
    return True

def check_domain_valid(mac_address, domain):
    device = devices.find_one({'mac_address': mac_address})
    domains = device['domains']
    for domain in domains:
        if domain['domain'] == domain:
            return True
    return False

def add_one_way(src, one_way):
    feature_dict = dict()
    feature_dict['src'] = str(src)
    feature_dict['endpoints'] = []
    for endpt in one_way[src]:
        endpt_dict = dict()
        endpt_dict['endpoint'] = endpt
        endpt_dict['stats'] = one_way[src][endpt]
        feature_dict['endpoints'].append(endpt_dict)
    one_way_stats.insert_one(feature_dict)

def update_one_way(src, old_one_way, new_one_way):
    src_one_way = one_way_stats.find_one({'src': src})
    endpoints = src_one_way['endpoints']
    for endpt in new_one_way[src]:
        for old_endpt in endpoints:
            try:
                if old_endpt['endpoint'] == endpt:
                    #need to test if this is right
                    continue
                elif old_endpoint['stats']['domain'] == new_one_way[src][endpt]['domain']:
                    old_endpt['endpoint'] = endpt
                    continue
            except Exception as e:
                pass
            endpt_dict = dict()
            endpt_dict['endpoint'] = endpt
            endpt_dict['stats'] = new_one_way[src][endpt]
            endpoints.append(endpt_dict)
    one_way_stats.update({'src': src}, {'$set': {'endpoints': endpoints}})

def check_endpt_valid(src, endpt):
    src_one_way = one_way_stats.find_one({'src': src})
    endpoints = src_one_way['endpoints']
    valid = False
    for valid_endpt in endpoints:
        if valid_endpt['endpoint'] == endpt:
            valid = True
    return valid

def check_endpts_valid(one_way_stats):
    bad_endpts = []
    for src in one_way_stats:
        for endpt in one_way_stats[src]:
            if not check_endpt_valid(src, endpt):
                bad_endpts.append(endpt)
    return bad_endpts

def add_feature_extraction_to_db(feature_set):

    for feature in feature_set:
        if 'flow' in feature:
            feature_dict = dict()
            feature_dict[feature] = feature_set[feature]
            flow_stats.insert_one(feature_dict)
        elif feature == 'session_stats':
            print('sess')
            for src_dst in feature_set[feature]:
                feature_dict = dict()
                src = src_dst.split(',')[0]
                dst = src_dst.split(',')[1]
                feature_dict['src'] = src
                feature_dict['dst'] = dst
                #maybe?
                #endpt_dict['domain'] = feature_set[feature][src][endpt]['domain']
                feature_dict['stats'] = feature_set[feature][src_dst]
                session_stats.insert_one(feature_dict)
        elif feature == 'one_way_stats':
            print('one')
            for src in feature_set[feature]:
                feature_dict = dict()
                feature_dict['src'] = str(src)
                feature_dict['endpoints'] = []
                for endpt in feature_set[feature][src]:
                    endpt_dict = dict()
                    endpt_dict['endpoint'] = endpt
                    #maybe?
                    #endpt_dict['domain'] = feature_set[feature][src][endpt]['domain']
                    endpt_dict['stats'] = feature_set[feature][src][endpt]
                    feature_dict['endpoints'].append(endpt_dict)
                one_way_stats.insert_one(feature_dict)
        else:
            print('error')

def query_db():
    return flow_stats.find(), session_stats.find(), one_way_stats.find()

def query_all_flow_stats():
    return flow_stats.find()

def query_flow_stats(stat):
    for feat in flow_stats.find():
        if stat in feat:
            return feat[stat]

def query_all_sess_stats(src, dst):
    return session_stats.find_one({'src': src, 'dst': dst})

def query_sess_stats(src, dst, stat):
    return session_stats.find_one({'src': src, 'dst': dst})['stats'][stat]

def query_one_way_stats_src(src):
    return one_way_stats.find_one({'src': src})

def query_one_way_stats_src_dst(src, dst):
    one_way = one_way_stats.find_one({'src': src})
    for endpt in one_way['endpoints']:
        if endpt['endpoint'] == dst:
            return endpt['stats']

def query_one_way_stats_src_dst_stat(src, dst, stat):
    return query_one_way_stats_src_dst(src, dst)[stat]

def query_endpoints(src):
    one_way = one_way_stats.find_one({'src': src})
    endpoints = []
    for endpt in one_way['endpoints']:
        endpoints.append(endpt['endpoint'])
    return endpoints

def query_devices():
    return devices.find()

def get_devices():
    devices = query_devices()
    device_list = []
    for device in devices:
        device_list.append(device)

    return device_list

def get_IoT():
    devices = query_devices()
    device_list = []
    for device in devices:
        if(device_is_Iot(device)):
            device_list.append(device)
    return device_list

def device_exists(device):
    mac_address = device['mac_address']
    if (devices.find_one({'mac_address': mac_address}) == None):
        return False
    else: return True

def device_is_IoT(device):
    mac_address = device['mac_address']
    device = devices.find_one({'mac_address': mac_address})
    if (device['IoT'] == True):
        return True
    else:
        return False

def update_device_ip(device, ip):
    mac_address = device['mac_address']
    devices.update({'mac_address': mac_address}, {'$set':{'ip_address': ip}})

def get_one_way(ip):
    one_way = one_way_stats.find_one({'src': ip})
    return one_way

def get_one_way_by_mac(mac):
    one_way = one_way_stats.find_one({'mac_address': mac})
    return one_way

def update_one_way_ip(device, new_ip):
    mac_address = device['mac_address']
    one_way_stats.update({'mac_address': mac_address}, {'$set':{'src': new_ip}})

def ip_in_device_db(ip):
    if (devices.find_one({'ip_address': ip}) == None):
        return False
    return True

def ip_in_one_way_db(ip):
    if (one_way_stats.find_one({'src': ip}) == None):
        return False
    return True

def get_device(ip):
    return devices.find_one({'ip_address': ip})

def update_one_way_db(one_way):
    for src in one_way:
        if not ip_in_one_way_db(src):
            add_one_way(src, one_way)
        else:
            current = query_one_way_stats(src)
            update_one_way(src, one_way, current)

def check_valid(device, endpt):
    existing_device = devices.find_one({'mac_address': device['mac_address']})
    if device['ip_address'] != existing_device['ip_address']:
        # print("duplicate mac address")
        return False

    if is_endpt_domain(existing_device, endpt):
        return True

    if endpt in existing_device['endpts']:
        return True

    return False

def get_device(mac_address):
    device = devices.find_one({'mac_address': mac_address})
    return device

def get_ip_list():
    devices = query_devices()
    device_list = []

    for device in devices:
        ip = None
        iot = True
        try:
            ip = device['ip_address']
        except Exception as e:
            continue
        try:
            iot = device['IoT']
        except Exception as e:
            pass

        if iot == False:
            continue

        if ip:
            device_list.append(ip)

    return device_list
