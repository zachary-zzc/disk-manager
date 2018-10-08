import os
import sys


class Backup:
    """
    backup information
    properties:
        - status        backup status, no(0), yes(1)
        - disk          backup disk
    """

    def __init__(self, status, disk):
        self._status = status
        self._disk = disk

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def disk(self, value):
        self._disk = value
