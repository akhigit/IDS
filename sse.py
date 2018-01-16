from flask import Flask, render_template
from flask_sse import sse
import pika

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

@app.route('/')
def index():
    return render_template("index_sse.html")

@app.route('/consume')
def publish_hello():
    start_consuming()

def sse_publisher(msg):
  print("Received %r" % msg)
  sse.publish({"message": msg}, type='greeting')
  print("Message Sent!");
  return;

def start_consuming():
    print "Inside start_consuming()"
    # Access the CLODUAMQP_URL environment variable and parse it
    url = 'amqp://unmntdbc:cOLaTd5JrnOdbxMSnVUwABRAZRZhXSlZ@fish.rmq.cloudamqp.com/unmntdbc'
    params = pika.URLParameters(url)
    #url = 'localhost'
    #params = pika.ConnectionParameters(host = url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel() # start a channel
    channel.queue_declare(queue='deviceip') # Declare a queue

    # create a function which is called on incoming messages
    def callback(ch, method, properties, body):
      sse_publisher(body)

    # set up subscription on the queue
    channel.basic_consume(callback,
      queue='deviceip',
      no_ack=True)

    # start consuming (blocks)
    channel.start_consuming()
    connection.close()
