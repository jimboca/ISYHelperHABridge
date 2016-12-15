#!/usr/bin/python
#

NAME    = "ISYHABridge"
VERSION = "1.15"

# When run in directory containing downloaded PyIsy
import sys
import logging
import logging.handlers
import time
import json
import yaml
import socket
import os
from Connection import Connection
from Rest import Rest
try:
    # python 2.7
    from urllib import quote
    from urllib import urlencode
except ImportError:
    # python 3.4
    from urllib.parse import quote
    from urllib.parse import urlencode
# Load our dependancies
from datetime import datetime
sys.path.insert(0,"../PyISY")
sys.path.insert(0,"../VarEvents")
import PyISY

print('ISYHelperHABridge: Version %s Started: %s' % (VERSION, datetime.now()))
def get_network_ip(rhost):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((rhost, 0))
    return s.getsockname()[0]

def load_config ():
    config_file = open('config.yaml', 'r')
    config = yaml.load(config_file)
    config_file.close
    # host config param overrides default.
    if 'host' in config and config['host'] is not None:
        # use what the user has defined.
        this_host = config['host']
    else:
        # Only way to get the current host ip is connect to something, so use the ISY.
        this_host = get_network_ip(config['isy']['host'])
    # port config param overrides port
    port = '8088'
    if 'port' in config and config['port'] is not None:
        port = str(config['port'])
    config['this_host'] = {
        'host' : this_host,
        # TODO: This is the REST interface, should be configurable?
        'port' : port,
    }
    # TODO: Check all isy and bridge params are defined.
    if 'isy' in config:
        if not 'log_enable' in config['isy']:
            config['isy']['log_enable'] = False
    config['this_host']['url'] = 'http://'+config['this_host']['host']+':'+config['this_host']['port']
    config['log_format']       = '%(asctime)-15s:%(name)s:%(levelname)s: %(message)s'
    config['version']          = VERSION
    return config

def get_logger(config):
    if 'log_file' not in config:
        config['log_file'] = False
        print("No log_file defined")
    elif config['log_file'] == 'none':
        print("Not writing log because log_file is none")
        config['log_file'] = False

    if config['log_file'] != False:
        print('Writing to log: %s level=%s' % (config['log_file'],str(config['log_level'])))
        if os.path.exists(config['log_file']):
            os.remove(config['log_file'])
        # Create the logger
        logger = logging.getLogger('IH')
        # Set the log level Warning level by default, unless log_level is debug or info
        if config['log_level'] == 'debug':
            logger.setLevel(logging.DEBUG)
        elif config['log_level'] == 'info':
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)
        # Make a handler that writes to a file, 
        # making a new file at midnight and keeping 30 backups
        handler = logging.handlers.TimedRotatingFileHandler(config['log_file'], when="midnight", backupCount=7)
        # Format each log message like this
        formatter = logging.Formatter(config['log_format'])
        # Attach the formatter to the handler
        handler.setFormatter(formatter)
        # Attach the handler to the logger
        logger.addHandler(handler)
    else:
        logger = False
    return logger

class isy():
    def __init__(self,config,logger,bridge):
        self.config = config
        self.logger = logger
        self.user   = config['isy']['user']
        self.password = config['isy']['password']
        self.host     = config['isy']['host']
        self.port     = config['isy']['port']
        self.bridge   = bridge
        self.nurl = "http://%s:%s@%s:%s/rest/nodes" % (self.user,self.password,self.host,self.port)
        if config['isy']['log_enable']:
            log = self.logger
        else:
            log=None
        info = "ihab:isy: %s:%s log=%s" % (self.host,self.port,log)
        print(info)
        logger.info(info)
        isy = PyISY.ISY(self.host, self.port, self.user, self.password, False, "1.1", log=log)
        info = "ish: connected: %s" % (str(isy.connected))
        print(info)
        logger.info(info)
        isy.auto_update = True
        self.devices = []

        info = "ihab:isy: ISY for Spoken objects."
        print(info)
        logger.info(info)
        idevs  = []
        for child in isy.nodes.allLowerNodes:
            #print child
            if child[0] is 'node' or child[0] is 'group':
                logger.info(child)
                mnode = isy.nodes[child[2]]
                spoken = mnode.spoken
                if spoken is not None:
                    # TODO: Should this be a comman seperate list of which echo will respond?
                    # TODO: Or should that be part of notes?
                    if spoken == '1':
                        spoken = mnode.name
                    logger.info("name=%s spoken=%s" % (mnode.name,str(spoken)))
                    cnode = False
                    if child[0] is 'node':
                        # Is it a controller of a scene?
                        cgroup = mnode.get_groups(responder=False)
                        if len(cgroup) > 0:
                            cnode = isy.nodes[cgroup[0]]
                            logger.info("%s is a scene controller of %s='%s'" % (str(cgroup[0]),str(cnode),cnode.name))
                        else:
                            cnode = mnode
                            if len(mnode.controllers) > 0:
                                mnode = isy.nodes[mnode.controllers[0]]
                    self.devices.append(isy_node_handler(self,spoken,mnode,cnode))
    # TODO: If idevs size is zero, no spoken devices in ISY, or ERROR in log.
        
#
# These push device changes to the ha-bridge
#
class isy_node_handler():

    def __init__(self, parent, name, node, scene):
        self.parent  = parent
        self.name    = name
        self.node    = node
        self.scene   = scene
        node.status.subscribe('changed', self.get_all_changed)
        self.parent.logger.info('ihab:isy.__init__:  name=%s node=%s scene=%s' % (self.name, self.node, self.scene));
        self.add_or_update()
        
    def add_or_update(self):
        sobj = self.node
        if self.scene != False:
            sobj = self.scene
        purl = "%s/%s/cmd" % (self.parent.nurl,quote(sobj._id))
        self.payload = {
            'name'       : self.name,
            'mapId'      : "isy:%s" % (sobj._id),
            'deviceType' : 'custom',
            'onUrl'      : "%s/DON" % (purl),
            'dimUrl'     : "%s/DON/${intensity.byte}" % (purl),
            'offUrl'     : "%s/DOF" % (purl),
            'httpVerb'   : 'GET',
        }
        (st,id) = self.parent.bridge.add_or_update_device(self.payload)
        self.bid = id
        
    def get_all_changed(self,e):
        self.parent.logger.info('ihab:isy.get_all_changed:  %s e=%s' % (self.name, str(e)));
        self.get_all()

    def get_all(self):
        self.parent.logger.info('ihab:isy.get_all:  %s status=%s' % (self.name, str(self.node.status)));
        # node.status will be 0-255
        self.bri = self.node.status
        if int(self.node.status) == 0:
            self.on  = "false"
        else:
            self.on  = "true"
        self.parent.logger.info('ihab:isy.get_all:  %s on=%s bri=%s' % (self.name, self.on, str(self.bri)));
        self.parent.bridge.set_device_state(self.bid,self.on,str(self.bri))
                
    def set_on(self):
        self.parent.logger.info('pyhue:isy_handler.set_on: %s node.on()' % (self.name));
        if self.scene != False:
            ret = self.scene.on()
            self.parent.logger.info('pyhue:isy_handler.set_on: %s scene.on() = %s' % (self.name, str(ret)));
        else:
            # TODO: If the node is a KPL button, we can't control it, which shows an error.
            ret = self.node.on()
        return ret
                
    def set_off(self):
        self.parent.logger.info('pyhue:isy_handler.set_off: %s node.off()' % (self.name));
        if self.scene != False:
            ret = self.scene.off()
            self.parent.logger.info('pyhue:isy_handler.set_off: %s scene.off() = %s' % (self.name, str(ret)));
        else:
            # TODO: If the node is a KPL button, we can't control it, which shows an error.
            ret = self.node.off()
            return ret
                
    def set_bri(self,value):
        self.parent.logger.info('pyhue:isy_handler.set_bri: %s on val=%d' % (self.name, value));
        # Only set directly on the node when it's dimmable and value is not 0 or 254
        if self.node.dimmable and value > 0 and value < 254:
            # val=bri does not work?
            ret = self.node.on(value)
            self.parent.logger.info('pyhue:isy_handler.set_bri: %s node.on(%d) = %s' % (self.name, value, str(ret)));
        else:
            if value > 0:
                ret = self.set_on()
                self.bri = 255
            else:
                ret = self.set_off()
                self.bri = 0
        self.parent.logger.info('pyhue:isy_handler.set_bri: %s on=%s bri=%d' % (self.name, self.on, self.bri));
        return ret

class bridge():
    def __init__(self,config,logger):
        self.config = config
        self.logger = logger
        self.host = config['bridge']['host']
        self.port = config['bridge']['port']
        info = "ihab:bridge: %s:%s" % (self.host,self.port)
        print info
        logger.info(info)
        self.connection = Connection(logger,self.host,self.port)
        self.get_username()
        self.get_devices()

    def get_username(self):
        data = {
            "devicetype" : "ihb:%s:%s" % (self.host,self.port),
            "username"   : "ihb:%s:%s" % (self.host,self.port),
        }
        (bstat,info) = self.connection.request('', type='post', body=data)
        if bstat:
            info = json.loads(info)
            print info[0]
            self.username = info[0]["success"]["username"]
        # TODO: else should throw error
        
    def get_devices(self):
        (bstat,devices) = self.connection.request('/devices')
        if bstat != True:
            self.logger.error("ihab:bridge: communicating with bridge %s:%s",self.host,self.port)
            return False
        self.devices = json.loads(devices)
        #print json.dumps(self.devices)
        for dev in self.devices:
            self.logger.debug("ihab:brige: found name=%s id=%s mapId=%s",dev["name"],dev["id"],dev["mapId"])

    def add_or_update_device(self,device):
        fdev = self.has_device_by_mapId(device["mapId"])
        if fdev is False:
            self.logger.info("ihab:bridge: adding device '%s' %s",device["name"],device["mapId"])
            (st,res) = self.connection.request('%s/devices' % (self.username),type='post', body=device)
            self.logger.info("ihab:bridge: st=%s",st)
            if st:
                res = json.loads(res);
                return(st,res["id"])
            else:
                return(st,"")
        else:
            self.logger.info("ihab:bridge: device '%s' %s already exists",device["name"],device["mapId"])
            (st,res) = self.connection.request('/%s/devices/%s' % (self.username,fdev["id"]), type='post', body=device)
            self.logger.info("ihab:bridge: st=%s",st)
            return (st,fdev["id"])
        
        
    def has_device_by_mapId(self,mapId):
        for dev in self.devices:
            if dev["mapId"] == mapId:
                return dev
        return False

    def set_device_state(self,id,on,bri):
        state = {
            "on"  : on,
            "bri" : bri,
        }
        self.logger.info("ihab:bridge:set_device_state '%s'=%s",id,state)
        (st,res) = self.connection.request('/%s/lights/%s/bridgeupdatestate' % (self.username,id), type='put', body=state)
    
# Load the config file.
config = load_config();
print("This host IP is " + config['this_host']['host'])

# Start the log_file
logger = get_logger(config)

# Prepare the REST interface
rest = Rest(config,logger)

bridge = bridge(config,logger)

isy = isy(config,logger,bridge)

# Start the REST interface
# TODO: I'm not really happy with having the rest be an object, since auto-reload does not work
info = "Starting REST interface..."
logger.info(info)
print info
rest.run()
