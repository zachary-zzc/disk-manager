import sys
import os
import datetime
import scandir
from utils.utils import *

def require_scan(disk, user, panel):
    if not disk.last_scan_time:
        return True
    delta = datetime.timedelta(days=int(panel.LISTEN["scan"]))
    return (datetime.datetime.now() - disk.last_scan_time) > delta

def get_tree_size(path):
    total = 0
    for entry in scandir.scandir(path):
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError as error:
            print('Error calling is_dir():', error)
            continue
        if is_dir:
            total += get_tree_size(entry.path)
        else:
            try:
                total += entry.stat(follow_symlinks=False).st_size
            except OSError as error:
                print("Error calling stat():", error)
    return total

def scan(disk, user, panel, ignore=None):
    hierarchy = {}
    for entry in scandir.scandir(disk.mount_path):
        hierarchy[entry.name] = size_human_fmt(get_tree_size(entry.path))
    return hierarchy
