from flask import Flask, render_template
from flask_sse import sse
app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

from celery import Celery

celery = Celery('tasks', backend='amqp', broker='amqp://localhost//')
celery.conf.update(
CELERY_ROUTES = {
'device_ip': {'queue': 'red'},
},
)

message = None

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/hello')
def publish_hello():
    print "Calling celery task"
    message = str(device_ip.apply_async(queue='red').get())
    sse.publish({"message": message}, type='greeting')
    return "Message sent: "+message

@celery.task
def device_ip():
    return "169.30.11.23"
