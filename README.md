# IDS

# Overview

# Dependencies
The project uses the following packages:

- libnmap https://pypi.python.org/pypi/python-libnmap
- BeautifulSoup https://pypi.python.org/pypi/beautifulsoup4
- celery https://pypi.python.org/pypi/celery
- celery_once https://pypi.python.org/pypi/celery_once
- rabbitmq (sudo apt-get install rabbitmq-server)
- redis https://www.rosehosting.com/blog/how-to-install-configure-and-use-redis-on-ubuntu-16-04/


# Subdirectories

-templates
    - HTML containing logic for the front-end
-static
    - css and js libraries
    - An xml file that stores the result of nmap deep scan
    - A json file that is used to generate the topology
    
# Usage
- In separate tabs/windows, run the following comamnds with root privileges
  - python application.py
  - celery -A application.celery worker --loglevel=info
  - redis-server
