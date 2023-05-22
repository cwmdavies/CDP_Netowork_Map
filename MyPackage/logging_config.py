import sys
import logging
import os
from MyPackage import config_params

Debugging = config_params.Settings["Debugging"]
FolderPath = os.getcwd()

# Log file location
logfile = f'{FolderPath}\\debug.log'

# Define the log format
log_format = (
    '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')

# Define basic configuration
if Debugging == "0":
    logging.basicConfig(
        # Define logging level
        level=logging.INFO,
        # Declare the object we created to format the log messages
        format=log_format,
        # Declare handlers
        handlers=[
            logging.FileHandler(logfile),
            logging.StreamHandler(sys.stdout),
        ]
    )
    logging.getLogger("paramiko").setLevel(logging.ERROR)
elif Debugging == "1":
    logging.basicConfig(
        # Define logging level
        level=logging.DEBUG,
        # Declare the object we created to format the log messages
        format=log_format,
        # Declare handlers
        handlers=[
            logging.FileHandler(logfile),
            logging.StreamHandler(sys.stdout),
        ]
    )

log = logging.getLogger(__name__)
