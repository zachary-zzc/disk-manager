import os
import sys
from persistent import Persistent


class Disk(Persistent):
    def __init__(
            self,
            label,
            principle="",
            info="",
            default_pos="",
            current_pos="",
            total=0.,
            used=0.,
            status=0,
            mount_path="",
            last_mount_time=None,
            last_umount_time=None,
            backup_status=0,
            backup_pos=""):
        """
        Disk Object
        Properties:
            [BASIC INFO]
            - Label             The label of the disk (delta_*)
            - Principle         The persion in charge of this disk
            - Information       Information of the disk
            - Default_pos       The default position of the disk
            - Current_pos       Current position of the disk
            - Total             Total space of the disk
            - Used              Used space of the disk
            - Free              Free space of the disk
            - Percent           Used percent of the disk
            [MOUNT INFO]
            - Status            Disk status, including idle(0), mount(1), working(2), sick(3)
            - Mount_path        Mount path of the disk if it is mounted
            - Last_mount_time   Last time the disk was mounted
            - Last_umount_time  Last time the disk was umounted
            [BACKUP INFO]
            - Backup_status     Whether the disk has backup, No(0), Yes(1)
            - Backup_pos        Backup label of the disk
        """
        # ava_kwargs = {'port', 'backup_info'}
        # for kwarg in kwargs.keys():
        #     assert kwarg in ava_kwargs, "Invalid argument: " + kwarg
        self.label = label
        self.principle = principle
        self.info = info
        self.default_pos = default_pos
        self.current_pos = current_pos
        self.total = total
        self.used = used
        self.free = total - used
        self.percent = 0 if self.total == 0. else \
                float(self.used) / float(self.total)
        self.percent = round(self.percent, 2) * 100

        self.status = status
        self.mount_path = mount_path
        self.last_mount_time = last_mount_time
        self.last_umount_time = last_umount_time

        self.backup_status = backup_status
        self.backup_pos = backup_pos

    def __repr__(self):
        ret = ""
        status = ""
        if self.status is 0:
            status = "idle"
        if self.status is 1:
            status = "mounted"
        if self.status is 2:
            status = "working"
        if self.status is 3:
            status = "sick"
        ret += "Label: {}\n".format(self.label)
        ret += "Status: {}\n".format(status)
        ret += "Current Position: {}\n".format(self.current_pos)
        ret += "Default Position: {}\n".format(self.default_pos)
        if self.mount_path:
            ret += "Mount Path: {}\n".format(self.mount_path)
        ret += "Principle: {}\n".format(self.principle)
        ret += "Total Space: {}G\n".format(self.space)
        ret += "Usage: {}G\n".format(self.usage)
        if self.backup_info:
            ret += "Backup Information:\n"
            ret += str(self.backup_info)
        return ret

    def __str__(self):
        return self.__repr__()

    # def is_backup(self):
    #     return self.backup_info.status

    # def update_backup(self, status, pos):
    #     self.backup_info.status = status
    #     self.backup_info.pos = pos
