from flask import Flask, render_template, redirect, request, g, session, url_for, flash
from celery import Celery
from celery_once import QueueOnce
from celery_once import AlreadyQueued
from time import sleep
import config
from portscanner import *
import subprocess
import thread
import os
import psutil

app = Flask(__name__)
app.config.from_object(config)

celery = Celery('tasks', broker='amqp://localhost//')
celery.conf.ONCE = {
'backend': 'celery_once.backends.Redis',
'settings': {
'url': 'redis://localhost:6379/0',
'default_timeout': 60 * 60
}
}

@app.route("/")
def index():
    message = 'Portscanner not running'
    try:
        scanner.delay(True)
    except AlreadyQueued:
        message = 'Portscanner running.'
    return render_template("index.html", message=message)

@celery.task(base=QueueOnce, once={'keys': []}, name='celery_exampele.application2')
def scanner(status_check):
    if not status_check:
        start_scan()

@app.route("/scan")
def scan():
    try:
        scanner.delay(False)
    except AlreadyQueued:
        pass
    return redirect("/", code=302)

if __name__ == "__main__":
    app.run(debug=True, port=5008)
