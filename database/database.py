import psycopg2 as psql
import json
from singleton_decorator import singleton
from datetime import datetime
from disk.disk import Disk
from utils.utils import *

@singleton
class Database:
    """ database """
    def __init__(self):
        self._conn = None

    def _open(self, panel):
        try:
            self._conn = psql.connect(database=panel.DATABASE["database"],
                    user=panel.DATABASE["user"],
                    password=panel.DATABASE["password"],
                    host = panel.DATABASE["host"],
                    port = panel.DATABASE["port"])
        except:
            raise

    def _close(self):
        try:
            self._conn.close()
        except:
            raise

    def scan(self, panel):
        prows = []
        drows = []
        brows = []

        self._open(panel)
        cur = self._conn.cursor()
        try:
            # disks without principles
            cur.execute("SELECT label from disks WHERE principle = ''")
            prows = cur.fetchall()
            # disks without default storage position
            cur.execute("SELECT label from disks WHERE default_pos = ''")
            drows = cur.fetchall()
            # disks have not backup
            cur.execute("SELECT label from disks WHERE backup_status = 0")
            drows = cur.fetchall()
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            self._conn.commit()
        finally:
            cur.close()
            self._close()
            return prows, drows, brows

    def get_disk_by_label(self, label, panel):
        disk = None

        self._open(panel)
        cur = self._conn.cursor()
        try:
            cur.execute("SELECT * from disks WHERE label = '{}'".format(label))
            index, label, princ, default_pos, current_pos, status, total, used, \
                    free, percent, mount_path, \
                    backup_status, backup_pos, \
                    last_mount_time, last_umount_time, \
                    last_scan_time, last_backup_time, \
                    description, disk_info_string, \
                    hierarchy_string = cur.fetchall()[0]
            # change disk_info, hierarchy to dict object
            disk_info = json.loads(disk_info_string) if disk_info_string else {}
            hierarchy = json.loads(hierarchy_string) if hierarchy_string else {}
            disk = Disk(label, principle=princ, default_pos=default_pos,
                    current_pos=current_pos, status=status, total=total,
                    used=used, mount_path=mount_path, backup_status=backup_status,
                    backup_pos=backup_pos, last_mount_time=last_mount_time,
                    last_umount_time=last_umount_time, last_scan_time=last_scan_time,
                    last_backup_time=last_backup_time, description=description,
                    disk_info=disk_info, hierarchy=hierarchy)
            self._conn.commit()
        except:
            self._conn.rollback()
            self._conn.commit()
            print label
            cur.execute("SELECT * from disks WHERE label = '{}'".format(label))
            print cur.fetchall()
            raise
        finally:
            cur.close()
            self._close()
        return disk

    def get_disk_property(self, label, header, panel):
        self._open(panel)
        cur = self._conn.cursor()
        prop = None

        try:
            cur.execute("SELECT {} from disks WHERE label = '{}'".format(header, label))
            prop = cur.fetchall()[0]
            if header is "disk_info" or header is "hierarchy":
                prop = json.loads(prop)
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            self._conn.commit()
            raise
        finally:
            cur.close()
            self._close()
        return prop

    def change_disk_property(self, label, header, content, panel):
        self._open(panel)
        cur = self._conn.cursor()

        try:
            cur.execute("UPDATE disks SET {} = '{}' WHERE label = '{}'".format(header, content, label))
            self._conn.commit()
        except:
            self._conn.rollback()
            self._conn.commit()
            raise
        finally:
            cur.close()
            self._close()

    def check_disk_in_table(self, label, panel):
        self._open(panel)
        cur = self._conn.cursor()

        try:
            cur.execute("SELECT label from disks")
            labels = cur.fetchall()
            return label in [l[0] for l in labels]
        except:
            self._conn.rollback()
            self._conn.commit()
            raise
        finally:
            cur.close()
            self._close()

    def add_disk(self, disk, panel):
        self._open(panel)
        cur = self._conn.cursor()

        try:
            cur.execute("INSERT INTO disks "
                    "(label, principle, default_pos, current_pos, "
                    "status, total, used, free, percent, mount_path, "
                    "backup_status, backup_place, "
                    "last_mount_time, last_umount_time, "
                    "last_scan_time, last_backup_time, "
                    "description, disk_info, hierarchy) "
                    "VALUES ({})".format(
                        ', '.join(format_db_str(
                            [disk.label, disk.principle, disk.default_pos,
                             disk.current_pos, disk.status, disk.total,
                             disk.used, disk.free, disk.percent, disk.mount_path,
                             disk.backup_status, disk.backup_pos,
                             disk.last_mount_time, disk.last_umount_time,
                             disk.last_scan_time, disk.last_backup_time,
                             disk.description, disk.disk_info, disk.hierarchy]
                            )
                            )
                        )
                    )
            self._conn.commit()
        except:
            self._conn.rollback()
            self._conn.commit()
            raise
        finally:
            cur.close()
            self._close()
