# IDS

# Overview

# Dependencies
The project uses the following packages:

- libnmap https://pypi.python.org/pypi/python-libnmap
- BeautifulSoup https://pypi.python.org/pypi/beautifulsoup4
- celery https://pypi.python.org/pypi/celery
- celery_once https://pypi.python.org/pypi/celery_once
- rabbitmq (Install: sudo apt-get install rabbitmq-server, Start: invoke-rc.d rabbitmq-server start)
- redis https://www.rosehosting.com/blog/how-to-install-configure-and-use-redis-on-ubuntu-16-04/
- gevent, gunicorn and flask-sse (sudo -H pip install flask-sse gunicorn gevent)
- redis_lock (sudo -H pip install python-redis-lock)
- flask_cors (sudo -H pip install flask_cors)
- netifaces (sudo -H pip install netifaces)


# Subdirectories
The project contains the following subdirectories:

- templates
    - HTML containing logic for the front end
- static
    - css and js libraries
    - An xml file that stores the result of nmap deep scan
    - A json file that is used to generate the topology
    
# Usage
- In separate tabs/windows, run the following comamnds with root privileges
  - sudo gunicorn application:app --worker-class gevent --bind 0.0.0.0:5009
  - sudo celery -A application.celery worker --autoscale=10,0 --loglevel=info --beat -n scanner
  - sudo gunicorn sse:app --worker-class gevent --bind 127.0.0.1:8000
  - Check if redis-server is running: redis-cli ping should return PONG
