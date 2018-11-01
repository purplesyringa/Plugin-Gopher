class HTTPGopherProxy(object):
    def __init__(self):
        self.code = "Welcome to HTTP Gopher proxy!<hr><pre>"
    def append(self, part):
        self.code += part
    def format(self):
        self.code += "</pre><hr>See you later!"
        return self.code
