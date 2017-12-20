from flask import Flask, render_template
from flask_sse import sse
import pika

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
    start_consuming()
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

def pdf_process_function(msg):
  print(" PDF processing")
  print(" Received %r" % msg)

  #time.sleep(5) # delays for 5 seconds
  sse.publish({"message": msg}, type='greeting')
  print(" PDF processing finished");
  return;

def start_consuming():
    print "Inside start_consuming()"
    # Access the CLODUAMQP_URL environment variable and parse it (fallback to localhost)
    url = 'amqp://unmntdbc:cOLaTd5JrnOdbxMSnVUwABRAZRZhXSlZ@fish.rmq.cloudamqp.com/unmntdbc'
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel() # start a channel
    channel.queue_declare(queue='deviceip') # Declare a queue

    # create a function which is called on incoming messages
    def callback(ch, method, properties, body):
      pdf_process_function(body)

    # set up subscription on the queue
    channel.basic_consume(callback,
      queue='deviceip',
      no_ack=True)

    # start consuming (blocks)
    channel.start_consuming()
    connection.close()
