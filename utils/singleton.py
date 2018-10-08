import threading


class Singleton:

    def __init__(self, decorated):
        self._decorated = decorated
        self.lock = threading.Lock()

    def instance(self):
        try:
            return self._instance
        except AttributeError:
            self.lock.acquire()
            try:
                return self._instance
            except AttributeError:
                self._instance = self._decorated()
                return self._instance
            finally:
                self.lock.release()

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)
