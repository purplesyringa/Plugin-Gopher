import socket
import gevent
import logging

class SocketServer(object):
    def __init__(self, port, max_connections):
        self.sock = socket.socket()
        sock.bind(("", port))
        sock.listen(max_connections)
        self.log = logging.getLogger(__name__)

    def start(self):
        gevent.spawn(self._start)
    def _start(self):
        # Accept connections
        while True:
            conn, addr = self.sock.accept()
            if not conn:
                break
            gevent.spawn(self._onConnection, conn, addr)

    def _onConnection(self, conn, addr):
        self.log.debug("Connection from %s:%d" % (addr[0], addr[1]))

        # Read all the buffer
        while True:
            data = conn.recv(1024)
            if not data:
                break

        # Handle data
        try:
            result = self.handleRequest(data)
            if result is not None:
                conn.send(result)
        finally:
            conn.close()

    def onConnection(self, data):
        raise NotImplementedError("onConnection must be implemented by the server class")