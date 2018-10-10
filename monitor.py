import os
import sys
import time
import threading
from utils.utils import *
from database import database as db
from logging import logging as log

_SERVER = "delta2"


def update_database(dbroot, curr_partitions, prev_partitions, user):
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
        usage = get_usage_from_partition(partition, user)
        labels = list(dbroot.keys())
        label = get_label_from_partition(partition, labels)
        dbroot[label].current_pos = _SERVER
        dbroot[label].status = 1
        dbroot[label].usage = usage.used
        dbroot[label].space = usage.total
    # del partitions from server
    for partition in del_partitions:
        labels = list(dbroot.keys())
        label = get_label_from_partition(partition, labels)
        dbroot[label].current_pos = dbroot[label].default_pos
        dbroot[label].status = 0
    # remain partitions
    for partition in rem_partitions:
        usage = get_usage_from_partition(partition, user)
        labels = list(dbroot.keys())
        label = get_label_from_partition(partition, labels)
        dbroot[label].usage = usage.used
        dbroot[label].space = usage.total

class MonitorThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._user = User.instance()
        self._prev_partitions = []
        self._curr_partitions = []
        self._dbroot = db.Database.instance().dbroot

    def run(self):
        log.write("Monitor is ready")
        while True:
            log.write("========================================================================")
            log.write("mount all the disks")
            delta_mount_all(self._user)
            self._curr_partitions = list_mounted()
            log.write("update database")
            update_database(self._dbroot, self._curr_partitions, self._prev_partitions)
            log.write("done")
            log.write("========================================================================")

            time.sleep(1800)

def main():
    t = MonitorThread()
    t.start()
