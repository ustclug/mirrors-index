# Dependencies

* Python3
* nodejs
* incron

# Install

Run webhook.js with nodejs on system boot to listen web hook.

Add a following line to incrontab:

```/srv/www IN_CREATE,IN_DELETE,IN_MOVE /home/mirror/newindex/genindex.py```
