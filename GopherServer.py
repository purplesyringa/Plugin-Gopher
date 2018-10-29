from gevent.server import StreamServer
import logging
import traceback

class GopherServer(object):
    def __init__(self, port, handler):
        self.server = StreamServer(("127.0.0.1", port), self._handle)
        self.log = logging.getLogger(__name__)
        self.handler = handler
    def start(self):
        self.log.debug("Starting GopherServer")
        self.server.start()

    def _handle(self, sock, addr):
        self.log.debug("Connection from %s:%s" % (addr[0], addr[1]))
        # Read all the buffer
        data = ""
        while True:
            buf = sock.recv(1024)
            if not buf:
                break
            data += buf
            if "\r\n" in data:
                # Request ended
                data = data[:data.index("\r\n")]
                break

        # Handle data
        try:
            for result in self.handleRequest(data):
                sock.send(result + "\r\n")
            sock.send(".\r\n")
        finally:
            self.log.debug("Closing connection with %s:%s" % (addr[0], addr[1]))
            sock.close()


    def handleRequest(self, path):
        try:
            result = self.handler(path)
        except Exception as e:
            # Report exceptions as server errors
            formatted = traceback.format_exc(e)
            for line in formatted.split("\n"):
                yield "3%s" % line.replace("\t", "    ")
            return

        yield "iHello, world!"