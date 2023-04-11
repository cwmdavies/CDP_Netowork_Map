"""
Author Details:
Name: Chris Davies
Email: chris.davies@weavermanor.co.uk
App Version: 2.0
Tested on Python 3.11
This script takes in up to two IP Addresses, preferably the core switches, runs the "Show CDP Neighbors Detail"
command and saves the information to a list of dictionaries. Each dictionary is then parsed for the neighbouring
IP Address for each CDP neighbour and saved to a separate list. Another list is used to store the IP Addresses
of those that have been processed so no switch is connected too more than once. A connection is made to each IP Address
in the list , using threading, to retrieve the same information. This recursion goes on until there are no
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
import multiprocessing
from tkinter import Tk
import ctypes
import pandas
import openpyxl
import socket
import os
import datetime
import shutil

EXCEL_TEMPLATE = "1 - CDP Switch Audit _ Template.xlsx"
LOCAL_IP_ADDRESS = '127.0.0.1'  # ip Address of the machine you are connecting from
IP_LIST = []
HOSTNAMES = []
DNS_IP = {}
CONNECTION_ERRORS = []
AUTHENTICATION_ERRORS = []
COLLECTION_OF_RESULTS = []
INDEX = 2
THREADLOCK = multiprocessing.Lock()
TIMEOUT = 15
DATE_TIME_NOW = datetime.datetime.now()
DATE_NOW = DATE_TIME_NOW.strftime("%d %B %Y")
TIME_NOW = DATE_TIME_NOW.strftime("%H:%M")

root = Tk()
my_gui = MyGui.MyGUIClass(root)
root.mainloop()


SiteName = my_gui.SiteName_var.get()
Debugging = my_gui.Debugging_var.get()
jump_server = my_gui.JumpServer_var.get()
_USERNAME = my_gui.Username_var.get()
_PASSWORD = my_gui.password_var.get()
A_USERNAME = "answer"
A_PASSWORD = my_gui.answer_password_var.get()
ANSWER_REDO = my_gui.answer_redo_var.get()
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


# --------------- Logging Configuration End ---------------
# ---------------------------------------------------------


def ip_check(ip) -> bool:
    """
    Takes in an IP Address as a string.
    Checks that the IP address is a valid one.
    Returns True or false.
    :param ip: Example: 192.168.1.1
    :return: Boolean
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        with THREADLOCK:
            log.error(f"ip_check function ValueError: "
                      f"IP Address: {ip} is an invalid address. Please check and try again!")
        return False


def dns_resolve(domain_name) -> None:
    """
    Takes in a domain name and does a DNS lookup on it.
    Saves the information to a dictionary
    :param domain_name: Domain name. Example: google.com
    :return: None. Saves IP Address and domain name to a dictionary. Example: {"google.com": "142.250.200.14"}
    """
    try:
        with THREADLOCK:
            log.info(f"Attempting to retrieve DNS 'A' record for hostname: {domain_name}")
        addr1 = socket.gethostbyname(domain_name)
        DNS_IP[domain_name] = addr1
        with THREADLOCK:
            log.info(f"Successfully retrieved DNS 'A' record for hostname: {domain_name}")
    except socket.gaierror:
        with THREADLOCK:
            log.error(f"Failed to retrieve DNS A record for hostname: {domain_name}")
        DNS_IP[domain_name] = "DNS Resolution Failed"


def jump_session(ip, username=_USERNAME, password=_PASSWORD) -> "SSH Session + Jump Session + Connection Status":
    """
    Takes in an IP Address as a string.
    Connects to the IP address through a jump host using SSH.
    Returns the SSH session, The jump Session and
    a boolean value that represents the state of the connection.
    :param username:
    :param password:
    :param ip: The IP Address you wish to connect to.
    :return: SSH Session + Jump Session + Connection Status(Boolean).
    """
    if not ip_check(ip):
        with THREADLOCK:
            log.error(f"open_session function error: "
                      f"ip Address {ip} is not a valid Address. Please check and restart the script!", )
        return None, None, False
    try:
        with THREADLOCK:
            log.info(f"Jump Session Function: Trying to establish a connection to: {ip}")
        jump_box = paramiko.SSHClient()
        jump_box.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jump_box.connect(jump_server, username=_USERNAME, password=_PASSWORD)
        jump_box_transport = jump_box.get_transport()
        src_address = (LOCAL_IP_ADDRESS, 22)
        destination_address = (ip, 22)
        jump_box_channel = jump_box_transport.open_channel("direct-tcpip", destination_address, src_address,
                                                           timeout=TIMEOUT, )
        target = paramiko.SSHClient()
        target.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        target.connect(hostname=ip, username=username, password=password,
                       sock=jump_box_channel, timeout=TIMEOUT, auth_timeout=TIMEOUT, banner_timeout=TIMEOUT)
        with THREADLOCK:
            log.info(f"Jump Session Function: Connection to IP: {ip} established")
        return target, jump_box, True
    except paramiko.ssh_exception.AuthenticationException:
        if ANSWER_REDO == "Yes":
            if ip not in AUTHENTICATION_ERRORS:
                AUTHENTICATION_ERRORS.append(ip)
                with THREADLOCK:
                    log.error(f"Jump Session Function Error: Authentication to IP: {ip} failed! "
                              f"Retrying using 'answer' credentials.")
                jump_session(ip, A_USERNAME, A_PASSWORD)
            elif ip in AUTHENTICATION_ERRORS:
                with THREADLOCK:
                    log.error(f"Jump Session Function Error: Authentication to IP: {ip} failed! "
                              f"Please check your ip, username and password.")
                return None, None, False
        else:
            AUTHENTICATION_ERRORS.append(ip)
            with THREADLOCK:
                log.error(f"Jump Session Function Error: Authentication to IP: {ip} failed! "
                          f"Please check your ip, username and password.")
            return None, None, False
    except paramiko.ssh_exception.NoValidConnectionsError:
        CONNECTION_ERRORS.append(ip)
        with THREADLOCK:
            log.error(f"Jump Session Function Error: Unable to connect to IP: {ip}!")
        return None, None, False
    except (ConnectionError, TimeoutError):
        CONNECTION_ERRORS.append(ip)
        with THREADLOCK:
            log.error(f"Jump Session Function Error: Connection or Timeout error occurred for IP: {ip}!")
        return None, None, False
    except Exception as err:
        CONNECTION_ERRORS.append(ip)
        with THREADLOCK:
            log.error(f"Jump Session Function Error: An unknown error occurred for IP: {ip}!\n{err}")
        return None, None, False


def direct_session(ip) -> "SSH Session + Connection Status":
    """
    Takes in an IP Address as a string.
    Connects to the IP address directly using SSH.
    Returns the SSH session and
    a boolean value that represents the state of the connection.
    :param ip: The IP Address you wish to connect to.
    :return: SSH Session + Jump Session + Connection Status(Boolean).
    """
    if not ip_check(ip):
        return None, False
    try:
        with THREADLOCK:
            log.info(f"Open Session Function: Trying to connect to ip Address: {ip}")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, port=22, username=_USERNAME, password=_PASSWORD)
        with THREADLOCK:
            log.info(f"Open Session Function: Connected to ip Address: {ip}")
        return ssh, True
    except paramiko.ssh_exception.AuthenticationException:
        AUTHENTICATION_ERRORS.append(ip)
        with THREADLOCK:
            log.error(f"Open Session Function: "
                      f"Authentication to ip Address: {ip} failed! Please check your ip, username and password.")
        return None, False
    except paramiko.ssh_exception.NoValidConnectionsError:
        CONNECTION_ERRORS.append(ip)
        with THREADLOCK:
            log.error(f"Open Session Function Error: Unable to connect to ip Address: {ip}!")
        return None, False
    except (ConnectionError, TimeoutError):
        CONNECTION_ERRORS.append(ip)
        with THREADLOCK:
            log.error(f"Open Session Function Error: Timeout error occurred for ip Address: {ip}!")
        return None, False
    except Exception as err:
        CONNECTION_ERRORS.append(ip)
        with THREADLOCK:
            log.error(f"Open Session Function Error: Unknown error occurred for ip Address: {ip}!\n{err}")
        return None, False


def get_cdp_details(ip) -> "None, appends dictionaries to a global list":
    """
    Takes in an IP Address as a string.
    Connects to the host's IP Address and runs the 'show cdp neighbors detail'
    command and parses the output using TextFSM and saves it to a list of dicts.
    Returns None.
    :param ip: The IP Address you wish to connect to.
    :return: None, appends dictionaries to a global list.
    """
    jump_box = None
    if jump_server == "None":
        ssh, connection = direct_session(ip)
    else:
        ssh, jump_box, connection = jump_session(ip)
    if not connection:
        return None
    hostname = get_hostname(ip)
    if hostname not in HOSTNAMES:
        HOSTNAMES.append(hostname)
        with THREADLOCK:
            log.info(f"Attempting to retrieve CDP Details for IP: {ip}")
        _, stdout, _ = ssh.exec_command("show cdp neighbors detail")
        stdout = stdout.read()
        stdout = stdout.decode("utf-8")
        with THREADLOCK:
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
            COLLECTION_OF_RESULTS.append(entry)
            if entry["MANAGEMENT_IP"] not in IP_LIST:
                if 'Switch' in entry['CAPABILITIES'] and "Host" not in entry['CAPABILITIES']:
                    IP_LIST.append(entry["MANAGEMENT_IP"])
    with THREADLOCK:
        log.info(f"Successfully retrieved CDP Details for IP: {ip}")
    ssh.close()
    if jump_box:
        jump_box.close()


def get_hostname(ip) -> "Hostname as a string":
    """
    Connects to the host's IP Address and runs the 'show run | inc hostname'
    command and parses the output using TextFSM and saves it as a string.
    Returns the hostname as a string.
    :param ip: The IP Address you wish to connect to.
    :return: Hostname(str).
    """
    jump_box = None
    if jump_server == "None":
        ssh, connection = direct_session(ip)
    else:
        ssh, jump_box, connection = jump_session(ip)
    if not connection:
        return None
    with THREADLOCK:
        log.info(f"Attempting to retrieve hostname for IP: {ip}")
    _, stdout, _ = ssh.exec_command("show run | inc hostname")
    stdout = stdout.read()
    stdout = stdout.decode("utf-8")
    try:
        with THREADLOCK:
            with open("textfsm/hostname.textfsm") as f:
                re_table = textfsm.TextFSM(f)
                result = re_table.ParseText(stdout)
                hostname = result[0][0]
                log.info(f"Successfully retrieved hostname for IP: {ip}")
    except Exception as Err:
        with THREADLOCK:
            log.error(Err)
        hostname = "Not Found"
    ssh.close()
    if jump_box:
        jump_box.close()
    return hostname


def main():
    global FolderPath
    # Start timer.
    start = time.perf_counter()

    # Added IP Addresses to the list if they exist, if not log an error.
    IP_LIST.append(IPAddr1) if ip_check(IPAddr1) else log.error(
        f"{IPAddr1}\nNo valid IP Address was found. Please check and try again")
    IP_LIST.append(IPAddr2) if ip_check(IPAddr2) else log.info(
        f"{IPAddr2}\nNo valid IP Address was found.")

    # Start the CDP recursive lookup on the network and save the results.
    thread_count = os.cpu_count()
    with ThreadPool(thread_count) as pool:
        i = 0
        while i < len(IP_LIST):
            limit = i + min(thread_count, (len(IP_LIST) - i))
            ip_addresses = IP_LIST[i:limit]

            pool.map(get_cdp_details, ip_addresses)

            i = limit
        # Close off and join the pools together.
        pool.close()
        pool.join()

    with ThreadPool(thread_count) as pool2:
        pool2.map(dns_resolve, HOSTNAMES)
        pool2.close()
        pool2.join()

    audit_array = pandas.DataFrame(COLLECTION_OF_RESULTS, columns=["LOCAL_HOST",
                                                                   "LOCAL_IP",
                                                                   "LOCAL_PORT",
                                                                   "DESTINATION_HOST",
                                                                   "REMOTE_PORT",
                                                                   "MANAGEMENT_IP",
                                                                   "PLATFORM",
                                                                   "SOFTWARE_VERSION",
                                                                   "CAPABILITIES"
                                                                   ])
    conn_array = pandas.DataFrame(CONNECTION_ERRORS, columns=["Connection Errors"])
    auth_array = pandas.DataFrame(AUTHENTICATION_ERRORS, columns=["Authentication Errors"])
    dns_array = pandas.DataFrame(DNS_IP.items(), columns=["Hostname", "IP Address"])

    filepath = f"{FolderPath}\\{SiteName}_CDP Switch Audit.xlsx"
    excel_template = f"{os.getcwd()}\\1 - CDP Switch Audit _ Template.xlsx"
    shutil.copy2(src=excel_template, dst=filepath)

    wb = openpyxl.load_workbook(filepath)
    ws1 = wb["Audit"]
    ws1["B4"] = SiteName
    ws1["B5"] = DATE_NOW
    ws1["B6"] = TIME_NOW
    ws1["B7"] = IPAddr1
    ws1["B8"] = IPAddr2
    wb.save(filepath)
    wb.close()

    writer = pandas.ExcelWriter(filepath, engine='openpyxl', if_sheet_exists="overlay", mode="a")
    audit_array.to_excel(writer, index=False, sheet_name="Audit", header=False, startrow=11)
    dns_array.to_excel(writer, index=False, sheet_name="DNS Resolved", header=False, startrow=4)
    conn_array.to_excel(writer, index=False, sheet_name="Connection Errors", header=False, startrow=4)
    auth_array.to_excel(writer, index=False, sheet_name="Authentication Errors", header=False, startrow=4)

    writer.close()

    ctypes.windll.user32.MessageBoxW(0, f"Script Complete\n\n"
                                        f"File saved in:\n"
                                        f"{filepath}", "Info", 0x40000)

    # End timer.
    end = time.perf_counter()
    log.info(f"Script finished in {end - start:0.4f} seconds")


if __name__ == "__main__":
    main()
