from GopherServer import GopherServer
from Plugin import PluginManager

@PluginManager.afterLoad
def importPluginnedClasses():
    from Config import config
    from handler import handler  # Imports pluginnable SiteManager

    global config, handler

@PluginManager.registerTo("UiServer")
class UiServer(object):
    def start(self):
        # First, start GopherServer
        server = GopherServer(port=config.gopher_port, handler=handler)
        server.start()

        # Now start UiServer itself
        super(UiServer, self).start()

@PluginManager.registerTo("ConfigPlugin")
class ConfigPlugin(object):
    def createArguments(self):
        group = self.parser.add_argument_group("Gopher plugin")
        group.add_argument("--gopher_port", help="The port to listen on", default=7070, type=int)

        return super(ConfigPlugin, self).createArguments()