
try:
    # python 2.7
    from urllib import quote
    from urllib import urlencode
except ImportError:
    # python 3.4
    from urllib.parse import quote
    from urllib.parse import urlencode
import sys
import re
import PyISY

class isy():
    def __init__(self,config,logger,status,bridge):
        self.config = config
        self.logger = logger
        self.status = status
        self.user   = config['isy']['user']
        self.password = config['isy']['password']
        self.host     = config['isy']['host']
        self.port     = config['isy']['port']
        self.bridge   = bridge
        self.isy_url  = "http://%s:%s@%s:%s/rest/nodes" % (self.user,self.password,self.host,self.port)
        self.ihb_url  = "http://%s:%s" % (config['this_host']['host'],config['this_host']['port'])
        if config['isy']['log_enable']:
            log = self.logger
        else:
            log=None
        self.status.set("isy: Connecting %s:%s log=%s" % (self.host,self.port,log))
        self.isy = PyISY.ISY(self.host, self.port, self.user, self.password, False, "1.1", log=log)
        self.status.set("isy: connected: %s" % (str(self.isy.connected)))
        self.isy.auto_update = True
        self.get_spoken()

    def get_spoken(self):
        self.status.set("isy: Checking for Spoken objects.")
        self.devices = []
        for child in self.isy.nodes.allLowerNodes:
            #print child
            if child[0] is 'node' or child[0] is 'group':
                #self.logger.info(child)
                main = self.isy.nodes[child[2]]
                spoken = main.spoken
                if spoken is not None:
                    # TODO: Should this be a comman seperate list of which echo will respond?
                    # TODO: Or should that be part of notes?
                    if spoken == '1':
                        spoken = main.name
                    self.logger.info("isy: name=%s spoken=%s" % (main.name,str(spoken)))
                    scene = False
                    if child[0] is 'node':
                        # Is it a controller of a scene?
                        cgroup = main.get_groups(responder=False)
                        if len(cgroup) > 0:
                            # TODO: We don't need to do this anymore, since we can put Spoken on Scenes!
                            scene = self.isy.nodes[cgroup[0]]
                            self.logger.info("isy: %s is a scene controller of %s='%s'" % (str(cgroup[0]),str(scene),scene.name))
                    #else:
                        # TODO: This shoud be all scene responders that are dimmable?
                        # TODO: Let set_on commands handle these
                        #if len(main.controllers) > 0:
                        #    scene = self.isy.nodes[main.controllers[0]]
                    if self.has_device_by_name(spoken) is False:
                        self.devices.append(isy_node_handler(self,spoken,main,scene))
                    else:
                        self.logger.error("isy: Duplicate Ignored: '%s' for main='%s' scene=%s" % (spoken,main,scene))
        # Now that we have all devices, delete bridge devices that don't exist anymore
        prog = re.compile("isy:.+$")
        for bdev in self.bridge.devices:
            if self.has_device_by_id(bdev["id"]) is False and "mapId" in bdev and prog.match(bdev["mapId"]):
                self.logger.warning("isy: Removing bridge device %s '%s'(%s)",bdev["id"],bdev["name"],bdev["mapId"])
                self.bridge.delete(bdev)
            
    def has_device_by_name(self,name):
        for dev in self.devices:
            if dev.name == name:
                return dev
        return False

    def has_device_by_id(self,id):
        for dev in self.devices:
            if dev.bid == id:
                return dev
        return False

    def has_device_by_mapid(self,map_id):
        for dev in self.devices:
            if dev.map_id == map_id:
                return dev
        return False

    def do_cmd(self,id,cmd,val=None):
        dev = self.has_device_by_id(id)
        if dev is False:
            self.logger.error("isy: No device '%s' for command '%s'",str(id),cmd)
            return dev
        if cmd == "on":
            if val is None:
                return dev.set_on()
            else:
                return dev.set_bri(val)
        elif cmd == "off":
            return dev.set_off()
        self.logger.error("isy: Unknown command '%s' for device '%s'",cmd,str(id))
        return False
        
#
# These push device changes to the ha-bridge
#
class isy_node_handler():

    def __init__(self, parent, name, main, scene):
        self.parent  = parent
        # Force as string to make habridge happy?
        self.name    = str(name)
        self.main    = main
        self.scene   = scene
        self.map_id  = str("isy:%s" % (self.main._id))
        self.parent.logger.info('isy:node:.__init__:  name=%s node=%s scene=%s' % (self.name, self.main, self.scene))
        # Subscribe to changes, if main is not a scene.
        # This is because PyISY notification of scene on/off doesn't work properly,
        # it notifies if anything on the kpl controlling that scene changes?
        if type(self.main).__name__ != "Group":
            main.status.subscribe('changed', self.get_all_changed)
        # ISY URL's
        self.isy_url = "%s/%s/cmd" % (self.parent.isy_url,quote(self.main._id))
        self.isy_on  = "%s/DON" % (self.isy_url)
        self.isy_off = "%s/DOF" % (self.isy_url)
        self.isy_bri = "%s/DON/{}" % (self.isy_url)
        # The URL's that are passed to ha-bridge to control this device.
        self.f_on  = self.isy_on
        self.f_off = self.isy_off
        # TODO: If main is a scene, we should not set this since it does nothing?
        self.f_bri = self.isy_bri
        # Add it to the ha-bridge cause we need it's id for the ihb url's
        self.add_or_update()
        # IHB URL's
        self.ihb_url = "%s/device/%s" % (self.parent.ihb_url,quote(self.bid))
        self.ihb_on  = "%s/on" % (self.ihb_url)
        self.ihb_off = "%s/off" % (self.ihb_url)
        self.ihb_bri = "%s/on/{}" % (self.ihb_url)
        # TODO: Reset f_* functions if controlling thru ihab
        if self.scene is not False or self.parent.config['use_rest'] is not True:
            self.f_on  = self.ihb_on
            self.f_off = self.ihb_off
            self.f_bri = self.ihb_bri
            self.add_or_update()
        # Set my on/off/bri status.
        self.get_all()
        
    def add_or_update(self):
        self.payload = {
            'name'       : self.name,
            'mapId'      : self.map_id,
            'deviceType' : 'custom',
            'onUrl'      : self.f_on,
            'dimUrl'     : self.f_bri.format('${intensity.byte}'),
            'offUrl'     : self.f_off,
            'httpVerb'   : 'GET',
        }
        (st,id) = self.parent.bridge.add_or_update_device(self.payload)
        self.bid = id
        
    def get_all_changed(self,e):
        self.parent.logger.info('isy:get_all_changed:  %s e=%s' % (self.name, str(e)))
        self.get_all()

    def get_all(self):
        self.parent.logger.info('isy:get_all:  %s status=%s' % (self.name, str(self.main.status)))
        # node.status will be 0-255
        self.bri = self.main.status
        if int(self.main.status) == 0:
            self.on  = "false"
        else:
            self.on  = "true"
        self.parent.logger.info('isy:get_all:  %s on=%s bri=%s' % (self.name, self.on, str(self.bri)))
        self.parent.bridge.set_device_state(self.bid,self.on,str(self.bri))
                
    def set_on(self):
        self.parent.logger.info('isy:set_on: %s node.on()' % (self.name))
        if self.scene is False:
            # TODO: If the node is a KPL button, we can't control it, which shows an error.
            ret = self.main.on()
        else:
            ret = self.scene.on()
            self.parent.logger.info('isy:set_on: %s scene.on() = %s' % (self.name, str(ret)))
        return ret
                
    def set_off(self):
        self.parent.logger.info('isy:set_off: %s node.off()' % (self.name))
        if self.scene is False:
            # TODO: If the node is a KPL button, we can't control it, which shows an error.
            ret = self.main.off()
        else:
            ret = self.scene.off()
            self.parent.logger.info('isy:set_off: %s scene.off() = %s' % (self.name, str(ret)))
        return ret
                
    def set_bri(self,value):
        value = int(value)
        self.parent.logger.info('isy:set_bri: %s on val=%d main-type=%s scene=%s' % (self.name, value, type(self.main).__name__, self.scene))
        # Just controlling a device/scene?
        if self.scene is False:
            if type(self.main).__name__ == "Group":
                # The main is a scene, so set all it's members
                ret = True
                for mem in self.main.members:
                    if not self._set_bri(self.main.parent[mem],value):
                        ret = False
            else:
                # The main is not a controller of a scene (Group), so just control the main.
                ret = self._set_bri(self.main,value)
        else:
            # Controlling all responders in the scene.
            ret = True
            for mem in self.scene.members:
                if not self._set_bri(self.scene.parent[mem],value):
                    ret = False
        if ret:
            self.bri = value
        return ret

    def _set_bri(self,device,value):
        # Only set directly on the node when it's dimmable and value is not 0
        self.parent.logger.info('isy:set_bri: %s on val=%d' % (self.name, value))
        if device.dimmable and value > 0:
            # val=bri does not work?
            # TODO: If the device is not already on, then turn the scene on, then change the brigthness
            ret = device.on(value)
            self.parent.logger.info('isy:_set_bri: %s %s.on(%d)' % (self.name, device.name, value))
        else:
            if value > 0:
                self.parent.logger.info('isy:_set_bri: %s %s.on()' % (self.name, device.name))
                ret = device.on()
                self.bri = 255
            else:
                self.parent.logger.info('isy:_set_bri: %s %s.off() = %s' % (self.name, device.name))
                ret = device.off()
        self.parent.logger.info('isy:_set_bri: %s %s on=%s bri=%d' % (self.name, device.name, self.on, self.bri))
        return ret
