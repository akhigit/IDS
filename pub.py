# example_publisher.py
import pika, os, logging
logging.basicConfig()

# Parse CLODUAMQP_URL (fallback to localhost)
url = 'amqp://unmntdbc:cOLaTd5JrnOdbxMSnVUwABRAZRZhXSlZ@fish.rmq.cloudamqp.com/unmntdbc'
params = pika.URLParameters(url)
#url = 'localhost'
#params = pika.ConnectionParameters(host = url)
params.socket_timeout = 5

connection = pika.BlockingConnection(params) # Connect to CloudAMQP
channel = connection.channel() # start a channel
channel.queue_declare(queue='deviceip') # Declare a queue

anomaly_msg = "Anomaly;192.168.86.65;8.8.8.8"
compromised_msg = "Compromised;192.168.86.65"
discovery_msg = "Discovered;192.168.86.65"

# send a message
channel.basic_publish(exchange='', routing_key='deviceip', body=compromised_msg)
print ("169.39.10.101")
connection.close()
