import os
import sys
import time
import copy
import pwd
import threading
import configparser
from singleton_decorator import singleton
from utils import utils # utils
from port import port # usb port
from scan import scan # scan first lvl directory
from disk.disk import Disk
from database import database as db
# from exception import * FIXME
from logging import logging as log # FIXME

_CONFIG_FILE = "config.ini"

@singleton
class User:
    def __init__(self):
        self.name = pwd.getpwuid( os.getuid() )[0]
        if self.name == "root":
            self.passwd = ""
            self.tp = 0
        elif self.name == _DEFAULT_USER:
            self.passwd = _DEFAULT_USER
            self.tp = 1
        else:
            self.passwd = raw_input("[sudo] Please enter {}'s password: ".format(
                self.name))
            self._check_pwd_valid()
            self.tp = 2

    def _check_pwd_valid(self):
        pass

@singleton
class Panel:
    def __init__(self, config_ini):
        config = configparser.ConfigParser()
        config.read(config_ini)
        self.__dict__.update(config)

def update_database(db, curr_partitions, prev_partitions, user, panel):
    # scan database
    db.scan()
    # partitions in curr list not in prev list
    add_partitions = [partition for partition in curr_partitions
            if partition not in prev_partitions]
    # partitions in prev list not in curr list
    del_partitions = [partition for partition in prev_partitions
            if partition not in curr_partitions]
    # remain partitions in curr list and prev list, update usage
    rem_partitions = [partition for partition in curr_partitions
            if partition in prev_partitions]
    # add partitions to server
    for partition in add_partitions:
        usage = port.get_usage_from_partition(partition, user, panel)
        # labels = list(db.keys())
        label = port.get_label_from_partition(partition, panel)
        print label, usage
        if db.check_disk_in_table(label):
            # generaral function
            db.change_disk_property(label, "CURRENT_POS", panel.SERVER["server"])
            db.change_disk_property(label, "STATUS", 1)
            db.change_disk_property(label, "USED", usage.used)
            db.change_disk_property(label, "TOTAL", usage.total)
            db.change_disk_property(label, "FREE", usage.free)
            db.change_disk_property(label, "PERCENT", usage.percent)
            db.change_disk_property(label, "MOUNT_PATH", partition.mountpoint)
            # # set last mount time
            # db.change_disk_property(label, "LAST_MOUNT_TIME", utils._get_time())
            db.change_disk_property(label, "UPDATED_AT", utils._get_time())

            # # for zodb
            # db._dbroot[label].current_pos = panel.SERVER["server"]
            # db._dbroot[label].status = 1
            # db._dbroot[label].usage = usage.used
            # db._dbroot[label].space = usage.total
        else:
            # add disk to table
            disk = Disk(label, current_pos=panel.SERVER["server"], status=1,
                        used=usage.used, total=usage.total)
            db.add_disk(disk)
    # del partitions from server
    for partition in del_partitions:
        # labels = list(db.keys())
        label = port.get_label_from_partition(partition, panel)
        disk = db.get_disk_by_label(label)
        # general function
        db.change_disk_property(label, "CURRENT_POS", disk.default_pos)
        db.change_disk_property(label, "STATUS", 0)
        # # set last umount time
        # db.change_disk_property(label, "LAST_UMOUNT_TIME", utils._get_time())
        db.change_disk_property(label, "UPDATED_AT", utils._get_time())
        # # for zodb
        # db._dbroot[label].current_pos = db[label].default_pos
        # db._dbroot[label].status = 0
    # remain partitions
    for partition in rem_partitions:
        usage = port.get_usage_from_partition(partition, user, panel)
        # labels = list(db.keys())
        label = port.get_label_from_partition(partition, panel)
        # general function
        db.change_disk_property(label, "USED", usage.used)
        db.change_disk_property(label, "TOTAL", usage.total)
        db.change_disk_property(label, "FREE", usage.free)
        db.change_disk_property(label, "PERCENT", usage.percent)

        # # for zodb
        # db._dbroot[label].usage = usage.used
        # db._dbroot[label].space = usage.total

class Monitor():
    def __init__(self):
        self._user = User()
        self._prev_partitions = []
        self._curr_partitions = []
        self._db = db.Database()
        self._panel = Panel(_CONFIG_FILE)
        self._log = log.Logging(self._panel.LOG["log"], self._panel.LOG["err"])

    def start(self):
        print "monitor is ready"
        self._log.write("Monitor is ready")
        while True:
            self._log.write("========================================================================")
            self._log.write("mount all the disks")
            port.delta_check_all(self._user, self._panel)
            port.delta_mount_all(self._user, self._panel)
            self._curr_partitions = port.list_mounted(self._panel)
            self._log.write("update database")
            update_database(self._db, self._curr_partitions, self._prev_partitions, self._user, self._panel)
            self._prev_partitions = copy.deepcopy(self._curr_partitions)
            self._log.write("done")
            self._log.write("========================================================================")
            time.sleep(1800)

class MonitorThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._user = User()
        self._prev_partitions = []
        self._curr_partitions = []
        self._db = db.Database()
        self._panel = Panel(_CONFIG_FILE)
        self._log = log.Logging(self._panel.LOG["log"], self._panel.LOG["err"])

    def run(self):
        print "monitor is ready"
        self._log.write("Monitor is ready")
        while True:
            self._log.write("========================================================================")
            self._log.write("mount all the disks")
            port.delta_mount_all(self._user, self._panel)
            self._curr_partitions = port.list_mounted(self._panel)
            self._log.write("update database")
            update_database(self._db, self._curr_partitions, self._prev_partitions, self._user, self._panel)
            self._prev_partitions = copy.deepcopy(self._curr_partitions)
            self._log.write("done")
            self._log.write("========================================================================")

            time.sleep(1800)

def main():
    t = Monitor()
    # t = MonitorThread()
    t.start()

if __name__ == '__main__':
    main()
