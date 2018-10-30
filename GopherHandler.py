from Site import SiteManager
from User import UserManager
from Config import config
import os
import mimetypes
import string


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
        path = path.replace("\\", "/")  # Fix gopher-client bug
        path = path.strip("/")

        # Defaults:
        search = ""
        if "%09" in path:
            # Search string
            path, search = path.split("%09", 1)

        if search != "":
            # Search isn't supported
            yield "3", "Search is not supported yet."
            return

        if path == "":
            # Homepage
            for line in self.actionHomepage():
                yield line
        else:
            # Site directory
            if "/" in path:
                address, path = path.split("/", 1)
            else:
                address, path = path, ""

            for line in self.actionSite(address, path):
                yield line

        # Footer
        yield
        yield
        yield "i", "We believe in open, free, and uncensored network and communication."


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
                title = title.replace("\t", "    ")  # Fix tabs
                title = title.replace("\r", " ")  # Fix linebreaks
                title = title.replace("\n", " ")
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


    def actionSite(self, address, path):
        site = SiteManager.site_manager.get(address)
        if not site:
            yield "i", "404 File Not Found"
            yield
            yield "i", "Site %s is not downloaded." % address
            return

        for filename in site.storage.list(path):
            # Probably check for dir/file here?
            abspath = os.path.join(path, filename)
            if site.storage.isDir(abspath):
                # Directory
                yield "1", filename, "/%s/%s" % (address, abspath)
            elif site.storage.isFile(abspath):
                # HTML/text/binary
                try:
                    with site.storage.open(abspath) as f:
                        prefix = f.read(512)
                    mime = self.getContentType(filename, prefix)
                except:
                    mime = "application/octet-stream"

                if mime == "text/html":
                    yield "h", filename, "/%s/%s" % (address, abspath)
                elif mime.startswith("text/") or mime in ("application/json",):
                    yield "0", filename, "/%s/%s" % (address, abspath)
                else:
                    yield "9", filename, "/%s/%s" % (address, abspath)
            else:
                # Neither directory nor file
                yield "1", filename + " [???]", "/%s/%s" % (address, abspath)


    def getContentType(self, file_name, prefix):
        if file_name.endswith(".css"):  # Force correct css content type
            return "text/css"
        content_type = mimetypes.guess_type(file_name)[0]
        if content_type:
            return content_type.lower()

        # Try to guess (thanks to Thomas)
        # https://stackoverflow.com/a/1446870/5417677
        text_characters = "".join(map(chr, range(32, 127))) + "\n\r\t\b"
        null_trans = string.maketrans("", "")
        if not prefix:
            # Empty files are considered text
            return "text/plain"
        if "\0" in prefix:
            # Files with null bytes are likely binary
            return "application/octet-stream"
        # Get the non-text characters (maps a character to itself then
        # use the 'remove' option to get rid of the text characters).
        non_txt = prefix.translate(null_trans, text_characters)
        # If more than 30% non-text characters, then
        # this is considered a binary file
        if float(len(non_txt)) / float(len(prefix)) > 0.30:
            return "application/octet-stream"
        else:
            return "text/plain"