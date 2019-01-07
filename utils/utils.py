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
_admin_email = u"shinaider.zhao@gmail.com"
_login = u"shinaider.zhao@gmail.com"
_password = u"3XkfqFE<"

#
# _MONITOR_ROUND = 30 # check usb ports every 30 minutes
# _SCAN_ROUND = 7 # scan disk usage and first lvl directories every 7 days
# _BACKUP_ROUND = 30 # backup disk every 30 days

def get_time():
    return time.asctime( time.localtime(time.time()) )

def db_str(s):
    return "'" + str(s) + "'"

def format_db_str(l):
    return map(lambda x: db_str(x), l)

def send_email(from_addr, to_addr_list, cc_addr_list,
        subject, message,
        login, password):
    header = 'From: %s\n' % from_addr
    header += 'To: %s\n' % ','.join(to_addr_list)
    header += 'Cc: %s\n' % ','.join(cc_addr_list)
    header += 'Subject: %s\n' % subject

    message = header + message
    server = smtplib.SMTP('smtp.gmail.com', 587)
    # server = smtplib.SMTP_SSL('smtp.googlemail.com', 465)
    server.ehlo()
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

def size_human_fmt(num, suffix=""):
    for unit in ["B", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%3.1f%s%s" % (num, "Y", suffix)

def parse_ignore(fname):
    import re
    ret = {}
    with open(fname) as ifs:
        header = 'all'
        for line in ifs:
            line = line.strip("\n")
            if line.strip() is "": # space lines
                continue
            if re.match(r"^#", line): # command lines
                continue
            if re.match(r"^>", line): # header line
                header = line[1:].strip()
                ret[header] = []
                continue
            if header in ret:
                ret[header].append(line.strip())
            else:
                ret[header] = [line.strip()]
    return ret

def check_ignore(value, patterns):
    import re
    reg_lst = []
    for regex in patterns:
        reg_lst.append(re.compile(regex.replace("*", ".[a-zA-z\s]*"))) # python 2.7.5 regex issue
    return any(compiled_reg.match(value) for compiled_reg in reg_lst)
