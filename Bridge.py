
import json
from Connection import Connection

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
            #"username"   : "ihb:%s:%s" % (self.host,self.port),
        }
        (bstat,info) = self.connection.request('', type='post', body=data)
        if bstat:
            info = json.loads(info)
            print info[0]
            self.username = info[0]["success"]["username"]
        # TODO: else should throw error
        self.logger.error("bridge: username=%s",self.username)
        
    def get_devices(self):
        (bstat,devices) = self.connection.request('/devices')
        if bstat != True:
            self.logger.error("bridge: communicating with bridge %s:%s",self.host,self.port)
            return False
        self.devices = json.loads(devices)
        #print json.dumps(self.devices)
        for dev in self.devices:
            if "mapId" in dev:
                self.logger.debug("bridge: found name=%s id=%s mapId=%s",dev["name"],dev["id"],dev["mapId"])
            else:
                self.logger.debug("bridge: found name=%s id=%s mapId=()",dev["name"],dev["id"])

    def devices(self):
        return self.devices

    def add_or_update_device(self,device):
        fdev = self.has_device_by_mapId(device["mapId"])
        if fdev is False:
            sdev = self.has_device_by_name(device["name"])
            if sdev is not False:
                self.logger.info("bridge:add_or_update: already have device '%s' as %s, will change to %s",device["name"],sdev["mapId"],device["mapId"])
                return self.update(sdev,device)
            else:
                return self.add(device)
        else:
            # Already have a device with our mapId, so update it in case something changed.
            return self.update(fdev,device)

    def add(self,device):
        self.logger.info("bridge:add: '%s' %s",device["name"],device["mapId"])
        (st,res) = self.connection.request('/devices', type='post', body=device)
        self.logger.info("bridge:add: st=%s",st)
        # TODO: Parse return res to make sure it was "success"?
        if st:
            res = json.loads(res)
            id = res[0]["id"]
            return(st,id)
        else:
            self.logger.error("bridge:add: " + device)
            return(st,"")

    def delete(self,device):
        self.logger.info("bridge:delete: %s '%s' %s",device["id"],device["name"],device["mapId"])
        (st,res) = self.connection.request('/devices/%s' % device["id"], type='delete')
        self.logger.info("bridge:delete: st=%s",st)
        return st

    def update(self,cdev,udev):
        self.logger.info("bridge:update: '%s' %s",cdev["name"],cdev["mapId"])
        # Update cdev with params in udev
        i = 0
        for item in udev:
            if cdev[item] != udev[item]:
                self.logger.info("bridge:update: %s '%s'->'%s'",item,cdev[item],udev[item])
                cdev[item] = udev[item]
                i += 1
        if i > 0:
            #self.logger.info("bridge:update:" + str(cdev))
            (st,res) = self.connection.request('/devices/%s' % (cdev["id"]), type='put', body=cdev)
            self.logger.info("bridge:update: st=%s",st)
            # TODO: Parse return res to make sure it was "success"?
            if st:
                (cst,cres) = self.connection.request('/devices/%s' % (cdev["id"]), type='get')
            else:
                self.logger.error("bridge:update: " + str(cdev))
        else:
            # Nothing to update.
            self.logger.info("bridge:update: No change for '%s'",cdev["name"])
            st = True
        return (st,cdev["id"])
        
    def has_device_by_mapId(self,mapId):
        for dev in self.devices:
            if "mapId" in dev and dev["mapId"] == mapId:
                return dev
        return False

    def has_device_by_name(self,name):
        for dev in self.devices:
            if dev["name"] == name:
                return dev
        return False

    def set_device_state(self,id,on,bri):
        state = {
            "on"  : on,
            "bri" : bri,
        }
        self.logger.info("bridge:set_device_state '%s'=%s",id,state)
        #(st,res) = self.connection.request('/%s/lights/%s/bridgeupdatestate' % (self.username,id), type='put', body=state)
