#!/usr/bin/python
#

import sys
from flask import Flask
from flask import request

debug = False

# TODO: need better way than using this global...
# TODO: This all probably should not be an object...
CONFIG = False

app = Flask(__name__)

class Rest(object):

    global CONFIG
    app = Flask(__name__)
    
    def __init__(self,config,logger):
        self.app     = app
        self.config  = config
        global CONFIG
        CONFIG = config
        self.logger  = logger
        self.host    = self.config['this_host']['host']
        self.port    = int(self.config['this_host']['port'])
        info = "Configuring REST interface...";
        logger.info(info)
        print info
        self.app.debug = debug

    def run(self):
        info = "Starting REST interface %s:%s..." % (self.host,self.port)
        self.app.run(host=self.host, port=self.port)

    def get_ip(self):
        return request.remote_addr

@app.route("/")
def top():
    app.logger.info("REST:top")
    return "ISYHelper HABridge: %s<br>" % (CONFIG['version'])
    #return "ISYHelper Web Interface version %s<br>Requestor: %s<br>%s" % (CONFIG['isyhelper_version'], request.remote_addr, isyhelperRESTObj.helpers.get_index())

#
# This translates a REST setvar command to pass to the appropriate Helper
# that accepts responses from specific IP addresses, like Foscam.
#
#@app.route('/setvar/<path:path>')
#def setvar(path):
#    # Get the helper for the incoming IP address
#    rip = request.remote_addr;
#    helper = isyhelperRESTObj.helpers.get_helper(rip)
#    if helper is False:
#        return "REST:setvar: No helper for IP %s" % (rip), 404
#    if not path:
#        return "path not defined from %s" % (rip), 404
#    # TODO: Allow value param to be passed in?
#    # TODO: Make sure split only returns 2 objects?
#    #udata = web.input(value=None)
#    li = path.split("/")
#    varname = li[0]
#    varvalue = li[1]
#    info = 'REST:setvar:GET: ' + rip + ' varname='+ varname + ' value=' + str(varvalue)
#    isyhelperRESTObj.helpers.logger.info(info)
#    helper.setvar(varname,varvalue)
#    return info

#@app.route('/<helper_name>/<path:path>')
#def helper(helper_name,path):
#    app.logger.debug("REST:helper: helper_name=%s path=%s" % (helper_name,path))
#    helper = isyhelperRESTObj.helpers.get_helper_by_name(helper_name)
#    if not helper:
#        msg = "REST:default:GET: No helper '%s' exists for '%s' request by %s" % (helper_name, path, request.remote_addr)
#        app.logger.error(msg)
#        return msg, 404
#    # Call the Helpers rest_get method.
#    if request.method == 'GET':
#        app.logger.debug("REST:helper: Calling %s.rest_get(%s)" % (helper_name,path))
#        return helper.rest_get(app,request,path)
#    app.logger.error("REST:helper:%s: No %s method available" % (helper_name,request.method))
#    return msg, 404

if __name__ == "__main__":
    import logging
    import os
    config = { 'this_host' : { 'host' : '192.168.1.77', 'port' : '8082' } }
    log_file = "REST.log"
    log_format = '%(asctime)-15s:%(name)s:%(levelname)s: %(message)s'
    if os.path.exists(log_file):
        os.remove(log_file)
    logging.basicConfig(filename=log_file, format=log_format);
    logger = logging.getLogger('IH')
    logger.setLevel(logging.DEBUG)
    rest = REST(config,[],logger)
    rest.run()
