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
    prows, drows, brows = database.scan(panel)

    # update disk basic info
    for partition in curr_partitions:
        label = port.get_label_from_partition(partition, panel)
        if database.check_disk_in_table(label, panel):
            disk = database.get_disk_by_label(label, panel)
            if disk.disk_info:
                continue
            disk_info = port.get_device_info(partition.device, user, panel)
            disk.disk_info = disk_info
            database.change_disk_property(label, "DISK_INFO", json.dumps(disk.disk_info), panel)
        else:
            # add disk to table
            disk = Disk(label, current_pos=panel.SERVER["server"], status=1)
            database.add_disk(disk, panel)

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
        disk = database.get_disk_by_label(label, panel)
        print disk
        print label, usage, partition.mountpoint
        # if database.check_disk_in_table(label, panel):
        # generaral function
        database.change_disk_property(label, "CURRENT_POS", panel.SERVER["server"], panel)
        database.change_disk_property(label, "STATUS", 1, panel)
        database.change_disk_property(label, "USED", usage.used, panel)
        database.change_disk_property(label, "TOTAL", usage.total, panel)
        database.change_disk_property(label, "FREE", usage.free, panel)
        database.change_disk_property(label, "PERCENT", usage.percent, panel)
        database.change_disk_property(label, "MOUNT_PATH", partition.mountpoint, panel)
        # # set last mount time
        if disk.status is 0: # this has just been mounted
            database.change_disk_property(label, "LAST_MOUNT_TIME", datetime.now(), panel)
    # del partitions from server
    for partition in del_partitions:
        label = port.get_label_from_partition(partition, panel)
        disk = database.get_disk_by_label(label, panel)
        # general function
        database.change_disk_property(label, "CURRENT_POS", disk.default_pos, panel)
        database.change_disk_property(label, "STATUS", 0, panel)
        # # set last umount time
        database.change_disk_property(label, "LAST_UMOUNT_TIME", datetime.now(), panel)
    # remain partitions
    for partition in rem_partitions:
        usage = port.get_usage_from_partition(partition, user, panel)
        label = port.get_label_from_partition(partition, panel)
        # general function
        database.change_disk_property(label, "USED", usage.used, panel)
        database.change_disk_property(label, "TOTAL", usage.total, panel)
        database.change_disk_property(label, "FREE", usage.free, panel)
        database.change_disk_property(label, "PERCENT", usage.percent, panel)


class ScanThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global scan_queue
        global user, database, panel
        try:
            self._ignore = utils.parse_ignore(panel.IGNORE["scan"])['all']
        except KeyError:
            self._ignore = []

        while True:
            while scan_queue:
                disk = scan_queue[0]
                print "start to scan {}".format(disk.label)
                hierarchy = scan.scan(disk, user, panel, self._ignore)
                # update database
                database.change_disk_property(disk.label, "LAST_SCAN_TIME", datetime.now(), panel)
                database.change_disk_property(disk.label, "hierarchy", json.dumps(hierarchy), panel)
                print "finish scan {}, database updated".format(disk.label)
                scan_queue.pop(0)
            time.sleep(int(panel.LISTEN["round"]) * 60)

class Monitor():

    def __init__(self):
        self._prev_partitions = []
        self._curr_partitions = []
        self._log = log.Logging(panel.LOG["log"], panel.LOG["err"])

    def start(self):
        global scan_queue, backup_queue
        global user, database, panel
        try:
            disk_ignore = utils.parse_ignore(panel.IGNORE["disk"])
            self._scan_ignore = disk_ignore["scan"]
            self._backup_ignore = disk_ignore["backup"]
        except KeyError:
            self._scan_ignore = []
            self._disk_ignore = []

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
                disk = database.get_disk_by_label(label, panel)
                if scan.require_scan(disk, user, panel) and disk not in scan_queue and label not in self._scan_ignore:
                    print "add {} to scan queue".format(disk.label)
                    if not disk.mount_path:
                        disk.mount_path = os.path.join(panel.MOUNT["mount_dir"], disk.label)
                    scan_queue.append(disk)
                print "current scan queue: {}".format(", ".join([d.label for d in scan_queue]))
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
        global scan_queue, backup_queue
        global user, database, panel
        try:
            disk_ignore = utils.parse_ignore(panel.IGNORE["disk"])
            self._scan_ignore = disk_ignore["scan"]
            self._backup_ignore = disk_ignore["backup"]
        except KeyError:
            self._scan_ignore = []
            self._disk_ignore = []

        print "monitor is ready"
        self._log.write("Monitor is ready")
        while True:
            self._log.write("========================================================================")
            self._log.write("new round")
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
                disk = database.get_disk_by_label(label, panel)
                if scan.require_scan(disk, user, panel) and disk not in scan_queue and label not in self._scan_ignore:
                    print "add {} to scan queue".format(disk.label)
                    scan_queue.append(disk)
                # if backup.require_backup(disk, user, panel) and disk not in backup_queue:
                #     backup_queue.append(disk)
            print "current scan queue: {}".format(", ".join([d.label for d in scan_queue]))
            self._log.write("current scan queue: {}".format(", ".join([d.label for d in scan_queue])))
            self._log.write("done")
            self._log.write("========================================================================")
            time.sleep(int(panel.LISTEN["round"]) * 60)

def main():
    # tm = Monitor()
    tm = MonitorThread()
    tm.start()
    time.sleep(60)
    ts = ScanThread()
    ts.start()

if __name__ == '__main__':
    main()
