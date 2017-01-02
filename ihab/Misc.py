
import yaml
import socket
import os
import logging
import logging.handlers

global NAME
global VERSION
NAME    = "ISYHABridge"
VERSION = "0.2"

#
# Misc functions.
#
def get_network_ip(rhost):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((rhost, 0))
    return s.getsockname()[0]

def load_config ():
    error = False
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
    # Check use_rest
    if 'use_rest' in config:
        if not ( config['use_rest'] is False or config['use_rest'] is True ):
            print "ERROR: use_rest must be true or false, not " + str(config['use_rest'])
    else:
        config['use_rest'] = True
    # TODO: Check all isy and bridge params are defined.
    if 'isy' in config:
        if not 'host' in config['isy']:
            print "ERROR: isy host not defined in config"
            error = True
        if not 'port' in config['isy']:
            print "ERROR: isy port not defined in config"
            error = True
        if not 'user' in config['isy']:
            print "ERROR: isy user not defined in config"
            error = True
        if not 'password' in config['isy']:
            print "ERROR: isy password not defined in config"
            error = True
        if not 'log_enable' in config['isy']:
            config['isy']['log_enable'] = False
    else:
        print "ERROR: isy not defined in config"
        error = True
    if 'bridge' in config:
        # Default bridge is this host.
        if not 'host' in config['bridge'] or config['bridge']['host'] == "" or config['bridge']['host'] == None:
            config['bridge']['host'] = config['this_host']['host']
        if not 'port' in config['bridge'] or config['bridge']['port'] == "" or config['bridge']['port'] == None:
            config['bridge']['port'] = 80

    if error:
        exit
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
        logger = logging.getLogger('IHAB')
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
