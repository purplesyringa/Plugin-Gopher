class ServeFile(Exception):
    def __init__(self, file):
        super(ServeFile, self).__init__("Serving file %r" % file)
        self.__file = file

    def getServedFile(self):
        return self.__file




class Switch(object):
    def __init__(self, value):
        self.value = value
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def __call__(self, *cases):
        return self.value in cases