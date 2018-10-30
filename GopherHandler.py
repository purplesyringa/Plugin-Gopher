from Site import SiteManager
from User import UserManager
from Config import config


class GopherHandler(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self._user = None

    def getUser(self):
        if not self._user:
            self._user = UserManager.user_manager.get()
            if not self._user:
                self._user = UserManager.user_manager.create()
        return self._user

    def route(self, path):
        path = path.strip("/")

        # Defaults:
        type = "1"
        search = ""
        if "/" in path:
            # We have type and path
            _, path = path.split("/", 1)
        if "/" in path:
            # We also have search string
            path, search = path.split("/", 1)

        if search != "":
            # Search isn't supported
            yield "3", "Search is not supported yet."
            return

        if path == "":
            # Homepage
            for line in self.actionHomepage():
                yield line
        else:
            yield "3", "404 File Not Found"


    def actionHomepage(self):
        yield "i", "Welcome to ZeroNet Gopher proxy!"
        yield "i", "Site list follows:"

        # Get site info
        sites = {}
        for address, site in SiteManager.site_manager.sites.iteritems():
            # Try to get site title
            try:
                content_json = site.content_manager.contents["content.json"]
                title = content_json["title"]
                sites[address] = title
            except:
                pass

        # Print favorited sites
        yield
        yield "i", "Favorited sites"
        yield "i", "---------------"
        zerohello_settings = self.getUser().sites[config.homepage].get("settings", {})
        favorites = zerohello_settings.get("favorite_sites", {}).keys()
        for address in favorites:
            yield "1", sites.get(address, address), "/" + address

        # Print other sites
        yield
        yield "i", "Sites"
        yield "i", "-----"
        for address in sites.keys():
            if address not in favorites:
                yield "1", sites.get(address, address), "/" + address

        # Footer
        yield
        yield
        yield "i", "We believe in open, free, and uncensored network and communication."