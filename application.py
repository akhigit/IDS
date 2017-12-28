from flask import Flask, render_template, redirect, request, g, session, url_for, jsonify, flash, make_response
from flask_cors import CORS, cross_origin
from time import sleep
import config
import subprocess
import thread
import os
import time
import json

from portscanner import *
from parser import *

from flask_sse import sse

from net_config import *
from setup import *

from celery import Celery, states
from celery_once import QueueOnce
from celery_once import AlreadyQueued
from celery.decorators import periodic_task

from kombu import Exchange, Queue

from mongo_ops import *
from ONOS_API import *

### Remove previously generated resource files ###
remove_resource_files()

### Configure celery-related parameters ###
celery = Celery('tasks', backend='amqp', broker='amqp://localhost//')

CELERY_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default', queue_arguments={'x-max-priority': 100}),
)
CELERY_ACKS_LATE = True
CELERYD_PREFETCH_MULTIPLIER = 1

"""
celery.conf.ONCE = {
'backend': 'celery_once.backends.Redis',
'settings': {
'url': 'redis://localhost:6379/0',
'default_timeout': 60 * 60
}
}
"""

### Configure flask app parameters ###
app = Flask(__name__)
app.secret_key = "secret"
app.config.from_object(config)
CORS(app)

### Configure redis for SSE ###
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

#@celery.task(base=QueueOnce, once={'keys': []}, name='celery_application.scanner')
@celery.task(name='celery_application.scanner')
def scan_and_parse(status_check, hosts=[], mode='w', netmask='29'):
    return_msg = "Status check finished"
    print "****************************"
    print scan_and_parse.request.id
    print "****************************"
    if not status_check:
        if len(hosts) == 0:
            hosts = list_hosts(ip, netmask.encode('ascii','ignore'))
        print "Found hosts: ",hosts
        if mode == 'w':
            scan_hosts(nmap_xml1, hosts, scan_and_parse.request.id)
            parse(nmap_xml1, mode)
        elif mode == 'a':
            print "In append mode"
            scan_hosts(nmap_xml2, hosts, scan_and_parse.request.id)
            parse(nmap_xml2, mode)
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

@app.route("/")
def index():
    print "Inside index page"
    flash_message = request.args.get('messages')
    if flash_message:
        print flash_message
        flash(flash_message)
    message = 'Portscanner not running'
    try:
        scan_and_parse.delay(True)
    except AlreadyQueued:
        print 'Portscanner running!'
        message = 'Portscanner running'
    return render_template("index.html", message=message)

@app.route("/scan_post", methods=['POST'])
def scan_post():
    try:
        netmask = request.form['netmask']
        args = [False, [], 'w', netmask]
        scan_and_parse_task = scan_and_parse.apply_async(args=args, priority=2)
    except AlreadyQueued:
        return make_response(jsonify({'task_id': json.dumps(None)}))
    return make_response(jsonify({'task_id': scan_and_parse_task.task_id}))

def device_already_present(host_ip):
    print "device_already_present to acquire host_json_files lock"
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

@app.route("/scan_host/<host_ip>", methods=['GET'])
def scan_host(host_ip):
    try:
        host_in_list = []
        host_in_list.append(host_ip)
        args = [False, host_in_list, 'a']
        if device_already_present(host_ip):
            return
        static_profile("160.39.253.141","of%3A0000687f7429badf",host_ip)
        scan_and_parse_task = scan_and_parse.apply_async(args=args, priority=1)
    except AlreadyQueued:
        return make_response(jsonify({'task_id': json.dumps(None)}))
    return make_response(jsonify({'task_id': scan_and_parse_task.task_id}))

@app.route('/task/<task_id>', methods=['GET'])
def check_task_status(task_id):
    task = scan_and_parse.AsyncResult(task_id)
    state = task.state
    response = {}
    response['state'] = state

    if state == states.SUCCESS:
        response['result'] = task.get()
    elif state == states.FAILURE:
        try:
            response['error'] = task.info.get('error')
        except Exception as e:
            response['error'] = 'Unknown error occurred'
    return make_response(jsonify(response))

def set_device_compromised(host_ip):
    print "set_device to acquire host_json_files lock"
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

@app.route('/process_anomaly/<endpoints>', methods=['GET'])
def process_anomaly(endpoints):
    host_ips = str(endpoints).split()
    print host_ips
    ACL_Blacklist("160.39.253.141", "of%3A0000687f7429badf",
                  host_ips[0], host_ips[1])
    response = {}
    response['is_refresh_req'] = set_device_compromised(host_ips[0])
    return make_response(jsonify(response))

@app.route('/block_device/<deviceip>', methods=['GET'])
def block_device(deviceip):
    device_ip = str(deviceip)
    print device_ip
    #QUARANTINE("160.39.253.141", "of%3A0000687f7429badf", device_ip)
    response = {}
    response['is_refresh_req'] = set_device_compromised(device_ip)
    return make_response(jsonify(response))
