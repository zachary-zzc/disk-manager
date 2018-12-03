import os
import sys
import time
import copy
import pwd
import threading
import configparser
import json
from datetime import datetime
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
    def __init__(self):
        pass

    def setup(self, config_ini):
        config = configparser.ConfigParser()
        config.read(config_ini)
        self.__dict__.update(config)

scan_queue = []
backup_queue = []

user = User()
database = db.Database()
panel = Panel()
panel.setup(_CONFIG_FILE)

def update_database(database, curr_partitions, prev_partitions, user, panel):
    # scan database, disks without principles (prows), disks without default position (drows)
    # and disk that donot have backup (brows)
    prows, drows, brows = database.scan()

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
        label = port.get_label_from_partition(partition, panel)
<<<<<<< HEAD
        print label, usage, partition.mountpoint
        if db.check_disk_in_table(label):
=======
        disk = database.get_disk_by_label(label)
        print disk
        print label, usage, partition.mountpoint
        if database.check_disk_in_table(label):
>>>>>>> ec1223cf1ef3cb3314b95c2ff89175e71ea7d8de
            # generaral function
            database.change_disk_property(label, "CURRENT_POS", panel.SERVER["server"])
            database.change_disk_property(label, "STATUS", 1)
            database.change_disk_property(label, "USED", usage.used)
            database.change_disk_property(label, "TOTAL", usage.total)
            database.change_disk_property(label, "FREE", usage.free)
            database.change_disk_property(label, "PERCENT", usage.percent)
            database.change_disk_property(label, "MOUNT_PATH", partition.mountpoint)
            # # set last mount time
            if disk.status is 0: # this has just been mounted
                database.change_disk_property(label, "LAST_MOUNT_TIME", datetime.now())
        else:
            # add disk to table
            disk = Disk(label, current_pos=panel.SERVER["server"], status=1,
                        used=usage.used, total=usage.total,
                        last_mount_time=datetime.now())
            database.add_disk(disk)
    # del partitions from server
    for partition in del_partitions:
        label = port.get_label_from_partition(partition, panel)
        disk = database.get_disk_by_label(label)
        # general function
        database.change_disk_property(label, "CURRENT_POS", disk.default_pos)
        database.change_disk_property(label, "STATUS", 0)
        # # set last umount time
        database.change_disk_property(label, "LAST_UMOUNT_TIME", datetime.now())
    # remain partitions
    for partition in rem_partitions:
        usage = port.get_usage_from_partition(partition, user, panel)
        label = port.get_label_from_partition(partition, panel)
        # general function
        database.change_disk_property(label, "USED", usage.used)
        database.change_disk_property(label, "TOTAL", usage.total)
        database.change_disk_property(label, "FREE", usage.free)
        database.change_disk_property(label, "PERCENT", usage.percent)


class ScanThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global scan_queue
        global user, database, panel

        while True:
            while scan_queue:
                disk = scan_queue[0]
                print "start to scan {}".format(disk.label)
                hierarchy = scan.scan(disk, user, panel)
                # update database
                database.change_disk_property(disk.label, "LAST_SCAN_TIME", datetime.now())
                database.change_disk_property(disk.label, "hierarchy", json.dumps(hierarchy))
                print "finish scan {}, database updated".format(disk.label)
                scan_queue.pop()
            time.sleep(int(panel.LISTEN["round"]) * 60)

class Monitor():
    def __init__(self):
        self._prev_partitions = []
        self._curr_partitions = []
        self._log = log.Logging(panel.LOG["log"], panel.LOG["err"])

    def start(self):
        global scan_queue, backup_queue
        global user, database, panel

        print "monitor is ready"
        self._log.write("Monitor is ready")
        while True:
            self._log.write("========================================================================")
            self._log.write("mount all the disks")
            # start check current disks, update database
            port.delta_check_all(user, panel)
            port.delta_mount_all(user, panel)
            self._curr_partitions = port.list_mounted(panel)
            self._log.write("update database")
            update_database(database, self._curr_partitions, self._prev_partitions, user, panel)
            self._prev_partitions = copy.deepcopy(self._curr_partitions)
            # check current disks, scan if necessary, open a thread for each disk
            for partition in self._curr_partitions:
                label = port.get_label_from_partition(partition, panel)
                disk = database.get_disk_by_label(label)
                if scan.require_scan(disk, user, panel) and disk not in scan_queue:
                    print "add {} to scan queue".format(disk.label)
                    print "current scan queue: {}".format(", ".join([d.label for d in scan_queue]))
                    scan_queue.append(disk)
                # if backup.require_backup(disk, user, panel) and disk not in backup_queue:
                #     backup_queue.append(disk)
            self._log.write("done")
            self._log.write("========================================================================")
            time.sleep(int(panel.LISTEN["round"]) * 60)

class MonitorThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._prev_partitions = []
        self._curr_partitions = []
        self._log = log.Logging(panel.LOG["log"], panel.LOG["err"])

    def run(self):
        print "monitor is ready"
        self._log.write("Monitor is ready")
        while True:
            self._log.write("========================================================================")
            self._log.write("mount all the disks")
            port.delta_mount_all(user, panel)
            self._curr_partitions = port.list_mounted(panel)
            self._log.write("update database")
            update_database(database, self._curr_partitions, self._prev_partitions, user, panel)
            self._prev_partitions = copy.deepcopy(self._curr_partitions)
            self._log.write("done")
            self._log.write("========================================================================")

            time.sleep(1800)

def main():
    tm = Monitor()
    # t = MonitorThread()
    tm.start()
    time.sleep(60)
    ts = ScanThread()
    ts.start()

if __name__ == '__main__':
    main()
