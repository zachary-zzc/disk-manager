import sys
import os
import unittest

from utils import *


class utilsTest(unittest.TestCase):

    user = User.instance()
    test_command = "echo hello world"
    curr_devices = ['/dev/sdj', '/dev/sdm', '/dev/sdg', '/dev/sdo',
            '/dev/sdl', '/dev/sdf', '/dev/sdh', '/dev/sde']
    curr_partitions = ['/dev/mapper/centos-root', '/dev/sda1',
            '/dev/mapper/centos-home', '/dev/sdj2', '/dev/sdm2',
            '/dev/sdo1', '/dev/sdp1', '/dev/sdl1', '/dev/sdf1',
            '/dev/sde2', '/dev/sdh1', '/dev/mapper/centos-home',
            '/dev/mapper/centos-home',
            '/dev/mapper/docker-253:2-4599664633-67d11bd5f5adef321373455ce4e3d2c5849fc4f125aabc248d2069d51832725f',
            '/dev/sdg1']
    test_device = "/dev/sdg"
    test_device_name = "sdg"
    test_device_block_path = "/sys/block/sdg"
    test_partition_id = "/dev/sdg1"
    test_partition = get_partition(test_device, user)
    test_device_total = 3726
    test_device_used = 3618
    test_device_free = 107
    test_device_percent = 97.1

    test_mount_device1 = "/dev/sdg"
    test_mount_device2 = "/dev/sdj"
    test_mount_path1 = "/mnt/delta_b"
    test_mount_path2 = "/mnt/FGI-37"

    def test_system_call(self):
        stdout = system_call(self.test_command, self.user)
        self.assertEqual(stdout[0], "hello world\n")

    def test_list_devices(self):
        devices = list_devices()
        self.assertEqual(devices, self.curr_devices)

    def test_get_device_name(self):
        device_name = get_device_name(self.test_device)
        self.assertEqual(device_name, self.test_device_name)

    def test_get_device_block_path(self):
        device_block_path = get_device_block_path(self.test_device)
        self.assertEqual(device_block_path, self.test_device_block_path)

    def test_get_partition_id(self):
        partition_id = get_partition_id(self.test_device, self.user)
        self.assertEqual(partition_id, self.test_partition_id)

    def test_list_mounted(self):
        mounted = list_mounted()
        partition_ids = [partition.device for partition in mounted]
        self.assertEqual(partition_ids, self.curr_partitions)

    def test_is_mounted(self):
        self.assertEqual(is_mounted(self.test_device, self.user), True)

    def test_get_usage_from_device(self):
        usage = get_usage_from_device(self.test_device, self.user)
        self.assertEqual([usage.total, usage.used, usage.free, usage.percent],
                [self.test_device_total, self.test_device_used,
                    self.test_device_free, self.test_device_percent])

    def test_umount_mount_device(self):
        umount_device(self.test_mount_device1, self.user)
        umount_device(self.test_mount_device2, self.user)
        mount_device(self.test_mount_device1, self.test_mount_path1, self.user)
        mount_device(self.test_mount_device2, self.test_mount_path2, self.user)

    def test_mount_device(self):
        pass

    def test_umount_mountpoint(self):
        pass

    def test_umount_partition(self):
        pass

    def test_umount_device(self):
        pass

    def test_delta_mount_partition(self):
        pass

    def test_delta_mount_device(self):
        pass

    def test_delta_mount_all(self):
        pass

    def test_get_label_from_partition(self):
        pass


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(utilsTest)
    unittest.TextTestRunner().run(suite)
