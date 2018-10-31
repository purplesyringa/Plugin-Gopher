from gevent.server import StreamServer
from GopherHandler import GopherHandler
from gutil import ServeFile
import logging
import traceback
import sys

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

                    def encodeStr(s):
                        return unicode(s).encode("utf8", "ignore")

                    line = encodeStr(line[0]) + "\t".join(map(encodeStr, line[1:]))

                    sock.send(line + "\r\n")
                sock.send(".\r\n")
            except ServeFile as e:
                # Pipe file to socket
                file = e.getServedFile()
                while True:
                    buf = file.read(1024)
                    if buf == "":
                        break
                    sock.send(buf)
        finally:
            self.log.debug("Closing connection with %s:%s" % (addr[0], addr[1]))
            sock.close()


    def handleRequest(self, path, ip, port):
        try:
            for line in GopherHandler(ip, port).route(path):
                yield line
        except ServeFile:
            raise
        except SyntaxError as e:
            # Report exceptions as server errors
            e_type, value, tb = sys.exc_info()

            yield "i", "------------------"
            yield "i", "Invalid expression"
            yield "i", e
            yield
            yield "1", "Return home", "/"
        except:
            # Report exceptions as server errors
            e_type, value, tb = sys.exc_info()

            yield "i", "---------------------"
            yield "i", "Internal Server Error"
            yield

            # Format exception message and traceback
            formatted = traceback.format_exception(e_type, value, tb)
            for line in "".join(formatted).split("\n"):
                yield "i", line.replace("\t", "    ")
                self.log.error(line)

            yield "1", "Return home", "/"