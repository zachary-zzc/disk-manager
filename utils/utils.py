import sys
import os
import pwd
import time
# import psutil as ps
# import pyudev
import smtplib
import configparser
from pyudev.core import Device

# from singleton import Singleton

# _DEFAULT_USER = "zzc"
# _DEFAULT_PASSWORD = "zhao900420"
# _TEMP_MOUNT_DIR = "/mnt/temp"
#
_admin_email = "shinaider.zhao@gmail.com"
_login = "shinaider.zhao@gmail.com"
_password = "3XkfqFE<"
#
# _MONITOR_ROUND = 30 # check usb ports every 30 minutes
# _SCAN_ROUND = 7 # scan disk usage and first lvl directories every 7 days
# _BACKUP_ROUND = 30 # backup disk every 30 days

def _get_time():
    return time.asctime( time.localtime(time.time()) )

def _format_db_str(l):
    return map(lambda x: "'" + str(x) + "'", l)


def send_email(from_addr, to_addr_list, cc_addr_list,
        subject, message,
        login, password,
        smtpserver='smtp.gmail.com:587'):
    header = 'From: %s' % from_addr
    header += 'To: %s' % ','.join(to_addr_list)
    header += 'Cc: %s' % ','.join(cc_addr_list)
    header += 'Subject: %s' % subject

    message = header + message
    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login, password)
    problems = server.sendmail(from_addr, to_addr_list, message)
    server.quit()

def admin_email(subject, message, to_addr_list, cc_addr_list=[]):
    send_email(_admin_email, to_addr_list, cc_addr_list,
            subject, message, _login, _password)

def system_call(cmdline, user, with_root=True):
    """
    system call
    return:
        STDOUT
    """
    if user.tp is 0:
        return os.popen(cmdline).readlines()
    else:
        if with_root:
            # if temp file exist, delete it first
            if os.path.isfile(".temp"): os.remove(".temp")
            # first touch
            os.popen("sudo -S sleep 0.01", "w").write(user.passwd)
            # write stdout to temp file
            os.popen("sudo -S " + cmdline + " > .temp", 'w').write(user.passwd)
            with open(".temp", "r") as ifs:
                stdout = ifs.readlines()
            # delete temp file
            os.remove(".temp")
            return stdout
        else:
            return os.popen(cmdline).readlines()

def read_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def scan(label, user):
    """
    system call: du --max-depth=1 -dh /mnt/{label}
    """
    pass
