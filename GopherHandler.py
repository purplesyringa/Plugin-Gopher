from Site import SiteManager
from User import UserManager
from Config import config
from gutil import ServeFile, getReSafety, getContentType
from evaluate import evaluate, evaluateCode, GopherFunction, GasHolder
from footer import footer
from Plugin import PluginManager
import re
import os
import gevent


@PluginManager.acceptPlugins
class GopherHandler(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self._user = None
        self.gas_holder = GasHolder(config.gopher_gas)

    def getUser(self):
        if not self._user:
            self._user = UserManager.user_manager.get()
            if not self._user:
                self._user = UserManager.user_manager.create()
        return self._user

    def route(self, path):
        path = path.replace("\\", "/")  # Fix gopher-client bug

        # Defaults:
        search = ""
        if "\t" in path:
            # Search string
            path, search = path.split("\t", 1)
        path = path.strip("/")

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

            for line in self.actionSite(address, path, search):
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


    def actionSite(self, address, path, search):
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
                    for line in self.actionSiteRouter(site, matches, search, rules[rule]):
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
        else:
            if not site.storage.isFile(path):
                # Try to download the file
                if not site.needFile(path, priority=15):
                    yield "i", "404 File Not Found"
                    yield "i", "Could not find file %s." % path
                    yield
                    yield "1", "Return home", "/"
                    return
            # Serve the file
            file = site.storage.open(path)
            size = site.storage.getSize(path)
            raise ServeFile(file, os.path.basename(path), size)


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
                mime = getContentType(filename, prefix)
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


    def actionSiteRouter(self, site, matches, search, actions):
        # Expose some site information as variables
        matches["site_address"] = site.address
        # TODO(Christian): May want to move this somewhere else?
        content = site.content_manager.contents.get("content.json")
        matches["site_title"] = content["title"]
        matches["site_description"] = content["description"]
        matches["site_peers"] = str(len(site.peers))
        matches["search"] = search

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
                return evaluate(s, matches, self.gas_holder)
            else:
                return str(s)

        for action in actions:
            if isinstance(action, list):
                # We just yield the arrays
                self.gas_holder.needGas(1)
                action = [
                    (
                        replaceVars(part)
                        if isinstance(part, (str, unicode)) else part
                    ) for part in action
                ]
                yield action
            elif isinstance(action, (str, unicode)):
                # Treat strings as info
                self.gas_holder.needGas(1)
                yield "i", replaceVars(action.replace("\t", "    "))
            elif isinstance(action, dict):
                # Handle specific keys
                if "break" in action:
                    break
                elif "include" in action:
                    # Switch to another rule/address and then return back
                    self.gas_holder.needGas(1)
                    for line in self.route(action["redirect"]):
                        yield line
                elif "redirect" in action:
                    # Switch to another rule/address (same as include + break)
                    self.gas_holder.needGas(1)
                    for line in self.route(action["redirect"]):
                        yield replaceVars(line)
                    break
                elif "sql" in action:
                    # Use each row as an individual line
                    self.gas_holder.needGas(5)
                    for row in site.storage.query(action["sql"], matches):
                        yield row
                elif "sql_foreach" in action:
                    self.gas_holder.needGas(7)
                    for row in site.storage.query(action["sql_foreach"], matches):
                        for line in self.actionSiteRouter(site, dict(row), action["do"]):
                            yield line
                elif "re_foreach" in action:
                    # List of actions -- search all matches and execute
                    self.gas_holder.needGas(3)
                    pattern = replaceVars(action["re_foreach"])
                    self.gas_holder.needGas(getReSafety(pattern))
                    for row in re.finditer(pattern, replaceVars(action["in"])):
                        # Match object to dict
                        row_dict = row.groupdict()
                        for i, value in enumerate(row.groups()):
                            row_dict[str(i + 1)] = value
                        row_dict["0"] = row.group(0)
                        # Do
                        for line in self.actionSiteRouter(site, row_dict, action["do"]):
                            yield line
                elif "var" in action:
                    self.gas_holder.needGas(1)
                    matches[action["var"]] = self.handleGopherDefinition(action, matches)
                elif "do" in action:
                    self.gas_holder.needGas(1)
                    evaluateCode(action["do"], matches, self.gas_holder, no_result=True)


    def actionSiteGophermap(self, address, path):
        site = SiteManager.site_manager.get(address)
        with site.storage.open(path) as f:
            for line in f:
                if line == "":
                    yield
                    continue


                gophertype = line[0]
                sections = line[1:].split("\t")
                if gophertype not in "0123456789+:;<IMPTdghips":
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
    

    def handleGopherDefinition(self, value, matches):
        def replaceVars(s):
            if isinstance(s, (str, unicode)):
                return evaluate(s, matches, self.gas_holder)
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
                    return GopherFunction(value[key], arg_names, self.gas_holder)
                elif key == "= f":
                    return GopherFunction(value[key], [], self.gas_holder)
        return None


    def actionGophermedia(self, *path):
        curdir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(curdir, "media", *path)
        try:
            f = open(path, "rb")
        except IOError:
            yield "i", "IOError"
            return
        raise ServeFile(f, os.path.basename(path), os.path.getsize(path))