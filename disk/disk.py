import os
import sys
from persistent import Persistent


class Disk(Persistent):
    def __init__(
            self,
            label,
            principle,
            current_pos,
            default_pos,
            status,
            space,
            usage,
            **kwargs):
        """
        Disk Object
        Properties:
            - Label        The label of the disk (delta_*)
            - Current_pos  Current position of the disk
            - Status       Disk status, including idle(0), mount(1), working(2), sick(3)
            - Principle    The persion in charge of this disk
            - Default_pos  The default position of the disk
            - Space        Total space of the disk
            - Usage        Space usage
            - Mount_path   Mount path of the disk if it is mounted
            - Information  Information of the disk
            - BackupInfo   Backup information of the disk
        """
        ava_kwargs = {'port', 'backup_info'}
        for kwarg in kwargs.keys():
            assert kwarg in ava_kwargs, "Invalid argument: " + kwarg
        self.label = label
        self.principle = principle
        self.current_pos = current_pos
        self.default_pos = default_pos
        self.status = status
        self.space = space
        self.usage = usage

        mount_path = kwargs.get("mount_path", False)
        backup_info = kwargs.get("backup_info", False)

        self.info = kwargs.get("info", "")
        self.mount_path = mount_path if mount_path else ""
        self.backup_info = backup_info if backup_info else None

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

    def is_backup(self):
        return self.backup_info.status

    def update_backup(self, status, pos):
        self.backup_info.status = status
        self.backup_info.pos = pos
