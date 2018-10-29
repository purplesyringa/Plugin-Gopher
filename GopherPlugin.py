from GopherServer import GopherServer
from Plugin import PluginManager

@PluginManager.afterLoad
def importPluginnedClasses():
    from Config import config
    global config

@PluginManager.registerTo("UiServer")
class UiServer(object):
    def start(self):
        # First, start GopherServer
        port = config.gopher_port
        max_connections = config.gopher_max_conn
        server = GopherServer(port=port, max_connections=max_connections)
        server.start()

        # Now start UiServer itself
        super(UiServer, self).start()

@PluginManager.registerTo("ConfigPlugin")
class ConfigPlugin(object):
    def createArguments(self):
        group = self.parser.add_argument_group("Gopher plugin")
        group.add_argument("--gopher_port", help="The port to listen on", default=70, type=int)
        group.add_argument("--gopher_max_conn", help="Maximum concurrent connections", default=128, type=int)

        return super(ConfigPlugin, self).createArguments()