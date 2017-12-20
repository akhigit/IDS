from flask import Flask, render_template, redirect, request, g, session, url_for, jsonify, flash, make_response
from flask_cors import CORS, cross_origin
from time import sleep
import config
import subprocess
import thread
import os

from portscanner import *
from parser import *
from celery import Celery, states
from celery_once import QueueOnce
from celery_once import AlreadyQueued
from celery.task.schedules import crontab
from celery.decorators import periodic_task

# example_consumer.pyimport pika
import time

from flask_sse import sse

from net_config import *

app = Flask(__name__)
app.secret_key = "secret"
app.config.from_object(config)

app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')
CORS(app)

### Remove previously generated resource files ###
if os.path.isfile('static/nmap_raw1.xml'):
    os.remove('static/nmap_raw1.xml')
if os.path.isfile('static/nmap_raw2.xml'):
    os.remove('static/nmap_raw2.xml')
if os.path.isfile('static/host_list_file.list'):
    os.remove('static/host_list_file.list')
if os.path.isfile('static/json_dictionary.json'):
    os.remove('static/json_dictionary.json')

#ip = get_IP()
scan_host_result = None

celery = Celery('tasks', backend='amqp', broker='amqp://localhost//')
celery.conf.ONCE = {
'backend': 'celery_once.backends.Redis',
'settings': {
'url': 'redis://localhost:6379/0',
'default_timeout': 60 * 60
}
}

@celery.task(base=QueueOnce, once={'keys': []}, name='celery_application.scanner')
def scan_and_parse(status_check, hosts=[], mode='w', netmask='29'):
    return_msg = "Status check finished"
    if not status_check:
        if len(hosts) == 0:
            hosts = list_hosts(ip, netmask.encode('ascii','ignore'))
        print "Found hosts: ",hosts
        if mode == 'w':
            scan_hosts('static/nmap_raw1.xml', hosts)
            parse('static/nmap_raw1.xml', mode)
        elif mode == 'a':
            print "In append mode"
            scan_hosts('static/nmap_raw2.xml', hosts)
            parse('static/nmap_raw2.xml', mode)
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
        scan_and_parse_task = scan_and_parse.apply_async(args=args)
    except AlreadyQueued:
        return make_response(jsonify({'task_id': json.dumps(None)}))
    return make_response(jsonify({'task_id': scan_and_parse_task.task_id}))

@app.route("/scan_host/<host_ip>", methods=['GET'])
def scan_host(host_ip):
    try:
        host_in_list = []
        host_in_list.append(host_ip)
        args = [False, host_in_list, 'a']
        scan_and_parse_task = scan_and_parse.apply_async(args=args)
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
