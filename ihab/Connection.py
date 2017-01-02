try:
    # python 2.7
    from urllib import quote
    from urllib import urlencode
except ImportError:
    # python 3.4
    from urllib.parse import quote
    from urllib.parse import urlencode
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl
import sys
import json

class Connection(object):

    def __init__(self, logger, address, port, username=False, password=False):
        self._logger   = logger
        self._address = address
        self._port = port
        self._username = username
        self._password = password
        # test settings
        # TODO: Need a way to just connect without sending a request to make sure it works?
        #if not self.ping():
        #    raise(ValueError('Could not connect to the %s:%s ' % (address,str(port))))

    def request(self, path, type='get', payload=None, body=None, ok404=False):
        url = "http://{}:{}/api{}".format(self._address,self._port,path)
        #auth = HTTPDigestAuth(self.user,self.password)
        #auth = (self.user,self.password)
        try:
            if (type == 'get'):
                self._logger.info("request:get: %s",url)
                response = requests.get(
                    url,
                    #auth=auth,
                    params=payload,
                    timeout=10
                )
            elif (type == 'delete'):
                self._logger.info("request:delete: %s",url)
                response = requests.delete(
                    url,
                    #auth=auth,
                    params=payload,
                    timeout=10
                )
            elif (type == 'post'):
                self._logger.info("request:post: %s",url)
                self._logger.info("request:post: body=%s", body)
                response = requests.post(
                    url,
                    #auth=auth,
                    #params=payload,
                    data=json.dumps(body),
                    timeout=10
                )
            elif (type == 'put'):
                self._logger.info("request:put: %s",url)
                response = requests.put(
                    url,
                    #auth=auth,
                    data=json.dumps(body),
                    timeout=10
                )
            else:
                raise(ValueError("type must be get, delete, put, or post, not '%s'" % (type)))
                
        except requests.exceptions.Timeout:
            self._logger.error("Connection timed out: %s", url)
            return (None,"")
        except requests.ConnectionError as err:
            self._logger.error('ConnectionError: %s', url)
            return (None,"")
        self._logger.info("request:connect:success: url=%s", response.url)
        self._logger.debug("request:connect:success: text=%s", response.text)
        if response.status_code == 200 or response.status_code == 201:
            return (True,response.text)
        elif response.status_code == 400:
            self.parent.logger.error("reqeust: error %s", self.name, response.text)
        elif response.status_code == 401:
            # Authentication error
            self.parent.logger.error(
                "Failed to authenticate, "
                "please check your username and password")
            return
        elif response.status_code == 404:
            if ok404:
                self._logger.info('request: 404 received, and ignored')
                return (False,response.text)
            else:
                self._logger.info('request: 404 received, and not ignored')
                return (False,response.text)
        else:
            self._logger.error("Invalid response from %s: %s: %s", response.url,response,response.text)
            return (False,response.text)


    # PING
    # This is a dummy command that does not exist in the REST API
    # this function return True if the device is alive
    #def ping(self):
    #    #req_url = self.compileURL(['devices/habridge/version'])
    #    #req_url = self.compileURL(['devices'])
    #    result = self.request('', ok404=True)
    #    return result is not None

