from gevent.server import StreamServer
from GopherHandler import GopherHandler
import logging
import traceback

class GopherServer(object):
    def __init__(self, port):
        self.server = StreamServer(("127.0.0.1", port), self._handle)
        self.port = port
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

        ip = sock.getsockname()[0]

        # Handle data
        try:
            for line in self.handleRequest(data, ip, self.port):
                if line is None:
                    line = []
                elif isinstance(line, tuple):
                    line = list(line)
                elif not isinstance(line, list):
                    line = [line]

                # Handle empty lines
                if len(line) == 0:
                    line = ["i"]

                # Fill till the end
                while len(line) < 3:
                    line.append("")
                # Add IP/port
                if len(line) < 5:
                    line += [ip, self.port]

                line = line[0] + "\t".join(map(str, line[1:]))

                sock.send(line + "\r\n")
            sock.send(".\r\n")
        finally:
            self.log.debug("Closing connection with %s:%s" % (addr[0], addr[1]))
            sock.close()


    def handleRequest(self, path, ip, port):
        try:
            for line in GopherHandler(ip, port).route(path):
                yield line
        except Exception as e:
            # Report exceptions as server errors
            yield "i", "Internal Server Error"
            yield
            formatted = traceback.format_exc(e)
            for line in formatted.split("\n"):
                yield "i", line.replace("\t", "    ")
            yield
            yield "1", "Return home", ""
            self.log.error(formatted)
            return