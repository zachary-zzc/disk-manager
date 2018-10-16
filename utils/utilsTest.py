import sys
import os
import unittest

from utils import *


class utilsTest(unittest.TestCase):

    user = User.instance()
    test_command = "echo hello world"
    curr_devices = ['/dev/sdj', '/dev/sdm', '/dev/sdg', '/dev/sdo',
            '/dev/sdl', '/dev/sdf', '/dev/sdh', '/dev/sde']
    curr_partitions = ['/dev/mapper/centos-root',
            '/dev/sda1',
            '/dev/mapper/centos-home',
            '/dev/sdj2',
            '/dev/sdm2',
            '/dev/sdo1',
            '/dev/sdp1',
            '/dev/sdl1',
            '/dev/sdf1',
            '/dev/sde2',
            '/dev/sdh1',
            '/dev/mapper/centos-home',
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

    test_mount_device1 = "/dev/sdh"
    test_mount_device2 = "/dev/sdj"
    test_mount_path1 = "/mnt/delta_m"
    test_mount_path2 = "/mnt/FGI-37"
    test_mount_label1 = "delta_m"
    test_mount_label2 = "FGI-37"
    test_mount_partition1 = get_partition(test_mount_device1, user)
    test_mount_partition2 = get_partition(test_mount_device2, user)

    def test_a_system_call(self):
        print ""
        print "test system call function"
        stdout = system_call(self.test_command, self.user)
        self.assertEqual(stdout[0], "hello world\n")

    def test_b_list_devices(self):
        print ""
        print "test list devices function"
        devices = list_devices()
        self.assertEqual(devices, self.curr_devices)

    def test_c_get_device_name(self):
        print ""
        print "test get device name function"
        device_name = get_device_name(self.test_device)
        self.assertEqual(device_name, self.test_device_name)

    def test_d_get_device_block_path(self):
        print ""
        print "test get device block path function"
        device_block_path = get_device_block_path(self.test_device)
        self.assertEqual(device_block_path, self.test_device_block_path)

    def test_e_get_partition_id(self):
        print ""
        print "test get partition id function"
        partition_id = get_partition_id(self.test_device, self.user)
        self.assertEqual(partition_id, self.test_partition_id)

    def test_f_list_mounted(self):
        print ""
        print "test list mounted function"
        mounted = list_mounted()
        partition_ids = [partition.device for partition in mounted]
        self.assertEqual(sorted(partition_ids), sorted(self.curr_partitions))

    def test_g_is_mounted(self):
        print ""
        print "test is mounted function"
        self.assertTrue(is_mounted(self.test_device, self.user))

    def test_h_get_usage_from_device(self):
        print ""
        print "test get usage from device function"
        usage = get_usage_from_device(self.test_device, self.user)
        self.assertEqual([usage.total, usage.used, usage.free, usage.percent],
                [self.test_device_total, self.test_device_used,
                    self.test_device_free, self.test_device_percent])

    def test_i_umount_device(self):
        print ""
        print "test umount device function"
        umount_device(self.test_mount_device1, self.user)
        umount_device(self.test_mount_device2, self.user)
        self.assertFalse(is_mounted(self.test_mount_device1, self.user))
        self.assertFalse(is_mounted(self.test_mount_device2, self.user))

    def test_j_mount_device(self):
        print ""
        print "test mount device function"
        mount_device(self.test_mount_device1, self.test_mount_path1, self.user)
        mount_device(self.test_mount_device2, self.test_mount_path2, self.user)
        self.assertTrue(is_mounted(self.test_mount_device1, self.user))
        self.assertTrue(is_mounted(self.test_mount_device2, self.user))

    def test_k_umount_mountpoint(self):
        print ""
        print "test umount mountpoint function"
        umount_mountpoint(self.test_mount_path1, self.user)
        umount_mountpoint(self.test_mount_path2, self.user)
        self.assertFalse(is_mounted(self.test_mount_device1, self.user))
        self.assertFalse(is_mounted(self.test_mount_device2, self.user))
        mount_device(self.test_mount_device1, self.test_mount_path1, self.user)
        mount_device(self.test_mount_device2, self.test_mount_path2, self.user)

    def test_l_umount_partition(self):
        print ""
        print "test umount partition function"
        umount_partition(self.test_mount_partition1, self.user)
        umount_partition(self.test_mount_partition2, self.user)
        self.assertFalse(is_mounted(self.test_mount_device1, self.user))
        self.assertFalse(is_mounted(self.test_mount_device2, self.user))
        mount_device(self.test_mount_device1, self.test_mount_path1, self.user)
        mount_device(self.test_mount_device2, self.test_mount_path2, self.user)

    def test_m_delta_mount_device_with_label(self):
        print ""
        print "test delta mount device with label function"
        umount_device(self.test_mount_device1, self.user)
        umount_device(self.test_mount_device2, self.user)
        delta_mount_device_with_label(self.test_mount_device1, self.test_mount_label1, self.user)
        delta_mount_device_with_label(self.test_mount_device2, self.test_mount_label2, self.user)
        self.assertTrue(check_readme(self.test_mount_path1, self.test_mount_label1))
        self.assertTrue(check_readme(self.test_mount_path2, self.test_mount_label2))

    def test_n_delta_mount_device(self):
        print ""
        print "test delta mount device function"
        umount_device(self.test_mount_device1, self.user)
        umount_device(self.test_mount_device2, self.user)
        delta_mount_device(self.test_mount_device1, self.user)
        delta_mount_device(self.test_mount_device2, self.user)
        self.assertTrue(is_mounted(self.test_mount_device1, self.user))
        self.assertTrue(is_mounted(self.test_mount_device2, self.user))

    def test_o_delta_mount_all(self):
        print ""
        print "test delta mount all function"
        umount_device(self.test_mount_device1, self.user)
        umount_device(self.test_mount_device2, self.user)
        delta_mount_all(self.user)
        self.assertTrue(is_mounted(self.test_mount_device1, self.user))
        self.assertTrue(is_mounted(self.test_mount_device2, self.user))

    def test_p_get_label_from_partition(self):
        print ""
        print "test get label from partition function"
        self.assertEqual(get_label_from_partition(self.test_mount_partition1),
                self.test_mount_label1)
        self.assertEqual(get_label_from_partition(self.test_mount_partition2),
                self.test_mount_label2)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(utilsTest)
    unittest.TextTestRunner().run(suite)
