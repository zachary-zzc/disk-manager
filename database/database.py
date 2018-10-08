from ZODB import FileStorage, DB
import transaction

from utils.singleton import Singleton
from utils import utils
from disk.disk import Disk

DataPath = "data.fs"


@Singleton
class Database:
    """database functions, singleton"""

    def __init__(self):
        self._storage = FileStorage.FileStorage(DataPath)
        self._db = DB(self._storage)
        self._connection = self._db.open()
        self.dbroot = self._connection.root()

    def close(self):
        self._connection.close()
        self._db.close()
        self._storage.close()


dbroot = Database.instance().dbroot


def add_disk(disk):
    assert isinstance(disk, Disk), "Database can only store disk type"
    dbroot[disk.label] = disk
    transaction.commit()


def query_disk_by_label(disk):
    label = utils.get_disk_label(disk)
    return dbroot.get(label)
    # try:
    #     return dbroot.get(label)
    # except:
    #     raise KeyError("Disk not exist: {}".format(label))


def query_disk_by_principle(princ):
    pass


def query_disk_by_pos(pos):
    pass


def query_disk_by_status(status):
    pass


def query_disk_by_spare(spare):
    pass


def delete_disk(disk):
    label = utils.get_disk_label(disk)
    del dbroot[label]
    transaction.commit()


def list_disks(verbose=False):
    if verbose is False:
        # add header
        print("{}\t{}\t{}\t{}\t{}".format(
            "label", "position", "status", "total", "usage"
        )
        )
    for disk in dbroot.values():
        if verbose is False:
            print(
                "{}\t{}\t{}\t{}\t{}".format(
                    disk.label,
                    disk.current_pos,
                    disk.status,
                    disk.space,
                    disk.usage))
        else:
            print(disk)


def close():
    Database.instance().close()


# as zodb will track and auto update objects, this function is not nessesary
# def modify_disk(orig_disk, new_disk):
#     pass
