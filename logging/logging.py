import os
import time

class Logging:
    def __init__(self, log_file, err_file,
            log_format="Normal", err_format="Normal"):
        self._ifs = open(log_file, "a+")
        self._efs = open(err_file, "a+")

    def __del__(self):
        self._ifs.close()
        self._efs.close()

    def _get_time(self):
        return time.asctime( time.localtime(time.time()) )

    def write(self, info):
        local_time = self._get_time()
        self._ifs.write("[{}] {}\n".format(local_time, info))

    def error(self, info):
        local_time = self._get_time()
        self._efs.write("[{}] {}\n".format(local_time, info))
