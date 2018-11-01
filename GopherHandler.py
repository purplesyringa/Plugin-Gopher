from Site import SiteManager
from User import UserManager
from Config import config
from gutil import ServeFile
from evaluate import evaluate, GopherFunction
from footer import footer
from Plugin import PluginManager
from util import SafeRe
import os
import mimetypes
import string
import gevent


@PluginManager.registerTo("UiRequest")
class UiRequestPlugin(object):
    # HTTP page that explains the Gopher plugin, what Gopher is, and how to use Gopher
    def actionGopher(self):
        from Ui import UiRequest

        self.sendHeader();
        yield "<h3>Gopher ZeroNet Plugin</h3>"
        yield "<hr>"

    # A Gopher HTTP Proxy / Web Client
    def actionGopherClient(self):
        from Ui import UiRequest

        location = self.get["url"] if self.get.get("url") else "127.0.0.1:7070/1/" # TODO(Christian): Use correct ip and port

        self.sendHeader()
        yield "<h3>Gopher Web Client</h3>"
        yield "<p>%s</p>" % location
        yield "<hr>"


@PluginManager.acceptPlugins
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
            yield "i", "Search is not supported yet."
            yield
            yield "1", "Return home", "/"
            return

        if "../" in path or "./" in path or path.endswith("/..") or path.endswith("/.") or path == ".." or path == ".":
            yield "3", "Invalid path"
            return

        if path == "":
            # Homepage
            for line in self.actionHomepage():
                yield line
        elif path.startswith("download/"):
            # Start downloading the file
            _, gopher_type, address, path = path.split("/", 3)

            for line in self.actionDownload(gopher_type, address, path):
                yield line
        else:
            # Site directory
            if "/" in path:
                address, path = path.split("/", 1)
            else:
                address, path = path, ""

            if not SiteManager.site_manager.isAddress(address):
                # Try to route
                args = path.split("/") if path else []
                f = getattr(self, "action" + address[0].upper() + address[1:], None)
                if f:
                    for line in f(*args):
                        yield line
                else:
                    yield "i", "Unknown remote path /%s" % address
                    yield
                    yield "1", "Return home", "/"
                return

            for line in self.actionSite(address, path):
                if isinstance(line, (tuple, list)) and line[0].startswith("z"):
                    # z-link
                    gopher_type = line[0][1:]
                    fileaddress, filepath = line[2].strip("/").split("/", 1)
                    # Check whether the file is downloaded
                    site = SiteManager.site_manager.get(fileaddress)
                    if site.storage.isFile(filepath):
                        # Show direct link
                        line = list(line)
                        line[0] = gopher_type
                        yield line
                    else:
                        # Show link to download page
                        yield "1", line[1], "/" + os.path.join("download", gopher_type, fileaddress, filepath)
                else:
                    yield line

        # Footer
        if footer != []:
            yield
            yield
            for line in footer:
                yield line


    def actionHomepage(self):
        yield "i", "Welcome to ZeroNet Gopher proxy!"
        yield "i", "Site list follows:"

        # Get site info
        sites = {}
        merged_types = {}
        is_merged = {}
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
                sites[address] = address

            if "merged_type" in content_json:
                merged_type = content_json["merged_type"]
                if merged_type not in merged_types:
                    merged_types[merged_type] = []
                merged_types[merged_type].append(address)
                is_merged[address] = True

        # Print favorited sites
        yield
        yield "i", "Favorited sites"
        yield "i", "---------------"
        zerohello_settings = self.getUser().sites[config.homepage].get("settings", {})
        favorites = zerohello_settings.get("favorite_sites", {}).keys()
        for address in sorted(favorites, key=lambda address: sites.get(address, "")):
            if address not in sites:
                # Skip deleted sites
                continue
            title = sites[address]
            yield "1", title, "/" + address

        # Print other sites
        yield
        yield "i", "Connected sites"
        yield "i", "---------------"
        for address in sorted(sites.keys(), key=lambda address: sites[address]):
            if address not in favorites and not is_merged.get(address):
                title = sites[address]
                yield "1", title, "/" + address
        
        # Print hubs
        for merged_type, merged_sites in merged_types.iteritems():
            header = "Merged: %s" % merged_type
            yield
            yield "i", header
            yield "i", "-" * len(header)
            for address in sorted(merged_sites, key=lambda address: sites[address]):
                title = sites[address]
                yield "1", title, "/" + address


    def actionSite(self, address, path):
        site = SiteManager.site_manager.get(address)
        if not site:
            gevent.spawn(SiteManager.site_manager.need, address)

            yield "i", "Downloading site..."
            yield "i", "Refresh to see the result."
            return


        # Try to route via content.json rules
        if site.storage.isFile("gopher.json"):
            rules = site.storage.loadJson("gopher.json")["rules"]
            split_path = path.split("/")
            for rule in rules.iterkeys():
                # a/b/:c/:d/e
                # "a" is just a match
                # ":c" means anything, remember to "c" variable
                split_rule = rule.split("/")

                if len(split_path) != len(split_rule):
                    # Length mismatch
                    continue

                matches = {}
                for i, part in enumerate(split_path):
                    expected_part = split_rule[i]
                    if expected_part.startswith(":"):
                        # Save to variable
                        matches[expected_part[1:]] = part
                    elif expected_part == "*":
                        # Anything
                        pass
                    else:
                        # Full match
                        if expected_part != part:
                            break
                else:
                    # Matched! Handle the result
                    for line in self.actionSiteRouter(site, matches, rules[rule]):
                        yield line
                    return


        if site.storage.isDir(path):
            # TODO: Or when text/any file is served as gophertype 1
            if site.storage.isFile(os.path.join(path, "gophermap")):
                # Serve gophermap
                for line in self.actionSiteGophermap(address, os.path.join(path, "gophermap")):
                    yield line
            else:
                # Serve directory
                for line in self.actionSiteDir(address, path):
                    yield line
        elif site.storage.isFile(path):
            # Serve the file
            file = site.storage.open(path)
            raise ServeFile(file)
        else:
            # Try to download the file
            result = site.needFile(path, priority=15)
            if result:
                # Download complete
                file = site.storage.open(path)
                raise ServeFile(file)
            else:
                yield "i", "404 File Not Found"
                yield "i", "Could not find file %s." % path
                yield
                yield "1", "Return home", "/"


    def actionSiteDir(self, address, path):
        # Render directory list
        site = SiteManager.site_manager.get(address)

        dirs = []
        files = []

        for filename in site.storage.list(path):
            abspath = os.path.join(path, filename)
            if site.storage.isDir(abspath):
                # Directory
                dirs.append(filename)
            elif site.storage.isFile(abspath):
                # File
                files.append(filename)

        # ..
        if path == "":
            yield "1", "..", "/"
        elif "/" not in path:
            yield "1", "..", "/%s" % address
        else:
            parent, _ = path.rsplit("/", 1)
            yield "1", "..", "/%s/%s" % (address, parent)

        # First, show directories
        for filename in sorted(dirs):
            abspath = os.path.join(path, filename)
            yield "1", filename, "/%s/%s" % (address, abspath)

        # Now show files
        for filename in sorted(files):
            # HTML/text/binary
            abspath = os.path.join(path, filename)
            try:
                with site.storage.open(abspath) as f:
                    prefix = f.read(512)
                mime = self.getContentType(filename, prefix)
            except:
                mime = "application/octet-stream"

            if mime == "text/html":
                yield "h", filename, "/%s/%s" % (address, abspath)
            elif mime.startswith("text/") or mime in ("application/json", "application/javascript"):
                yield "0", filename, "/%s/%s" % (address, abspath)
            elif mime == "image/gif":
                yield "g", filename, "/%s/%s" % (address, abspath)
            elif mime.startswith("image/"):
                yield "I", filename, "/%s/%s" % (address, abspath)
            else:
                yield "9", filename, "/%s/%s" % (address, abspath)


    def actionSiteRouter(self, site, matches, actions):
        # Expose some site information as variables
        matches["site_address"] = site.address
        # TODO(Christian): May want to move this somewhere else?
        content = site.content_manager.contents.get("content.json")
        matches["site_title"] = content["title"]
        matches["site_description"] = content["description"]
        matches["site_peers"] = str(len(site.peers))

        for name, value in site.storage.loadJson("gopher.json").get("global", {}).iteritems():
            if name not in matches:
                matches[name] = self.handleGopherDefinition(value, matches)

        if "sql_prepared" not in matches:
            def doSqlPrepared(query, matches):
                rows = []
                for row in site.storage.query(query, matches):
                    rows.append(dict(row))
                return rows
            matches["sql_prepared"] = doSqlPrepared
        if "sql" not in matches:
            def doSql(query):
                rows = []
                for row in site.storage.query(query):
                    rows.append(dict(row))
                return rows
            matches["sql"] = doSql

        def replaceVars(s):
            if isinstance(s, (str, unicode)):
                return evaluate(s, matches)
            else:
                return str(s)

        for action in actions:
            if isinstance(action, list):
                # We just yield the arrays
                action = [
                    (
                        replaceVars(part)
                        if isinstance(part, (str, unicode)) else part
                    ) for part in action
                ]
                yield action
            elif isinstance(action, (str, unicode)):
                # Treat strings as info
                yield "i", replaceVars(action.replace("\t", "    "))
            elif isinstance(action, dict):
                # Handle specific keys
                if "break" in action:
                    break
                elif "include" in action:
                    # Switch to another rule/address and then return back
                    for line in self.route(action["redirect"]):
                        yield line
                elif "redirect" in action:
                    # Switch to another rule/address (same as include + break)
                    for line in self.route(action["redirect"]):
                        yield replaceVars(line)
                    return
                elif "sql" in action:
                    # Use each row as an individual line
                    for row in site.storage.query(action["sql"], matches):
                        row = list(row)

                        # NOTE(Christian): Handle new lines in the Display Text of the row
                        # All new lines after the first will use the text gophertype
                        additionalRows = []

                        if len(row) == 1:
                            row = ["i"] + row
                        text = row[1].replace("\r", "")
                        location = row[2] if len(row) >= 3 else ""
                        host = row[3] if len(row) >= 4 else ""
                        port = row[4] if len(row) >= 5 else ""

                        part_lines = text.split("\n")
                        row[1] = part_lines[0]

                        for line in part_lines[1:]:
                            additionalRows.append(["i", line, location, host, port])

                        # Yield the row and any additional rows due to new lines
                        yield row

                        for additional_row in additionalRows:
                            yield additional_row
                elif "sql_foreach" in action:
                    for row in site.storage.query(action["sql_foreach"], matches):
                        for line in self.actionSiteRouter(site, dict(row), action["do"]):
                            yield line
                elif "re_foreach" in action:
                    # List of actions -- search all matches and execute
                    pattern = replaceVars(action["re_foreach"])
                    for row in SafeRe.finditer(pattern, replaceVars(action["in"])):
                        # Match object to dict
                        row_dict = row.groupdict()
                        for i, value in enumerate(row.groups()):
                            row_dict[str(i + 1)] = value
                        row_dict["0"] = row.group(0)
                        # Do
                        for line in self.actionSiteRouter(site, row_dict, action["do"]):
                            yield line
                elif "var" in action:
                    matches[action["var"]] = self.handleGopherDefinition(action, matches)


    def actionSiteGophermap(self, address, path):
        site = SiteManager.site_manager.get(address)
        with site.storage.open(path) as f:
            for line in f:
                if line == "":
                    yield
                    continue


                gophertype = line[0]
                sections = line[1:].split("\t")
                if gophertype not in "0123456789ihI":
                    # Assume plain text if gophertype is invalid
                    gophertype = "i"
                    sections = [line]

                title = sections[0] if len(sections) >= 1 else ""
                location = sections[1] if len(sections) >= 2 else ""
                host = sections[2] if len(sections) >= 3 else ""
                port = sections[3] if len(sections) >= 4 else ""

                yield gophertype, title, location, host, port


    def actionDownload(self, gopher_type, address, path):
        site = SiteManager.site_manager.get(address)

        if site.storage.isFile(path):
            filename = os.path.basename(path)
            yield "i", "File is downloaded."
            yield
            yield gopher_type, filename, "/%s/%s" % (address, path)
        else:
            gevent.spawn(site.needFile, path, priority=15)
            yield "i", "Downloading file %s." % path
            yield "i", "Refresh to get the result."


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
    

    def handleGopherDefinition(self, value, matches):
        def replaceVars(s):
            if isinstance(s, (str, unicode)):
                return evaluate(s, matches)
            else:
                return str(s)

        if "=" in value:
            return replaceVars(value["="])
        elif "= int" in value:
            return replaceVars(int(value["= int"]))
        elif "= float" in value:
            return replaceVars(float(value["= float"]))
        elif "= str" in value:
            return replaceVars(str(value["= str"]))
        elif any((key.startswith("= f(") for key in value.iterkeys())):
            for key in value.iterkeys():
                if key.startswith("= f("):
                    # Function definition
                    arg_names = [
                        arg.strip().replace(":", "")
                        for arg in key.replace("= f(", "")[:-1].split(",")
                        if arg.strip()
                    ]
                    return GopherFunction(value[key], arg_names)
                elif key == "= f":
                    return GopherFunction(value[key], [])
        return None