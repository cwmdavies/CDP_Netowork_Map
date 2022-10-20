import sys
import logging
from Main import Debugging, FolderPath


# Log file location
logfile = f'{FolderPath}\\debug.log'

# Define the log format
log_format = (
    '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')

# Define basic configuration
if Debugging == "Off":
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
elif Debugging == "On":
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

# Define your own logger name
log = logging.getLogger(__name__)
