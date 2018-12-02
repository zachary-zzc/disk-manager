import psycopg2 as psql
from singleton_decorator import singleton

from disk.disk import Disk
from utils import utils

DATABASE = "disk-manager_production"
USER = "diskmanager"
PASSWORD = "diskmanager_production"
PORT = "5432"
HOST = "dl380a.cs.cityu.edu.hk"

@singleton
class Database:
    """ database """
    def __init__(self):
        self._conn = None

    def _open(self):
        try:
            self._conn = psql.connect(database=DATABASE, user=USER,
                password=PASSWORD, host=HOST, port=PORT)
        except:
            raise

    def _close(self):
        try:
            self._conn.close()
        except:
            raise

    def scan(self):
        prows = []
        drows = []
        brows = []

        self._open()
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

    def get_disk_by_label(self, label):
        disk = None

        self._open()
        cur = self._conn.cursor()
        try:
            cur.execute("SELECT * from disks WHERE label = '{}'".format(label))
            index, label, princ, default_pos, \
                    current_pos, status, total, used, \
                    free, percent, mount_path, \
                    backup_status, backup_pos = cur.fetchall()[0]
            disk = Disk(label, principle=princ, default_pos=default_pos,
                    current_pos=current_pos, status=status, total=total,
                    used=used, mount_path=mount_path, backup_status=backup_status,
                    backup_pos=backup_pos)
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            self._conn.commit()
        finally:
            cur.close()
            self._close()
            return disk

    def change_disk_property(self, label, header, content):
        self._open()
        cur = self._conn.cursor()

        try:
            cur.execute("UPDATE disks SET {} = '{}' WHERE label = '{}'".format(header, content, label))
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            self._conn.commit()
            raise
        finally:
            cur.close()
            self._close()

    def check_disk_in_table(self, label):
        self._open()
        cur = self._conn.cursor()

        try:
            cur.execute("SELECT label from disks")
            labels = cur.fetchall()
            return label in [l[0] for l in labels]
        except Exception:
            self._conn.rollback()
            self._conn.commit()
            raise
        finally:
            cur.close()
            self._close()

    def add_disk(self, disk):
        self._open()
        cur = self._conn.cursor()

        try:
            cur.execute("INSERT INTO disks "
                    "(label, principle, default_pos, current_pos, "
                    "status, total, used, free, percent, mount_path, "
                    "backup_status, backup_place, created_at, updated_at) "
                    "VALUES ({})".format(
                        ', '.join(utils._format_db_str(
                            [disk.label, disk.principle, disk.default_pos,
                             disk.current_pos, disk.status, disk.total,
                             disk.used, disk.free, disk.percent, disk.mount_path,
                             disk.backup_status, disk.backup_pos,
                             utils._get_time(), utils._get_time()]
                            )
                            )
                        )
                    )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            self._conn.commit()
            raise
        finally:
            cur.close()
            self._close()
