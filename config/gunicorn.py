# This file is used for gunicorn app -c config/gunicorn.py
def pre_request(worker, req):
    if req.path == '/active_proc_count':
        return
    worker.log.debug("%s %s" % (req.method, req.path))