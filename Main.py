"""
Author Details:
Name: Chris Davies
Email: chris.davies@weavermanor.co.uk

Tested on Python 3.8 to 3.10

This script takes in up to two IP Addresses, preferably the core switches, runs the "Show CDP Neighbors Detail"
command and saves the information to a list of dictionaries. Each dictionary is then parsed for the neighbouring
IP Address for each CDP neighbour and saved to a separate list. Another list is used to store the IP Addresses
of those that have been processed so no switch is connected too more than once. Each IP Address in the list
is connected to, up to 10 at a time, to retrieve the same information. This recursion goes on until there are no
more IP Addresses to connect to. The information is then converted to a numpy array and saved to an Excel spreadsheet.

Threading is used to connect to multiple switches at a time.
Each IP Address is checked to ensure each IP Address is valid.
"""

import MyPackage.MyGui as MyGui
import paramiko
import textfsm
import ipaddress
import logging
import sys
import time
from multiprocessing.pool import ThreadPool
from multiprocessing import Lock
from tkinter import Tk
import ctypes
import pandas as pd
from openpyxl import load_workbook

local_IP_address = '127.0.0.1'  # ip Address of the machine you are connecting from
IP_LIST = []
Hostnames_List = []
connection_error = []
authentication_error = []
collection_of_results = []
index = 2
ThreadLock = Lock()
timeout = 15

root = Tk()
my_gui = MyGui.MyGUIClass(root)
root.mainloop()

SiteName = my_gui.SiteName_var.get()
Debugging = my_gui.Debugging_var.get()
jump_server = my_gui.JumpServer_var.get()
username = my_gui.Username_var.get()
password = my_gui.password_var.get()
IPAddr1 = my_gui.IP_Address1_var.get()
IPAddr2 = my_gui.IP_Address2_var.get()
FolderPath = my_gui.FolderPath_var.get()
if my_gui.JumpServer_var.get() == "AR31NOC":
    jump_server = "10.251.6.31"
if my_gui.JumpServer_var.get() == "MMFTH1V-MGMTS02":
    jump_server = "10.251.131.6"
if my_gui.JumpServer_var.get() == "None":
    jump_server = "None"


# -----------------------------------------------------------
# --------------- Logging Configuration Start ---------------

# Log file location
logfile = f'{FolderPath}\\debug.log'

# Define the log format
log_format = (
    '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')

# Define basic configuration
if Debugging == "Off":
    logging.basicConfig(
        # Define logging level
        level=logging.WARN,
        # Declare the object we created to format the log messages
        format=log_format,
        # Declare handlers
        handlers=[
            logging.FileHandler(logfile),
            logging.StreamHandler(sys.stdout),
        ]
    )
elif my_gui.Debugging == "On":
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

# --------------- Logging Configuration End ---------------
# ---------------------------------------------------------


# Checks that the IP address is valid.
# Returns True or false.
def ip_check(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


# Connects to the IP address through a jump host using SSH.
# Returns the SSH session.
def jump_session(ip):
    if not ip_check(ip):
        with ThreadLock:
            log.error(f"open_session function error: "
                      f"ip Address {ip} is not a valid Address. Please check and restart the script!",)
        return None, None, False
    try:
        with ThreadLock:
            log.info(f"Trying to establish a connection to: {ip}")
        jump_box = paramiko.SSHClient()
        jump_box.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jump_box.connect(jump_server, username=username, password=password)
        jump_box_transport = jump_box.get_transport()
        src_address = (local_IP_address, 22)
        destination_address = (ip, 22)
        jump_box_channel = jump_box_transport.open_channel("direct-tcpip", destination_address, src_address,
                                                           timeout=timeout,)
        target = paramiko.SSHClient()
        target.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        target.connect(destination_address, username=username, password=password, sock=jump_box_channel,
                       timeout=timeout, auth_timeout=timeout, banner_timeout=timeout)
        with ThreadLock:
            log.info(f"Jump Session Function Error: Connection to IP: {ip} established")
        return target, jump_box, True
    except paramiko.ssh_exception.AuthenticationException:
        with ThreadLock:
            authentication_error.append(ip)
            log.error(f"Jump Session Function Error: Authentication to IP: {ip} failed!" 
                      f"Please check your ip, username and password.")
        return None, None, False
    except paramiko.ssh_exception.NoValidConnectionsError:
        with ThreadLock:
            connection_error.append(ip)
            log.error(f"Jump Session Function Error: Unable to connect to IP: {ip}!")
        return None, None, False
    except (ConnectionError, TimeoutError):
        with ThreadLock:
            connection_error.append(ip)
            log.error(f"Jump Session Function Error: Connection or Timeout error occurred for IP: {ip}!")
        return None, None, False
    except Exception as err:
        with ThreadLock:
            log.error(f"Jump Session Function Error: An unknown error occurred for IP: {ip}!")
            log.error(f"{err}")
        return None, None, False


def open_session(ip):
    if not ip_check(ip):
        return None, False
    try:
        log.info(f"Open Session Function: Trying to connect to ip Address: {ip}")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, port=22, username=username, password=password)
        log.info(f"Open Session Function: Connected to ip Address: {ip}")
        return ssh, True
    except paramiko.ssh_exception.AuthenticationException:
        log.error(f"Open Session Function:"
                  f"Authentication to ip Address: {ip} failed! Please check your ip, username and password.")
        return None, False
    except paramiko.ssh_exception.NoValidConnectionsError:
        log.error(f"Open Session Function Error: Unable to connect to ip Address: {ip}!")
        return None, False
    except (ConnectionError, TimeoutError):
        log.error(f"Open Session Function Error: Timeout error occurred for ip Address: {ip}!")
        return None, False
    except Exception as err:
        log.error(f"Open Session Function Error: Unknown error occurred for ip Address: {ip}!")
        log.error(f"\t Error: {err}")
        return None, False


# Connects to the host's IP Address and runs the 'show cdp neighbors detail'
# command and parses the output using TextFSM and saves it to a list of dicts.
# Returns None.
def get_cdp_details(ip):
    jump_box = None
    if jump_server == "None":
        ssh, connection = open_session(ip)
    else:
        ssh, jump_box, connection = jump_session(ip)
    if not connection:
        return None
    hostname = get_hostname(ip)
    if hostname not in Hostnames_List:
        Hostnames_List.append(hostname)
        _, stdout, _ = ssh.exec_command("show cdp neighbors detail")
        stdout = stdout.read()
        stdout = stdout.decode("utf-8")
        with ThreadLock:
            with open("textfsm/cisco_ios_show_cdp_neighbors_detail.textfsm") as f:
                re_table = textfsm.TextFSM(f)
                result = re_table.ParseText(stdout)
        result = [dict(zip(re_table.header, entry)) for entry in result]
        for entry in result:
            entry['LOCAL_HOST'] = hostname.upper()
            entry['LOCAL_IP'] = ip
            text = entry['DESTINATION_HOST']
            head, sep, tail = text.partition('.')
            entry['DESTINATION_HOST'] = head.upper()
            collection_of_results.append(entry)
            if entry["MANAGEMENT_IP"] not in IP_LIST:
                if 'Switch' in entry['CAPABILITIES'] and "Host" not in entry['CAPABILITIES']:
                    IP_LIST.append(entry["MANAGEMENT_IP"])
    ssh.close()
    if jump_box:
        jump_box.close()


# Connects to the host's IP Address and runs the 'show run | inc hostname'
# command and parses the output using TextFSM and saves as a string.
# Returns the string.
def get_hostname(ip):
    jump_box = None
    if jump_server == "None":
        ssh, connection = open_session(ip)
    else:
        ssh, jump_box, connection = jump_session(ip)
    if not connection:
        return None
    _, stdout, _ = ssh.exec_command("show run | inc hostname")
    stdout = stdout.read()
    stdout = stdout.decode("utf-8")
    try:
        with ThreadLock:
            with open("textfsm/hostname.textfsm") as f:
                re_table = textfsm.TextFSM(f)
                result = re_table.ParseText(stdout)
                hostname = result[0][0]
    except:
        hostname = "Not Found"
    ssh.close()
    if jump_box:
        jump_box.close()
    return hostname


def main():
    global FolderPath
    # Start timer.
    start = time.perf_counter()
    # Define amount of threads.
    thread_count = 10
    pool = ThreadPool(thread_count)

    # Added IP Addresses to the list if they exist, if not log an error.
    IP_LIST.append(IPAddr1) if ip_check(IPAddr1) else log.error(
        f"{IPAddr1}\nNo valid IP Address was found. Please check and try again")
    IP_LIST.append(IPAddr2) if ip_check(IPAddr2) else log.info(
        f"{IPAddr2}\nNo valid IP Address was found.")

    # Start the CDP recursive lookup on the network and save the results.
    i = 0
    while i < len(IP_LIST):
        limit = i + min(thread_count, (len(IP_LIST) - i))
        ip_addresses = IP_LIST[i:limit]

        pool.map(get_cdp_details, ip_addresses)

        i = limit

    # Close off and join the pools together.
    pool.close()
    pool.join()

    array = pd.DataFrame(collection_of_results, columns=["LOCAL_HOST",
                                                         "LOCAL_IP",
                                                         "LOCAL_PORT",
                                                         "DESTINATION_HOST",
                                                         "REMOTE_PORT",
                                                         "MANAGEMENT_IP",
                                                         "PLATFORM",
                                                         "SOFTWARE_VERSION",
                                                         "CAPABILITIES"
                                                         ])

    filepath = f"{FolderPath}\\{SiteName}_CDP Switch Audit.xlsx"

    array.to_excel(filepath, index=False)
    workbook = load_workbook(filename=filepath)
    ws = workbook["Sheet1"]
    ws.auto_filter.ref = ws.dimensions
    ws.column_dimensions['A'].width = "30"
    ws.column_dimensions['B'].width = "30"
    ws.column_dimensions['C'].width = "30"
    ws.column_dimensions['D'].width = "30"
    ws.column_dimensions['E'].width = "30"
    ws.column_dimensions['F'].width = "30"
    ws.column_dimensions['G'].width = "50"
    ws.column_dimensions['H'].width = "120"
    ws.column_dimensions['I'].width = "30"
    workbook.save(filename=filepath)

    ctypes.windll.user32.MessageBoxW(0, f"Script Complete\n\nFile saved in:\n{filepath}", "Info", 0x40000)

    # End timer.
    end = time.perf_counter()
    log.info(f"Script finished in {end - start:0.4f} seconds")


if __name__ == "__main__":
    main()
