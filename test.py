from disk.disk import Disk
from database import database as db

import os
import sys

# test cases


def test():
    # init disk delta_a, delta_b
    label_a = "delta_a"
    pos_a = "MMW3440"
    status_a = 0
    princ_a = "zzc"
    space_a = 4
    usage_a = 2.5

    label_b = "delta_b"
    pos_b = "dl580a"
    status_b = 1
    princ_b = "jwl"
    space_b = 4
    usage_b = 3.0
    port_b = "sda"

    delta_a = Disk(label_a, princ_a, pos_a, pos_a,
                   status_a, space_a, usage_a)
    delta_b = Disk(label_b, princ_b, pos_b, pos_a,
                   status_b, space_b, usage_b, port=port_b)

    db.add_disk(delta_a)
    db.add_disk(delta_b)

    print("add disk done")
    db.list_disks()

    print("query disk a")
    print(db.query_disk_by_label("delta_a"))
    print("------------------------------------------------------")
    print("query disk b")
    print(db.query_disk_by_label(delta_b))

    print("delete disk")
    db.delete_disk("delta_a")
    db.list_disks()

    db.close()


if __name__ == "__main__":
    test()
