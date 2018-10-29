from SocketServer import SocketServer

class GopherServer(SocketServer):
    def handleRequest(self, data):
        self.log.debug("Received: %s" % data)

        return "iHello, world!\r\n.\r\n"