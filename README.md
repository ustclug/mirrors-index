# Dependencies

* python3
* python3-requests 2.7.0
* python3-jinja2 2.7.3
* nodejs
* incron

# Install

Run webhook.js with nodejs on system boot to listen web hook.

Add a following line to incrontab:

```/srv/www IN_CREATE,IN_DELETE,IN_MOVE /home/mirror/newindex/genindex.py```
