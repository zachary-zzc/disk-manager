import sys
import os
import pwd
import psutil as ps
import pyudev
from pyudev.core import Device

from utils.utils import *

def get_disk_label(disk, panel=None):
    if isinstance(disk, str):
        return disk
    if hasattr(disk, "label"):
        return disk.label
    raise TypeError("{} is not a valid disk type".format(type(disk)))

def list_devices(panel=None):
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

def get_device_name(device, panel=None):
    return os.path.basename(device)

def get_device_block_path(device, panel=None):
    return os.path.join("/sys/block", get_device_name(device))

def get_partition_id(device, user, panel=None):
    context = pyudev.Context()
    dev = Device.from_device_file(context, device)
    spec_str = "Partition 1 does not start on physical sector boundary."
    if dev['ID_PART_TABLE_TYPE'] == 'gpt':
        stdout = system_call("fdisk -l {}".format(device), user)
        # special cases, partitions like /dev/sde2
        if spec_str in ''.join(stdout):
            return device + "2"
        return device + "1"
    else:
        stdout = system_call("fdisk -l {}".format(device), user)
        # special cases, partitions like /dev/sde2
        if spec_str in ''.join(stdout):
            return stdout[-2].split()[0].strip()[:-1] + "2"
        return stdout[-1].split()[0].strip()

def list_mounted(panel=None):
    return [d for d in ps.disk_partitions()
            if d.fstype == "fuseblk"
            and "temp" not in d.mountpoint]

def is_mounted(device, user, panel=None):
    return get_partition_id(device, user, panel) in [dev.device for dev in list_mounted(panel)]

def get_partition(device, user, panel=None):
    assert(is_mounted(device, user, panel))
    partition_id = get_partition_id(device, user, panel)
    partition = list_mounted(panel)[
            [dev.device for dev in list_mounted(panel)].index(partition_id)
            ]
    return partition

def get_usage_from_device(device, user, panel=None):
    partition = get_partition(device, user, panel)
    usage = ps.disk_usage(partition.mountpoint)
    from collections import namedtuple
    Usage = namedtuple("Usage", ["total", "used", "free", "percent"])
    husage = Usage(round(float(usage.total) / 1024 ** 3, 2),
                   round(float(usage.used) / 1024 ** 3, 2),
                   round(float(usage.free) / 1024 ** 3, 2),
                   round(float(usage.percent), 2))
    return husage

def get_usage_from_partition(partition, user, panel=None):
    usage = ps.disk_usage(partition.mountpoint)
    from collections import namedtuple
    Usage = namedtuple("Usage", ["total", "used", "free", "percent"])
    # print usage.total
    # print float(usage.total) / 1024 ** 4
    husage = Usage(round(float(usage.total) / 1024 ** 4, 2),
                   round(float(usage.used) / 1024 ** 4, 2),
                   round(float(usage.free) / 1024 ** 4, 2),
                   round(float(usage.percent), 2))
    return husage

def mount_partition_id(partition_id, path, user, panel=None):
    assert(not os.path.ismount(path))
    system_call("mount {} {}".format(partition_id, path), user)

def mount_device(device, path, user, panel=None):
    assert(not os.path.ismount(path))
    system_call("mount {} {}".format(get_partition_id(device, user), path), user)

def umount_mountpoint(mountpoint, user, panel=None):
    system_call("umount {}".format(mountpoint), user)

def umount_partition(partition, user, panel=None):
    umount_mountpoint(partition.mountpoint, user, panel)

def umount_device(device, user, panel=None):
    umount_mountpoint(get_partition(device, user, panel).mountpoint, user, panel)

def check_readme(path, label, panel=None):
    readme = os.path.join(path, "readme_of_{}.txt".format(label))
    # check readme file exist
    if os.path.isfile(readme):
        # check readme format
        with open(readme) as ifs:
            if "This is an auto readme file of this disk" in ifs.readline():
                return True
    return False

def write_readme(path, label, panel=None):
    if check_readme(path, label):
        return
    readme = os.path.join(path, "readme_of_{}.txt".format(label))
    print "write readme file to {}".format(readme)
    with open(readme, "w") as ofs:
        ofs.write("# This is an auto readme file of this disk\n")
        ofs.write("\n")
        ofs.write("This disk belongs to the Delta group of CS Dept. in CityU of HK.\n")
        ofs.write("The No. of this disk is {}\n".format(label))
        ofs.write("\n")
        ofs.write("Please modify your items in the disk management system of Delta group.\n")
        ofs.write("The disk management system aims to facilitate clear and simple disk-management.\n")
        ofs.write("Any question about the disk management system, please contact Zicheng Zhao.\n")
        ofs.write("\n")
        ofs.write("Please do not MODIFY this file.\n")
        ofs.write("\n")
        ofs.write("\n")
        ofs.write(50*" " + "Zicheng Zhao\n")
        ofs.write(45*" " + "Mail: shinaider.zhao@gmail.com\n")

def delta_mount_partition_id_with_label(partition_id, label, user, panel=None):
    """
    specific script for mount disks on delta servers
    """
    path = os.path.join("/mnt", label)
    if not os.path.isdir(path):
        os.mkdir(path)
    assert(not os.path.ismount(path))

    mount_partition_id(partition_id, path, user, panel)
    write_readme(path, label, panel)

def delta_mount_partition_with_label(partition, label, user, panel=None):
    delta_mount_partition_id_with_label(partition.device, label, user, panel)

def delta_mount_device_with_label(device, label, user, panel=None):
    delta_mount_partition_id_with_label(get_partition_id(device, user, panel), label, user, panel)

def delta_mount_partition_id(partition_id, user, panel=None):
    """
    find mount point by read me file
    if cannot find corresponding read me file:
        send me an alert email for manual mount.
    spesific script for mount disks on server
    """
    # check temp mount path exist, if not mkdir
    if not os.path.isdir(panel.MOUNT["temp_mount_dir"]):
        os.mkdir(panel.MOUNT["temp_mount_dir"])
    # if temp dir is mounted, umount it
    # FIXME: find a safe method
    if os.path.ismount(panel.MOUNT["temp_mount_dir"]):
        umount_mountpoint(panel.MOUNT["temp_mount_dir"], user)

    # mount device to temp dir
    mount_partition_id(partition_id, panel.MOUNT["temp_mount_dir"], user, panel)

    # find readme file
    readme = ""
    for _ in os.listdir(panel.MOUNT["temp_mount_dir"]):
        if "readme" in _.lower():
            readme = _
    # get mountpoint from readme file
    try:
        mountpoint = os.path.basename(readme).split(".")[0].replace("readme_of_", "")
        mountpoint = os.path.join("/mnt", mountpoint)
    except:
        subject = "[MOUNT ERROR] Cannot auto mount disk at %s" % panel.SERVER["server"]
        content  = "Hi Zac, \n"
        content += "\n"
        content += "Time: %s\n" % str(_get_time())
        content += "Error: Cannot auto mount disk at %s\n" % panel.SERVER["server"]
        content += "       We cannot find the README file that indicates disk label\n"
        content += "Partition ID: %s\n" % partition_id
        content += "\n"
        content += "Please manually mount this partition, README file will be automatically generated within %s minutes after you mount the disk" % str(panel.LISTEN["round"])
        content += "\n"
        content += "\n"
        content += "best regards\n"
        content += "DISK MANAGER@delta\n"

        to_addr_list = [panel.REPORT["admin_email_list"].split(",")]
        cc_addr_list = []
        admin_email(subject, content, to_addr_list, cc_addr_list)
    finally:
        # umount partition from temp mountpoint
        umount_mountpoint(panel.MOUNT["temp_mount_dir"], user, panel)
        # raise KeyError("This partition id {} do not have readme file, please mount with disk label".format(
        #     partition_id
        #     )
        #     )
    # remount partition
    try:
        mount_partition_id(partition_id, mountpoint, user, panel)
        print "successfully mount disk {} to {}".format(partition_id, mountpoint)
    except AssertionError:
        print partition_id, mountpoint
        print "Cannot mount this partition to mountpoint, the mountpoint has already been used, please check manually"

def delta_mount_device(device, user, panel=None):
    delta_mount_partition_id(get_partition_id(device, user, panel), user, panel)

def delta_check_all(user, panel=None):
    # check readme files on mounted files
    for partition in list_mounted(panel):
        mountpoint = partition.mountpoint
        label = mountpoint.replace("/mnt/", "")
        if "temp" in label:
            continue
        write_readme(mountpoint, label, panel)

def delta_mount_all(user, panel=None):
    for device in list_devices(panel):
        if not is_mounted(device, user, panel):
            delta_mount_device(device, user, panel)

def get_label_from_partition(partition, panel=None):
    return partition.mountpoint.split("/")[-1]
