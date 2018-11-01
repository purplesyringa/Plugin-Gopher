from gevent.server import StreamServer
from GopherHandler import GopherHandler
from gutil import ServeFile, getContentType
import HTTPGopherProxy
import logging
import traceback
import sys
import urllib

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
        ip = sock.getsockname()[0]

        f = sock.makefile()
        first_line = f.readline().rstrip("\r\n")
        gopher_type = "1"  # Assume directory by default
        if first_line.startswith("GET "):
            # Seems like HTTP
            # Read until we get an empty line
            while True:
                line = f.readline().rstrip("\r\n")
                if not line:
                    break
            # Parse HTTP query
            first_line = first_line[4:]
            if first_line.endswith(" HTTP/1.1"):
                first_line = first_line[:-len(" HTTP/1.1")]
            first_line = first_line.lstrip("/")
            if first_line and first_line[0] in "0123456789+:;<IMPTdghips":
                # Valid gopher type
                gopher_type = first_line[0]
                first_line = first_line[1:]
            # Transform search to gopher://-compatible format
            first_line = first_line.replace("?search=", "\t")
            first_line = urllib.unquote(first_line)
            is_http = True
        else:
            is_http = False
        f.close()

        # Handle data
        try:
            if is_http:
                gen = self.handleRequestHTTP(first_line.decode("utf8"), ip, gopher_type)
            else:
                gen = self.handleRequestGopher(first_line.decode("utf8"), ip)

            for part in gen:
                sock.send(part)
        finally:
            protocol = "http://" if is_http else "gopher://"
            self.log.debug("Closing %s connection with %s:%s" % (protocol, addr[0], addr[1]))
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
        except Exception:
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


    def handleRequestGopher(self, data, ip):
        try:
            for part in self.formatGopher(data, ip):
                yield part
        except ServeFile as e:
            # Pipe file to socket
            file = e.getServedFile()
            while True:
                buf = file.read(1024)
                if buf == "":
                    break
                yield buf
            file.close()


    def handleRequestHTTP(self, path, ip, gopher_type):
        try:
            gopher_text = ""
            for part in self.formatGopher(path, ip):
                gopher_text += part
            if gopher_type == "0":
                content_type, response = "text/plain", gopher_text
            elif gopher_type == "4":
                content_type, response = "application/mac-binhex", gopher_text
            elif gopher_type == "5":
                content_type, response = "application/zip", gopher_text
            elif gopher_type == "6":
                content_type, response = "text/x-uuencode", gopher_text
            elif gopher_type in "9I":
                content_type, response = "application/octet-stream", gopher_text
            elif gopher_type == "h":
                content_type, response = "text/html", gopher_text
            elif gopher_type == "g":
                content_type, response = "image/gif", gopher_text
            else:
                content_type, response = HTTPGopherProxy.format(gopher_text, path, ip, self.port)
        except ServeFile as e:
            # Get file
            file = e.getServedFile()
            if gopher_type == "1":
                # In case the mode is 1, we *always* use proxy
                content_type, response = HTTPGopherProxy.format(file.read(), path, ip, self.port)
                file.close()
            else:
                # Detect mime type
                prefix = file.read(512)
                mime_type = getContentType(e.getServedFilename(), prefix)
                # Yield header
                yield "HTTP/1.1 200 OK\r\n"
                yield "Server: Gopher/ZeroNet\r\n"
                yield "Content-Type: %s\r\n" % mime_type
                yield "Content-Length: %s\r\n" % e.getServedFilesize()
                yield "Connection: Closed\r\n"
                yield "\r\n"
                # Yield prefix
                yield prefix
                # Yield rest
                while True:
                    buf = file.read(1024)
                    if buf == "":
                        break
                    yield buf
                file.close()
                return

        # Yield header
        yield "HTTP/1.1 200 OK\r\n"
        yield "Server: Gopher/ZeroNet\r\n"
        yield "Content-Type: %s\r\n" % content_type
        yield "Content-Length: %s\r\n" % len(response)
        yield "Connection: Closed\r\n"
        yield "\r\n"
        # Yield body
        yield response


    def formatGopher(self, data, ip):
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

            yield line + "\r\n"
        yield ".\r\n"