from flask import Flask, render_template, redirect, request, g, session, \
                  url_for, jsonify, flash, make_response
from flask_cors import CORS, cross_origin
from threading import Thread
from time import sleep
import thread, os, time, json, cPickle as pickle

from flask_socketio import SocketIO, emit
from flask_sse import sse
from celery import Celery, states
from celery_once import QueueOnce, AlreadyQueued
from kombu import Queue
import config, pyping

from portscanner import *
from parser import parse, update_json_file
from helper import remove_resource_files, lock_host_json_files
from mongo_ops import *
from ONOS_API import *


#### Configure celery-related parameters ####
celery = Celery('tasks', backend='amqp', broker='amqp://localhost//')
celery.conf.task_default_queue = 'default'
celery.conf.task_queues = (
    Queue('default', routing_key='default'),
    Queue('manual_scanner_queue', routing_key='mscan'),
)
CELERY_ROUTES = {
    'manual_scan_and_parse': {
        'queue': 'manual_scanner_queue',
        'routing_key': 'mscan',
    },
    'scan_and_parse': {
        'queue': 'default',
        'routing_key': 'default',
    }
}
celery.conf.ONCE = {
  'backend': 'celery_once.backends.Redis',
  'settings': {
    'url': 'redis://localhost:6379/0',
    'default_timeout': 60 * 60
  }
}


#### Variables for the thread that checks the connectivity of hosts ####
thread = None
async_mode = None


#### Configure flask app parameters ####
app = Flask(__name__)
app.secret_key = "secret"
app.config.from_object(config)
CORS(app)


#### Configure redis for SSE ####
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')
socketio = SocketIO(app, async_mode=async_mode)


#### ONOS Controller parameters ####
controller_ip = "160.39.10.114"
controller_id = "of%3A0000687f7429badf"


#### Remove previously generated resource files ####
remove_resource_files()


def device_already_present(host_ip):
    """
    Checks if a device has already been scanned

    Args:
        host_ip (str): ip address of the device

    Returns:
        1 if the device has already been scanned. O otherwise.

    Raises:
        Nothing
    """
    lock_host_json_files.acquire()
    if not os.path.isfile('static/json_dictionary.json'):
        lock_host_json_files.release()
        return 0
    data = json.load(open('static/json_dictionary.json'))
    for node in data['nodes']:
        if node['IP'] == host_ip:
            lock_host_json_files.release()
            return 1
    lock_host_json_files.release()
    return 0


def set_device_compromised(host_ip):
    """
    Updates the json file to indicate the a device is potentially malicious

    Args:
        host_ip (str): ip address of the device

    Returns:
        1 if the device had not been marked as compromised. O otherwise or
        if the json file doesn't exist.

    Raises:
        Nothing
    """
    lock_host_json_files.acquire()
    if not os.path.isfile('static/json_dictionary.json'):
        lock_host_json_files.release()
        return 0
    data = json.load(open('static/json_dictionary.json'))
    for node in data['nodes']:
        if node['IP'] == host_ip and node['group'] != 4:
            node['group'] = 4
            with open(hosts_json_file,'w') as outfile:
                json.dump(data, outfile)
            lock_host_json_files.release()
            return 1
    lock_host_json_files.release()
    return 0


def find_disconnected_devices():
    """
    Checks connectivity for each scanned device and creates a list of devices
    that haven't are no longer reacheable.

    Args:
        Nothing

    Returns:
        A list of hosts are no longer connected to the network.

    Raises:
        Nothing
    """
    lock_host_json_files.acquire()
    hosts_disconnected = []
    if os.path.isfile('static/hosts_list_file.list'):
        hosts_list_file_handle = open('static/hosts_list_file.list', 'rb')
        hosts_list = pickle.load(hosts_list_file_handle)
        hosts_list_file_handle.close()
        new_hosts_list = []
        for host in hosts_list:
            ping_result = pyping.ping(host.address)
            if ping_result.ret_code:
                hosts_disconnected.append(host.address)
            else:
                new_hosts_list.append(host)
        if len(hosts_disconnected):
            hosts_list_file_handle = open('static/hosts_list_file.list', 'w')
            if len(new_hosts_list):
                pickle.dump(new_hosts_list, hosts_list_file_handle)
                update_json_file(new_hosts_list)
            else:
                os.remove('static/hosts_list_file.list')
                os.remove('static/json_dictionary.json')
            hosts_list_file_handle.close()
    lock_host_json_files.release()
    return hosts_disconnected


def background_stuff():
    """
    The function that the thread running in the background executes.
    Upon detection of a disconnected device, the network map is updated.

    Args:
        Nothing

    Returns:
        Nothing

    Raises:
        Nothing
    """
    while True:
        time.sleep(2)
        hosts_disconnected = find_disconnected_devices()
        if len(hosts_disconnected):
            print "A ping was unsuccessful"
            print hosts_disconnected
            socketio.emit('disconnection', {'disconnected_hosts':
                           hosts_disconnected}, namespace='/test')


@socketio.on('connect', namespace='/test')
def test_connect():
    """
    The flask_socketio function that spawns the aforemetioned background thread.

    Args:
        Nothing

    Returns:
        Nothing

    Raises:
        Nothing
    """
    global thread
    print('Socket started')
    if thread is None:
        thread = Thread(target=background_stuff)
        thread.start()


@celery.task(base=QueueOnce, once={'keys': []})
def manual_scan_and_parse(netmask='29'):
    """
    Runs a fast scan to find devices present in the network.
    Deep scans these devices to gather all the relevant information such as IP
    address, MAC address, Open ports and services running on them. To generate
    the network map, the hop distance (found from the deep scan) from the
    scanner is used. This function is invoked when the scanner is manually
    started by the user.

    Args:
        netmask (str): For specifying the subnet. Default value is 29.

    Returns:
        A status message indicating completion of the Deep Scan.

    Raises:
        Nothing
    """
    hosts = list_hosts(netmask.encode('ascii','ignore'))
    print "Found hosts: ",hosts
    scan_hosts('static/nmap_raw1.xml', hosts, scan_and_parse.request.id)
    parse('w')
    return_msg = "Deep Scanning Finished"
    return return_msg

@celery.task
def scan_and_parse(hosts=[]):
    """
    Deep scans a devices to gather all the relevant information such as IP
    address, MAC address, Open ports and services running on them. To generate
    the network map, the hop distance (found from the deep scan) from the
    scanner is used. This function is invoked when the scanner is triggered
    automatically upon host discovery.

    Args:
        host (list): Since the nmap library function for deep-scanning takes a
        list of devices as an argument, the host ip is passed as a
        single-element list.

    Returns:
        A status message indicating completion of the Deep Scan.

    Raises:
        Nothing
    """
    print "Found hosts: ",hosts
    print "In append mode"
    scan_hosts('static/nmap_raw2.xml', hosts, scan_and_parse.request.id)
    parse('a')
    return_msg = "Deep Scanning Finished"
    return return_msg


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.route("/acquire_lock", methods=['GET'])
def acquire_lock():
    """
    Used by the front-end to acquire the lock for the shared json file.
    """
    lock_host_json_files.acquire()
    response = {}
    response['locked'] = 1
    return make_response(jsonify(response))


@app.route("/release_lock", methods=['GET'])
def release_lock():
    """
    Used by the front-end to release the lock for the shared json file.
    """
    lock_host_json_files.release()
    response = {}
    response['unlocked'] = 1
    return make_response(jsonify(response))


@app.route("/scan_post", methods=['POST'])
def scan_post():
    """
    Invoked when the user manually starts the portscanner.

    Args:
        Nothing

    Returns:
        Task id of the celery worker engaged in this task. None if the scanner
        is already running.

    Raises:
        AlreadyQueued exception
    """
    try:
        netmask = request.form['netmask']
        args = [netmask]
        manual_scan_and_parse_task = manual_scan_and_parse.apply_async(args=args,
                              queue='manual_scanner_queue', routing_key='mscan')

    # To prevent resource-wastage, only one user-initiated port-scanning
    # task is allowed
    except AlreadyQueued:
        print "AlreadyQueued exception hit"
        return make_response(jsonify({'task_id': json.dumps(None)}))
    return make_response(jsonify({'task_id': manual_scan_and_parse_task.task_id}))


@app.route("/scan_host/<host_ip>", methods=['GET'])
def scan_host(host_ip):
    """
    Automatically invoked upon host-discovery.

    Args:
        host_ip (str): IP address of the discovered host.

    Returns:
        Task id of the celery worker engaged in this task.

    Raises:
        Nothing
    """
    host_in_list = []
    host_in_list.append(host_ip)
    args = [host_in_list]

    if device_already_present(host_ip):
        return make_response(jsonify({'task_id': -1}))
    print "About to check static profile"
    static_profile(controller_ip, controller_id, host_ip)
    print "Done checking static profile"
    scan_and_parse_task = scan_and_parse.apply_async(args=args,
                          queue='default', routing_key='default')
    return make_response(jsonify({'task_id': scan_and_parse_task.task_id}))


@app.route('/task/<task_id>', methods=['GET'])
def check_task_status(task_id):
    """
    Checks if the celery worker is busy.

    Args:
        task_id (str): Task id of the celery worker whose status
        is to be queried.

    Returns:
        A status message indicating the state of the task (PENDING,
        SUCCESS or FAILURE).

    Raises:
        Nothing
    """
    response = {}
    if (task_id != -1):
        task = scan_and_parse.AsyncResult(task_id)
        state = task.state
        response['state'] = state

        if state == states.SUCCESS:
            response['result'] = task.get()
        elif state == states.FAILURE:
            try:
                response['error'] = task.info.get('error')
            except Exception as e:
                response['error'] = 'Unknown error occurred'
    else:
        response['state'] = "SUCCESS"
    return make_response(jsonify(response))


@app.route("/")
def index():
    """
    The home page of the Web-application.
    """
    print "Inside index page"
    return render_template("index.html", async_mode=socketio.async_mode)


@app.route('/process_anomaly/<endpoints>', methods=['GET'])
def process_anomaly(endpoints):
    """
    Invoked for the purpose of applying ACLs on the controller that block
    communication between the passed endpoints.

    Args:
        endpoints (list): The ip addresses of the devices (passed as a list)
        participating in the communication.

    Returns:
        A response message indicating whether the first host of the pair has
        just been compromised (1) or had already been compromised (0). For the
        second case, we avoid redundancy by not attempting to apply an ACL that
        has already been applied.

    Raises:
        Nothing
    """
    host_ips = str(endpoints).split()
    is_device_present = device_already_present(host_ips[0])
    is_device_compromised = set_device_compromised(host_ips[0])
    if is_device_present and not is_device_compromised:
        ACL_Blacklist(controller_ip, controller_id,
                  host_ips[0], host_ips[1])
    response = {}
    response['is_refresh_req'] = is_device_compromised
    return make_response(jsonify(response))


@app.route('/block_device/<deviceip>', methods=['GET'])
def block_device(deviceip):
    """
    Invoked for the purpose of applying ACLs on the controller that block all
    traffic to and from the device.

    Args:
        deviceip (str): The ip addresses of the device.

    Returns:
        A response message indicating whether the host has just been
        compromised (1) or had already been compromised (0). For the
        second case, we avoid redundancy by not attempting to apply an ACL that
        has already been applied.

    Raises:
        Nothing
    """
    is_device_present = device_already_present(deviceip)
    is_device_compromised = set_device_compromised(deviceip)
    if is_device_present and not is_device_compromised:
        QUARANTINE(controller_ip, controller_id, deviceip)
    response = {}
    response['is_refresh_req'] = is_device_compromised
    return make_response(jsonify(response))
