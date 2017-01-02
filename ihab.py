#!/usr/bin/python
#
# TODO:
#  - Catch ISY or BRIGDE errors to and log them
#  - Start REST in a thread, so it is activated earlier
#

# Load our dependancies
import sys,time,threading,subprocess,re,os
from operator import itemgetter, attrgetter, methodcaller
from traceback import format_exception
#from multiprocessing import Process, Queue;
from flask import Flask
from flask import request
#from Rest import Rest
from datetime import datetime
# We need the new version of PyISY which isn't released...
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.realpath(__file__)))+"/PyISY")
# Our libs are in the same dir as this file + ihab
sys.path.insert(0,os.path.dirname(os.path.realpath(__file__))+"/ihab")
from Misc import load_config,get_logger
from Bridge import bridge
from ISY import isy

# ******************************************************************************

# Load the config file.
config = load_config()
print('ISYHelperHABridge: Version %s Started: %s' % (config['version'], datetime.now()))
print("This host IP is " + config['this_host']['host'])

# Start the log_file
logger = get_logger(config)

class status_obj():

    def __init__(self,status):
        self.status = status

    def set(self,status):
        self.status = status
        if status is not False:
            logger.info(status)
            print status

    def get(self):
        return self.status

global status
status = status_obj("Starting...")

# ******************************************************************************
#
# flask server setup
#
global some_queue
some_queue = None
global st_queue
st_queue = None
#
# Start the REST interface
#
status.set("Starting...")
# REST Interface
app = Flask(__name__)
# TODO: Need a way to set debug in config an rest command
app.debug = False

@app.route("/")
def top():
    global status
    try:
        app.logger.info("REST:top")
        out  =["ISYHelper HABridge: %s<br>Requestor: %s<br>" % (config['version'],request.remote_addr)]
        out.append("<h1><A HREF='http://%s:%s'>ha-bridge</A>\n" % (config['bridge']['host'],config['bridge']['port']))
        out.append("<h1>Functions:</h1><ul>\n")
        out.append("<li><A HREF='/log'>View Log</A><br>")
        out.append("<li><A HREF='/restart'>Restart IHAB</A><br>")
        out.append("<li><A HREF='/exit'>Exit IHAB</A><br>")
        out.append("<li><A HREF='/debug/on'>Debug REST On</A><br>")
        out.append("<li><A HREF='/debug/off'>Debug REST Off</A><br>")
        out.append("<li><A HREF='/refresh'>Refresh ISY Devices</A><br>")
        out.append("</ul>")
        if status.get() is False:
            out.append("<h1>ISY Spoken Devices</h1><ul>\n<table>")
            out.append("<tr border=1><th>HueId<th>Spoken<th colspan=2>Device<th colspan=3>ISY Commands<th colspan=3>IHAB Commands<th colspan=2>Scene</tr>")
            for device in sorted(isy.devices, key=attrgetter('name')):
                out.append("<tr><td>{0}<td>{1}<td>{2}<td>{3}".format(device.bid,device.name,device.main._id,device.main.name))
                out.append("<td><A HREF='{0}'>on</a><td><A HREF='{1}'>off</a><td><A HREF='{2}'>50%</a>".format(device.isy_on,device.isy_off,device.isy_bri.format('128')))
                out.append("<td><A HREF='{0}'>on</a><td><A HREF='{1}'>off</a><td><A HREF='{2}'>50%</a>".format(device.ihb_on,device.ihb_off,device.ihb_bri.format('128')))
                if device.scene is False:
                    out.append("<td>{0}<td>&nbsp;".format(device.scene))
                else:
                    out.append("<td>{0}<td>{1}".format(device.scene._id,device.scene.name))
            out.append("</table>")
        else:
            out.append("<h3>Status: {}</h3>".format(status.get()))
        return ''.join(out)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return "<pre>Top Error: %s</pre>" % ''.join(format_exception(exc_type, exc_value, exc_traceback))

@app.route("/log")
def log():
    app.logger.info("REST:log")
    if config['log_file'] == None or config['log_file'] == "none" or config['log_file'] == "":
        return "config log_file="+config['log_file']
    out = ["ISYHelper HABridge: %s<br>" % (config['log_file'])]
    fo = open(config['log_file'],"r")
    for line in fo:
        out.append(line+"<br>")
    fo.close
    return ''.join(out)

@app.route("/device/<id>/<cmd>")
def device_id_cmd(id,cmd):
    app.logger.info("REST:device %s %s",id,cmd)
    if isy.do_cmd(id,cmd):
        return "ok", 200
    else:
        return "ERROR", 404
        
@app.route("/device/<id>/<cmd>/<val>")
def device_id_cmd_val(id,cmd,val):
    app.logger.info("REST:device %s %s",id,cmd)
    if isy.do_cmd(id,cmd,val):
        return "ok", 200
    else:
        return "ERROR", 404

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/debug/<val>')
def debug(val):
    if val == 'on':
        ret = "REST:debug: True"
        app.debug = True
    else:
        ret = "REST:debug: False"
        app.debug = False
    app.logger.info(ret)
    return ret, 200

@app.route('/restart')
def restart():
    try:
        shutdown_server()
        status.set("restart")
        return status.get()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return "<pre>Restart Error: %s</pre>" % ''.join(format_exception(exc_type, exc_value, exc_traceback))

@app.route('/exit')
def exit():
    try:
        shutdown_server()
        status.set("exit")
        return status.get()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return "<pre>Exit Error: %s</pre>" % ''.join(format_exception(exc_type, exc_value, exc_traceback))

@app.route('/refresh')
def refresh():
    try:
        status.set("Rebuilding spoken...")
        # TODO: This needs to be run in a thread since it takes a while?
        isy.get_spoken()
        status.set(False)
        return 'Spoken updated'
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return "<pre>Refresh Error: %s</pre>" % ''.join(format_exception(exc_type, exc_value, exc_traceback))


# ******************************************************************************
#
# Start the REST Server
#
class RestThread(threading.Thread):
    def __init__(self):
        #self.threadID = threadID
        threading.Thread.__init__(self)

    def run(self):
        status.set("Starting REST interface...")
        app.run(host=config['this_host']['host'], port=int(config['this_host']['port']), use_reloader=False)
        # Can't call 
        print "Exiting REST interface..."

rest_thread = RestThread()
rest_thread.daemon = True
rest_thread.start()

   
# ******************************************************************************
#
# Prep the bridge
#
status.set("Initializing bridge...")
try:
    bridge = bridge(config,logger)
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    err_str = ''.join(format_exception(exc_type, exc_value, exc_traceback))
    status.set("Error initializing bridge: %s" % (err_str))
#
# Create ISY Connection
#
status.set("Initializing ISY...")
try:
    isy = isy(config,logger,status,bridge)
except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    err_str = ''.join(format_exception(exc_type, exc_value, exc_traceback))
    status.set("Error initializing ISY: %s" % (err_str))
#
# Hang around until told to quit.
#
status.set("Initialization complete.")
status.set(False)
# Don't give control to flask, since that causes cntl-C to be ignored...
iprog = re.compile("isy: .+$")
try:
    while True:
        if status.get() is False:
            time.sleep(1)
        elif iprog.match(status.get()):
            # ISY is busy updating...
            time.sleep(1)
        else:
            break
    if status.get() == "restart":
        args = [sys.executable] + [sys.argv[0]]
        status.set("Restarting: %s" % (args))
        subprocess.call(args)
    elif status.get() == "exit":
        status.set("Exiting...")
    else:
        print "Uknown Status " + status.get() + " Exiting.."
except KeyboardInterrupt:
    print "Exiting from interrupt"
except:
    raise
