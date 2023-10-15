"""
Author Details:
Name: Chris Davies
Email: chris.davies@weavermanor.co.uk
Tested on Python 3.10

This script takes in up to two IP Addresses, preferably the core switches, runs the "Show CDP Neighbors Detail"
command and saves the information to a list of dictionaries. Each dictionary is then parsed for the neighbouring
IP Address for each CDP neighbour and saved to a separate list. Another list is used to store the IP Addresses
of those that have been processed so no switch is connected too more than once. A connection is made to each IP Address
in the list , using threading, to retrieve the same information. This recursion goes on until there are no
more IP Addresses to connect to. The information is then converted to a numpy array and saved to an Excel spreadsheet.
The script uses threading to connect to multiple switches at a time.
Each IP Address is checked to ensure each IP Address is valid.
"""
import MyPackage.MyGui as MyGui
from MyPackage import config_params
import paramiko
import textfsm
import ipaddress
import time
import multiprocessing
import multiprocessing.pool
import ctypes
import pandas
import openpyxl
import socket
import os
from os.path import exists
import datetime
import shutil
import logging.config

EXCEL_TEMPLATE = "1 - CDP Network Audit _ Template.xlsx"
LOCAL_IP_ADDRESS = '127.0.0.1'  # ip Address of the machine you are connecting from
IP_LIST = []
HOSTNAMES = []
DNS_IP = {}
CONNECTION_ERRORS = []
AUTHENTICATION_ERRORS = []
COLLECTION_OF_RESULTS = []
THREADLOCK = multiprocessing.Lock()
TIMEOUT = int(config_params.Settings["TIMEOUT"])
DATE_TIME_NOW = datetime.datetime.now()
DATE_NOW = DATE_TIME_NOW.strftime("%d %B %Y")
TIME_NOW = DATE_TIME_NOW.strftime("%H:%M")

MyGui.root.mainloop()

SiteName = MyGui.my_gui.SiteName_var.get()
jump_server = MyGui.my_gui.JumpServer_var.get()
_USERNAME = MyGui.my_gui.Username_var.get()
_PASSWORD = MyGui.my_gui.password_var.get()
_ALT_USER = config_params.Alternative_Credentials["username"]
_ALT_PASSWORD = MyGui.my_gui.alt_password_var.get()
IPAddr1 = MyGui.my_gui.IP_Address1_var.get()
IPAddr2 = MyGui.my_gui.IP_Address2_var.get() if MyGui.my_gui.IP_Address2_var.get() else None
retry = MyGui.my_gui.Retry_Auth_var.get()

FolderPath = MyGui.my_gui.FolderPath_var.get()

JUMP_SERVER_KEYS = list(config_params.Jump_Servers.keys())
JUMP_SERVER_DICT = dict(config_params.Jump_Servers)
if MyGui.my_gui.JumpServer_var.get() == JUMP_SERVER_KEYS[0].upper():
    jump_server = JUMP_SERVER_DICT[JUMP_SERVER_KEYS[0]]
if MyGui.my_gui.JumpServer_var.get() == JUMP_SERVER_KEYS[1].upper():
    jump_server = JUMP_SERVER_DICT[JUMP_SERVER_KEYS[1]]
if MyGui.my_gui.JumpServer_var.get() == "None":
    jump_server = "None"

logging.config.fileConfig(fname='config_files/logging_configuration.conf',
                          disable_existing_loggers=False,
                          )
logging.getLogger("paramiko").setLevel(logging.ERROR)
log = logging.getLogger(__name__)


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
        log.error(
            f"ip_check function ValueError: IP Address: {ip} is an invalid address. Please check and try again!",
            exc_info=True)
        return False
    except Exception as Err:
        log.error(f"An error occurred: {Err}",)
        return False


def resolve_dns(domain_name) -> None:
    """
    Takes in a domain name and does a DNS lookup on it.
    Saves the information to a dictionary
    :param domain_name: Domain name. Example: google.com
    :return: None. Saves IP Address and domain name to a dictionary. Example: {"google.com": "142.250.200.14"}
    """
    try:
        log.info(f"Attempting to retrieve DNS 'A' record for hostname: {domain_name}")
        addr1 = socket.gethostbyname(domain_name)
        DNS_IP[domain_name] = addr1
        log.info(f"Successfully retrieved DNS 'A' record for hostname: {domain_name}")
    except socket.gaierror:
        log.error(f"Failed to retrieve DNS A record for hostname: {domain_name}",
                  exc_info=True)
        DNS_IP[domain_name] = "DNS Resolution Failed"
    except Exception as Err:
        log.error(f"An unknown error occurred for hostname: {domain_name}, {Err}",
                  exc_info=True)


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
        log.error(
            f"Jump_session function error: "
            f"ip Address {ip} is not a valid Address. Please check and restart the script!",
            exc_info=True)
        return None, None, False
    try:
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
        target.connect(hostname=ip, username=username, password=password, allow_agent=False,look_for_keys=False,
                       sock=jump_box_channel, timeout=TIMEOUT, auth_timeout=TIMEOUT, banner_timeout=TIMEOUT)
        log.info(f"Jump Session Function: Connection to IP: {ip} established")
        return target, jump_box, True
    except paramiko.ssh_exception.AuthenticationException:
        log.error(f"Jump Session Function Error: Authentication to IP: {ip} failed! ", exc_info=True)
        if retry == "Yes":
            if AUTHENTICATION_ERRORS.count(ip) < 3:
                log.info(f"Retrying connection to '{ip}' using alternative credentials.")
                AUTHENTICATION_ERRORS.append(ip)
                ssh, jump_box, connection = jump_session(ip, username=_ALT_USER, password=_ALT_PASSWORD)
                return ssh, jump_box, connection
            else:
                AUTHENTICATION_ERRORS.append(ip)
                return None, None, False
        else:
            AUTHENTICATION_ERRORS.append(ip)
            return None, None, False
    except paramiko.ssh_exception.NoValidConnectionsError:
        CONNECTION_ERRORS.append(ip)
        log.error(f"Jump Session Function Error: Unable to connect to IP: {ip}!",
                  exc_info=True
                  )
        return None, None, False
    except (ConnectionError, TimeoutError):
        CONNECTION_ERRORS.append(ip)
        log.error(
            f"Jump Session Function Error: Connection or Timeout error occurred for IP: {ip}!",
            exc_info=True
            )
        return None, None, False
    except Exception as err:
        CONNECTION_ERRORS.append(ip)
        log.error(
            f"Jump Session Function Error: An unknown error occurred for IP: {ip}!\n{err}",
            exc_info=True
            )
        return None, None, False


def direct_session(ip, username=_USERNAME, password=_PASSWORD) -> "SSH Session + Connection Status":
    """
    Takes in an IP Address as a string.
    Connects to the IP address directly using SSH.
    Returns the SSH session and
    a boolean value that represents the state of the connection.
    :param username:
    :param password:
    :param ip: The IP Address you wish to connect to.
    :return: SSH Session + Jump Session + Connection Status(Boolean).
    """
    if not ip_check(ip):
        return None, False
    try:
        log.info(f"Open Session Function: Trying to connect to ip Address: {ip}")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip, port=22, username=username, password=password, allow_agent=False,look_for_keys=False)
        log.info(f"Open Session Function: Connected to ip Address: {ip}")
        return ssh, True
    except paramiko.ssh_exception.AuthenticationException:
        if retry == "Yes":
            if AUTHENTICATION_ERRORS.count(ip) < 3:
                log.info(f"Retrying connection to '{ip}' using alternative credentials.")
                AUTHENTICATION_ERRORS.append(ip)
                ssh, jump_box, connection = direct_session(ip, username=_ALT_USER, password=_ALT_PASSWORD)
                return ssh, connection
            else:
                AUTHENTICATION_ERRORS.append(ip)
                return None, False
        else:
            AUTHENTICATION_ERRORS.append(ip)
            return None, False
    except paramiko.ssh_exception.NoValidConnectionsError:
        CONNECTION_ERRORS.append(ip)
        log.error(f"Open Session Function Error: Unable to connect to ip Address: {ip}!",
                  exc_info=True
                  )
        return None, False
    except (ConnectionError, TimeoutError):
        CONNECTION_ERRORS.append(ip)
        log.error(
            f"Open Session Function Error: Timeout error occurred for ip Address: {ip}!",
            exc_info=True
            )
        return None, False
    except Exception as err:
        CONNECTION_ERRORS.append(ip)
        log.error(
            f"Open Session Function Error: Unknown error occurred for ip Address: {ip}!\n{err}",
            exc_info=True
        )
        return None, False


def get_facts(ip) -> "None, appends dictionaries to a global list":
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
    try:
        get_version_output = send_command(ip, "show version")
        get_cdp_nei_output = send_command(ip, "show cdp neighbors detail")
        hostname = get_version_output[0].get("HOSTNAME")
        serial_numbers = get_version_output[0].get("SERIAL")
        uptime = get_version_output[0].get("UPTIME")
        if hostname not in HOSTNAMES:
            HOSTNAMES.append(hostname)
            for entry in get_cdp_nei_output:
                entry["LOCAL_HOST"] = hostname
                entry["LOCAL_IP"] = ip
                entry["LOCAL_SERIAL"] = serial_numbers
                entry["LOCAL_UPTIME"] = uptime
                text = entry['DESTINATION_HOST']
                head, sep, tail = text.partition('.')
                entry['DESTINATION_HOST'] = head.upper()
                COLLECTION_OF_RESULTS.append(entry)
                if entry["MANAGEMENT_IP"] not in IP_LIST:
                    if 'Switch' in entry['CAPABILITIES'] and "Host" not in entry['CAPABILITIES']:
                        IP_LIST.append(entry["MANAGEMENT_IP"])
        ssh.close()
        if jump_box:
            jump_box.close()
    except AttributeError:
        log.error("An Attribute Error occurred.", exc_info=True)
    finally:
        ssh.close()
        if jump_box:
            jump_box.close()


def send_command(ip, command):
    if not exists(f"./textfsm/cisco_ios_{command}.textfsm".replace(" ", "_")):
        log.error(f"The command: '{command}', cannot be found. "
                  "Check the command is correct and make sure the TextFSM file exists for that command.")
        return None
    else:
        jump_box = None
        if jump_server == "None":
            ssh, connection = direct_session(ip)
        else:
            ssh, jump_box, connection = jump_session(ip)
        if not connection:
            return None
        try:
            _, stdout, _ = ssh.exec_command(command)
            stdout = stdout.read()
            stdout = stdout.decode("utf-8")
            with open(f"./textfsm/cisco_ios_{command}.textfsm".replace(" ", "_")) as f:
                re_table = textfsm.TextFSM(f)
                result = re_table.ParseText(stdout)
            results = [dict(zip(re_table.header, entry)) for entry in result]
            ssh.close()
            if jump_box:
                jump_box.close()
            return results
        except Exception as err:
            log.error(f"Send_Command function error: An unknown exception occurred: {err}", exc_info=True)
        finally:
            ssh.close()
            if jump_box:
                jump_box.close()


def run_multi_thread(function, iterable):
    thread_count = os.cpu_count()
    with multiprocessing.pool.ThreadPool(thread_count) as pool:
        i = 0
        while i < len(iterable):
            limit = i + min(thread_count, (len(iterable) - i))
            ip_addresses = iterable[i:limit]
            pool.map(function, ip_addresses)
            i = limit


def main():
    global FolderPath
    global IPAddr1
    global IPAddr2
    global _USERNAME
    global _PASSWORD
    global _ALT_PASSWORD

    # Start timer.
    start = time.perf_counter()

    # Added IP Addresses to the list if they exist, if not log an error.
    IP_LIST.append(IPAddr1) if ip_check(IPAddr1) else log.error(
        f"{IPAddr1}\nNo valid IP Address was found. Please check and try again")
    try:
        if IPAddr2 is not None:
            IP_LIST.append(IPAddr2) if ip_check(IPAddr2)\
                else log.error(f"{IPAddr2}\nThe IP Address: {IPAddr2}, is invalid.")
    except NameError:
        log.info("Second IP Address not defined.")
        IPAddr2 = "Not Specified"

    # Start the CDP recursive lookup on the network and save the results.
    run_multi_thread(get_facts, IP_LIST)

    # Resolve DNS A addresses using hostnames
    run_multi_thread(resolve_dns, HOSTNAMES)

    audit_array = pandas.DataFrame(COLLECTION_OF_RESULTS, columns=["LOCAL_HOST",
                                                                   "LOCAL_IP",
                                                                   "LOCAL_PORT",
                                                                   "LOCAL_SERIAL",
                                                                   "LOCAL_UPTIME",
                                                                   "DESTINATION_HOST",
                                                                   "REMOTE_PORT",
                                                                   "MANAGEMENT_IP",
                                                                   "PLATFORM",
                                                                   "SOFTWARE_VERSION",
                                                                   "CAPABILITIES"
                                                                   ])
    conn_array = pandas.DataFrame(set(CONNECTION_ERRORS), columns=["Connection Errors"])
    auth_array = pandas.DataFrame(set(AUTHENTICATION_ERRORS), columns=["Authentication Errors"])
    dns_array = pandas.DataFrame(DNS_IP.items(), columns=["Hostname", "IP Address"])

    filepath = f"{FolderPath}\\{SiteName}_CDP Switch Audit.xlsx"
    excel_template = f"config_files\\1 - CDP Network Audit _ Template.xlsx"
    shutil.copy2(src=excel_template, dst=filepath)

    wb = openpyxl.load_workbook(filepath)
    ws1 = wb["Audit"]
    ws1["B4"] = SiteName
    ws1["B5"] = DATE_NOW
    ws1["B6"] = TIME_NOW
    ws1["B7"] = IPAddr1
    ws1["B8"] = IPAddr2 if IPAddr2 else "Not Specified"
    wb.save(filepath)
    wb.close()

    writer = pandas.ExcelWriter(filepath, engine='openpyxl', if_sheet_exists="overlay", mode="a")
    audit_array.to_excel(writer, index=False, sheet_name="Audit", header=False, startrow=11)
    dns_array.to_excel(writer, index=False, sheet_name="DNS Resolved", header=False, startrow=4)
    conn_array.to_excel(writer, index=False, sheet_name="Connection Errors", header=False, startrow=4)
    auth_array.to_excel(writer, index=False, sheet_name="Authentication Errors", header=False, startrow=4)

    writer.close()

    ctypes.windll.user32.MessageBoxW(0, f"Script Complete\n\n"
                                        f"File Save Location: {filepath}",
                                     "Info", 0x40000)

    # End timer.
    end = time.perf_counter()
    log.info(f"Script finished in {end - start:0.4f} seconds")


if __name__ == "__main__":
    main()
