from Plugin import PluginManager

@PluginManager.afterLoad
def importPluginnedClasses():
    from Config import config
    from GopherServer import GopherServer

    global config, GopherServer

@PluginManager.registerTo("UiServer")
class UiServer(object):
    def start(self):
        # First, start GopherServer
        server = GopherServer(port=config.gopher_port)
        server.start()

        # Now start UiServer itself
        super(UiServer, self).start()

@PluginManager.registerTo("ConfigPlugin")
class ConfigPlugin(object):
    def createArguments(self):
        group = self.parser.add_argument_group("Gopher plugin")
        group.add_argument("--gopher_port", help="The port to listen on", default=7070, type=int)
        group.add_argument("--gopher_gas", help="Default gas (smaller is safer)", default=1000, type=int)

        return super(ConfigPlugin, self).createArguments()