import configparser
import os
import logging.config

logging.config.fileConfig(fname='MyPackage//logging.conf',
                          disable_existing_loggers=False,
                          defaults={'logfilename': "debug.log"})
log = logging.getLogger(__name__)

parser = configparser.ConfigParser()

try:
    if os.path.isfile("MyPackage//global_config.ini"):
        parser.read("MyPackage//global_config.ini")
    else:
        raise FileNotFoundError
except FileNotFoundError:
    log.error("Error: Configuration file not found. Please check and try again")

Settings = parser["Settings"]
Jump_Servers = parser["Jump_Server"]
