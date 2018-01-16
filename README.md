# Intrusion Detection System

# Overview

# Dependencies
The project uses the following packages:

- libnmap https://pypi.python.org/pypi/python-libnmap (sudo -H pip install python-libnmap)
- celery https://pypi.python.org/pypi/celery (sudo -H pip install -U celery)
- celery_once https://pypi.python.org/pypi/celery_once (sudo -H pip install -U celery_once)
- rabbitmq (Install: sudo apt-get install rabbitmq-server, Start: invoke-rc.d rabbitmq-server start)
- redis https://www.rosehosting.com/blog/how-to-install-configure-and-use-redis-on-ubuntu-16-04/
- gevent, gunicorn and flask-sse https://media.readthedocs.org/pdf/flask-sse/latest/flask-sse.pdf
  (sudo -H pip install flask-sse gunicorn gevent)
- redlock https://pypi.python.org/pypi/redlock/1.2.0 (sudo -H pip install redlock)
- flask_cors http://flask-cors.readthedocs.io/en/latest/ (sudo -H pip install flask_cors)
- netifaces https://pypi.python.org/pypi/netifaces (sudo -H pip install netifaces)
- pyping https://pypi.python.org/pypi/pyping/ (sudo -H pip install pyping)
- flask-socketio https://flask-socketio.readthedocs.io/en/latest/ (sudo -H pip install flask-socketio)
- kombu https://pypi.python.org/pypi/kombu (sudo -H pip install kombu)


# Subdirectories
The project contains the following subdirectories:

- templates
    - index.html
    - index_sse.html
- static
    - css
      - css libraries
     - js 
      - js libraries
      - topo_renderer.js
      - helper.js
 - application.py
 - sse.py
 - portscanner.py
 - parser.py
 - helper.py
 - ONOS_API.py
 - mongo_ops.py
 - flowtable.py
 - quarantine_flow.py
 - static_flow.py
    
# Usage
- In separate tabs/windows, run the following comamnds with root privileges
  - sudo gunicorn application:app --worker-class gevent --bind 0.0.0.0:5009
  - sudo celery -A application.celery worker --autoscale=10,0 --loglevel=info --beat -n scanner2 -Q manual_scanner_queue
  - sudo celery -A application.celery worker --autoscale=10,0 --loglevel=info --beat -n scanner3 -Q default
  - sudo gunicorn sse:app --worker-class gevent --bind 127.0.0.1:800
