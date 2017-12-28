import os
import redis_lock
from redlock import RedLock

### Defining the resource files ###
nmap_xml1 = 'static/nmap_raw1.xml'
nmap_xml2 = 'static/nmap_raw2.xml'
hosts_list_file = 'static/hosts_list_file.list'
hosts_json_file = 'static/json_dictionary.json'

#### Define locks ####
lock_xml = RedLock("xml_lock")
lock_host_json_files = RedLock("host_json_files_lock")

### To hold the result of deep-scan ###
scan_host_result = None

### Remove previously generated resource files ###
def remove_resource_files():
    if os.path.isfile(nmap_xml1):
        os.remove(nmap_xml1)
    if os.path.isfile(nmap_xml2):
        os.remove(nmap_xml2)
    if os.path.isfile(hosts_list_file):
        os.remove(hosts_list_file)
    if os.path.isfile(hosts_json_file):
        os.remove(hosts_json_file)
