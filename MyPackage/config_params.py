import configparser
import os
import MyPackage.logging_config

parser = configparser.ConfigParser()

try:
    if os.path.isfile("config.ini"):
        parser.read("config.ini")
    else:
        raise FileNotFoundError
except FileNotFoundError:
    MyPackage.logging_config.log.error("Error: Configuration file not found. Please check and try again")

Settings = parser["Settings"]
Jump_Servers = parser["Jump_Server"]
