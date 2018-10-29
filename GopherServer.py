from gevent.server import StreamServer
import logging

class GopherServer(object):
    def __init__(self, port):
        self.server = StreamServer(("127.0.0.1", port), self._handle)
        self.log = logging.getLogger(__name__)
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
            result = self.handleRequest(data)
            if result is not None:
                sock.send(result)
        finally:
            self.log.debug("Closing connection with %s:%s" % (addr[0], addr[1]))
            sock.close()


    def handleRequest(self, data):
        self.log.debug("Received: %s" % data)
        return "iHello, world!\r\n.\r\n"