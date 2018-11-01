import os
import sys
import time
import copy
import threading
from utils import utils
from disk.disk import Disk
from database import database as db
from logging import logging as log

_SERVER = "delta2"
_LOG_FILE_ = "log.txt"
_ERR_FILE_ = "err.txt"


def update_database(db, curr_partitions, prev_partitions, user):
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
        usage = utils.get_usage_from_partition(partition, user)
        # labels = list(db.keys())
        label = utils.get_label_from_partition(partition)
        if db.check_disk_in_table(label):
            # generaral function
            db.change_disk_property(label, "CURRENT_POS", _SERVER)
            db.change_disk_property(label, "STATUS", 1)
            db.change_disk_property(label, "USED", usage.used)
            db.change_disk_property(label, "TOTAL", usage.total)
            db.change_disk_property(label, "PERCENT", usage.percent)
            # # set last mount time
            # db.change_disk_property(label, "LAST_MOUNT_TIME", utils._get_time())
            db.change_disk_property(label, "UPDATED_AT", utils._get_time())

            # # for zodb
            # db._dbroot[label].current_pos = _SERVER
            # db._dbroot[label].status = 1
            # db._dbroot[label].usage = usage.used
            # db._dbroot[label].space = usage.total
        else:
            # add disk to table
            disk = Disk(label, current_pos=_SERVER, status=1,
                        used=usage.used, total=usage.total)
            db.add_disk(disk)
    # del partitions from server
    for partition in del_partitions:
        # labels = list(db.keys())
        label = utils.get_label_from_partition(partition)
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
        usage = utils.get_usage_from_partition(partition, user)
        # labels = list(db.keys())
        label = utils.get_label_from_partition(partition)
        # general function
        db.change_disk_property(label, "USED", usage.used)
        db.change_disk_property(label, "TOTAL", usage.total)
        db.change_disk_property(label, "PERCENT", usage.percent)

        # # for zodb
        # db._dbroot[label].usage = usage.used
        # db._dbroot[label].space = usage.total

class MonitorThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._user = utils.User.instance()
        self._prev_partitions = []
        self._curr_partitions = []
        self._db = db.Database.instance()
        self._log = log.Logging(_LOG_FILE_, _ERR_FILE_)

    def run(self):
        print "monitor is ready"
        self._log.write("Monitor is ready")
        while True:
            self._log.write("========================================================================")
            self._log.write("mount all the disks")
            utils.delta_mount_all(self._user)
            self._curr_partitions = utils.list_mounted()
            self._log.write("update database")
            update_database(self._db, self._curr_partitions, self._prev_partitions, self._user)
            self._prev_partitions = copy.deepcopy(self._curr_partitions)
            self._log.write("done")
            self._log.write("========================================================================")

            time.sleep(1800)

def main():
    t = MonitorThread()
    t.start()

if __name__ == '__main__':
    main()


