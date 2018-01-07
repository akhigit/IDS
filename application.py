from flask import Flask, render_template, redirect, request, g, session, \
                  url_for, jsonify, flash, make_response
from flask_cors import CORS, cross_origin
from threading import Thread
from time import sleep
import subprocess
import thread
import os
import time
import json

from flask_socketio import SocketIO, emit
from flask_sse import sse
from celery import Celery, states
from celery_once import QueueOnce, AlreadyQueued
from kombu import Queue
import config
import pyping

from portscanner import *
from parser import *
from helper import *
from mongo_ops import *
from ONOS_API import *

### Remove previously generated resource files ###
remove_resource_files()

### Configure celery-related parameters ###
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

thread = None
async_mode = None

### Configure flask app parameters ###
app = Flask(__name__)
app.secret_key = "secret"
app.config.from_object(config)
CORS(app)

### Configure redis for SSE ###
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')
socketio = SocketIO(app, async_mode=async_mode)

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

@celery.task(base=QueueOnce, once={'keys': []})
def manual_scan_and_parse(hosts=[], netmask='29'):
    hosts = list_hosts(ip, netmask.encode('ascii','ignore'))
    print "Found hosts: ",hosts
    scan_hosts(nmap_xml1, hosts, scan_and_parse.request.id)
    parse(nmap_xml1, 'w')
    return_msg = "Deep Scanning Finished"
    return return_msg

@celery.task
def scan_and_parse(hosts=[]):
    print "Found hosts: ",hosts
    print "In append mode"
    scan_hosts(nmap_xml2, hosts, scan_and_parse.request.id)
    parse(nmap_xml2, 'a')
    return_msg = "Deep Scanning Finished"
    return return_msg

def device_already_present(host_ip):
    lock_host_json_files.acquire()
    if not os.path.isfile(hosts_json_file):
        lock_host_json_files.release()
        return 0
    data = json.load(open(hosts_json_file))
    for node in data['nodes']:
        if node['IP'] == host_ip:
            lock_host_json_files.release()
            return 1
    lock_host_json_files.release()
    return 0

def set_device_compromised(host_ip):
    lock_host_json_files.acquire()
    if not os.path.isfile(hosts_json_file):
        lock_host_json_files.release()
        return 0
    data = json.load(open(hosts_json_file))
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
    lock_host_json_files.acquire()
    hosts_disconnected = []
    if os.path.isfile(hosts_list_file):
        host_list_file_handle = open(hosts_list_file, 'rb')
        host_list = pickle.load(host_list_file_handle)
        host_list_file_handle.close()
        new_host_list = []
        for host in host_list:
            ping_result = pyping.ping(host.address)
            if ping_result.ret_code:
                hosts_disconnected.append(host.address)
            else:
                new_host_list.append(host)
        if len(hosts_disconnected):
            host_list_file_handle = open(hosts_list_file, 'w')
            if len(new_host_list):
                pickle.dump(new_host_list, host_list_file_handle)
                pairings = get_common_hop_dist(str(ip), new_host_list)
                pairs = get_all_possible_nw_pairings(pairings)
                links = get_sources_and_targets(pairs)
                json_blob_dictionary = {}
                json_blob_dictionary = {"nodes" : make_dictionaries(new_host_list), "links" : links}
                json_file_handle = open(hosts_json_file, 'w')
                json.dump(json_blob_dictionary, json_file_handle)
                json_file_handle.close()
            else:
                os.remove(hosts_list_file)
                os.remove(hosts_json_file)
            host_list_file_handle.close()
    lock_host_json_files.release()
    return hosts_disconnected

def background_stuff():
    while True:
        time.sleep(2)
        hosts_disconnected = find_disconnected_devices()
        if len(hosts_disconnected):
            print "A ping was unsuccessful"
            print hosts_disconnected
            socketio.emit('disconnection', {'disconnected_hosts': hosts_disconnected}, namespace='/test')

@app.route("/")
def index():
    print "Inside index page"
    return render_template("index.html", async_mode=socketio.async_mode)

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    print('Socket started')
    if thread is None:
        thread = Thread(target=background_stuff)
        thread.start()

@app.route("/scan_post", methods=['POST'])
def scan_post():
    try:
        netmask = request.form['netmask']
        args = [[], netmask]
        manual_scan_and_parse_task = manual_scan_and_parse.apply_async(args=args,
                              queue='manual_scanner_queue', routing_key='mscan')
    except AlreadyQueued:
        print "AlreadyQueued exception hit"
        return make_response(jsonify({'task_id': json.dumps(None)}))
    return make_response(jsonify({'task_id': manual_scan_and_parse_task.task_id}))

@app.route("/scan_host/<host_ip>", methods=['GET'])
def scan_host(host_ip):
    host_in_list = []
    host_in_list.append(host_ip)
    args = [host_in_list]
    #static_profile("160.39.10.114","of%3A0000687f7429badf",host_ip)
    if device_already_present(host_ip):
        return make_response(jsonify({'task_id': 1}))
    scan_and_parse_task = scan_and_parse.apply_async(args=args,
                          queue='default', routing_key='default')
    return make_response(jsonify({'task_id': scan_and_parse_task.task_id}))

@app.route('/task/<task_id>', methods=['GET'])
def check_task_status(task_id):
    response = {}
    if (task_id != 1):
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

@app.route('/process_anomaly/<endpoints>', methods=['GET'])
def process_anomaly(endpoints):
    host_ips = str(endpoints).split()
    is_device_present = device_already_present(host_ips[0])
    is_device_compromised = set_device_compromised(host_ips[0])
    if is_device_present and not is_device_compromised:
        ACL_Blacklist("160.39.10.114", "of%3A0000687f7429badf",
                  host_ips[0], host_ips[1])
    response = {}
    response['is_refresh_req'] = is_device_compromised
    return make_response(jsonify(response))

@app.route('/block_device/<deviceip>', methods=['GET'])
def block_device(deviceip):
    is_device_present = device_already_present(deviceip)
    is_device_compromised = set_device_compromised(deviceip)
    if is_device_present and not is_device_compromised:
        QUARANTINE("160.39.10.114", "of%3A0000687f7429badf", deviceip)
    response = {}
    response['is_refresh_req'] = is_device_compromised
    return make_response(jsonify(response))
