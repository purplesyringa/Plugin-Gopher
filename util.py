class ServeFile(Exception):
    def __init__(self, file):
        super(Exception, self).__init__("Serving file %r" % file)
        self.__file = file

    def getServedFile(self):
        return self.__file