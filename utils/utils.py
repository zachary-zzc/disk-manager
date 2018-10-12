import sys
import os
import pwd
import psutil as ps

from singleton import Singleton

_DEFAULT_USER = "zzc"
_DEFAULT_PASSWORD = "zhao900420"

_TEMP_MOUNT_DIR = "/mnt/temp"


def get_disk_label(disk):
    if isinstance(disk, str):
        return disk
    if hasattr(disk, "label"):
        return disk.label
    raise TypeError("{} is not a valid disk type".format(type(disk)))

@Singleton
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

def system_call(cmdline, user, with_root=True):
    """
    system call
    return:
        STDOUT
    """
    if user.tp is 0:
        return os.popen(cmdline).readlines()
    else:
        if with_root:
            # if temp file exist, delete it first
            if os.path.isfile(".temp"): os.remove(".temp")
            # first touch
            print "first touch"
            os.popen("sudo -S sleep 0.01", "w").write(user.passwd)
            # write stdout to temp file
            os.popen("sudo -S " + cmdline + " > .temp", 'w').write(user.passwd)
            with open(".temp", "r") as ifs:
                stdout = ifs.readlines()
            # delete temp file
            os.remove(".temp")
            return stdout
        else:
            return os.popen(cmdline).readlines()

def list_devices():
    with open('/proc/partitions', 'r') as ifs:
        devices = []

        for line in ifs.readlines()[2:]: # skip header
            tokens = [ token.strip() for token in line.split() ]
            minor_number = int(tokens[1])
            device_name = tokens[3]

            if (minor_number % 16) is 0:
                path = "/sys/class/block/" + device_name
                if os.path.islink(path):
                    if os.path.realpath(path).find("/usb") > 0:
                        devices.append("/dev/" + device_name)
    return devices

def get_device_name(device):
    return os.path.basename(device)

def get_device_block_path(device):
    return os.path.join("/sys/block", get_device_name(device))

def get_partition_id(device, user):
    stdout = system_call("fdisk -l {}".format(device), user)
    # special cases, partitions like /dev/sde2
    spec_str = "Partition 1 does not start on physical sector boundary."
    if spec_str in stdout[-1]:
        return stdout[-2].split()[0].strip()[:-1] + "2"
    return stdout[-1].split()[0].strip()

def list_mounted():
    return ps.disk_partitions()

def is_mounted(device, user):
    return get_partition_id(device, user) in [dev.device for dev in list_mounted()]

def get_partition(device, user):
    assert(is_mounted(device, user))
    partition_id = get_partition_id(device, user)
    partition = list_mounted()[
            [dev.device for dev in list_mounted()].index(partition_id)
            ]
    return partition

def get_usage_from_device(device, user):
    partition = get_partition(device, user)
    usage = ps.disk_usage(partition.mountpoint)
    from collections import namedtuple
    Usage = namedtuple("Usage", ["total", "used", "free", "percent"])
    husage = Usage(usage.total / 1024 ** 3, usage.used / 1024 ** 3,
            usage.free / 1024 ** 3, usage.percent)
    return husage

def get_usage_from_partition(partition, user):
    return ps.disk_usage(partition.mountpoint)

def mount_partition(partition, path, user):
    assert(not os.path.ismount(path))
    system_call("mount {} {}".format(partition.device, path), user)

def mount_partition_id(partition_id, path, user):
    assert(not os.path.ismount(path))
    system_call("mount {} {}".format(partition_id, path), user)

def mount_device(device, path, user):
    assert(not os.path.ismount(path))
    system_call("mount {} {}".format(get_partition_id(device), path), user)

def umount_mountpoint(mountpoint, user):
    system_call("umount {}".format(mountpoint), user)

def umount_partition(partition, user):
    umount_mointpoint(partition.mointpoint, user)

def umount_device(device, user):
    umount_mointpoint(get_partition(device, user).mointpoint, user)

def delta_mount_partition(partition, user):
    """
    spesific script for mount disks on server
    """
    # check temp mount path exist, if not mkdir
    if not os.path.isdir(_TEMP_MOUNT_DIR):
        os.mkdir(_TEMP_MOUNT_DIR)
    # if temp dir is mounted, umount it
    # FIXME: find a safe method
    if os.path.ismount(_TEMP_MOUNT_DIR):
        umount_mountpoint(_TEMP_MOUNT_DIR, user)

    # mount device to temp dir
    mount_partition(partition, _TEMP_MOUNT_DIR, user)

    # find readme file
    readme = ""
    for _ in os.listdir(_TEMP_MOUNT_DIR):
        if "readme" in _.lower():
            readme = _
    # get mountpoint from readme file
    mountpoint = os.path.basename(readme).upper().replace("README_", "")
    mountpoint = os.path.join("/mnt", mountpoint)

    # umount partition from temp mountpoint
    umount_partition(partition, user)

    # remount partition
    mount_partition(partition, mountpoint, user)

def delta_mount_device(device, user):
    delta_mount_partition(get_partition(device, user), user)

def delta_mount_all(user):
    for device in list_devices():
        if not is_mounted(device, user):
            delta_mount_device(device, user)

def get_label_from_partition(partition, labels):
    tmp = partition.mountpoint.split("/")[-1]
    return [label for label in labels if label.upper() == tmp.upper()][0]
