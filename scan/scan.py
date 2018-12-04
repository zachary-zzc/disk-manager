import sys
import os
import datetime
import scandir
from utils.utils import *

def require_scan(disk, user=None, panel=None):
    if not disk.last_scan_time:
        return True
    delta = datetime.timedelta(days=int(panel.LISTEN["scan"]))
    return (datetime.datetime.now() - disk.last_scan_time) > delta

def get_tree_size(path):
    total = 0
    for entry in scandir.scandir(path):
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
            entry.stat(follow_symlinks=False)
        except OSError as error:
            print 'OSError', error
            continue
        if is_dir:
            total += get_tree_size(entry.path)
        else:
            try:
                total += entry.stat(follow_symlinks=False).st_size
            except OSError as error:
                print "OSError, ", e
                total += 0
    return total

def scan(disk, user=None, panel=None, ignore=None):
    hierarchy = {}
    for entry in scandir.scandir(disk.mount_path):
        if check_ignore(entry.name, ignore):
            continue
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
            entry.stat(follow_symlinks=False)
        except OSError as error:
            print 'OSError', error
            hierarchy[entry.name] = error.strerror
            continue
        if is_dir:
            hierarchy[entry.name] = size_human_fmt(get_tree_size(entry.path))
        else:
            try:
                hierarchy[entry.name] = size_human_fmt(entry.stat(follow_symlinks=False).st_size)
            except OSError as error:
                print "OSError ", error
                hierarchy[entry.name] = error.strerror
    return hierarchy
