import sys
import os
from disk.disk import Disk


def get_disk_label(disk):
    if isinstance(disk, str):
        return disk
    if isinstance(disk, Disk):
        return disk.label
    raise TypeError("{} is not a valid disk type".format(type(disk)))
