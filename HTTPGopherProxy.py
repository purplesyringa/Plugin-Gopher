def format(text, path, ip, port):
    from Config import config
    import urllib

    gopher_text = u""

    for line in text.decode("utf8").split("\r\n"):
        if line == "" or line == ".":
            continue
        gophertype = line[0]
        parts = line[1:].split('\t')

        title = parts[0] if len(parts) >= 1 else u""
        title = title.replace("    ", "&nbsp;&nbsp;&nbsp;&nbsp;").replace("<", "&lt;").replace(">", "&gt;").replace("\\", "\\\\")

        location = urllib.quote(parts[1]) if len(parts) >= 2 else ""

        is_web = False
        if parts[1].startswith("URL:"):
            # Clearnet
            location = parts[1][len("URL:"):]
            is_web = True
        elif path.startswith("gopher://"):
            # Proxy
            host = parts[2] if len(parts) >= 3 else "(null.host)"
            port = parts[3] if len(parts) >= 4 else 70
            location = "/gopher://%s:%s/%s%s" % (host, port, gophertype, location)
        else:
            # Local
            host = parts[2] if len(parts) >= 3 else ip
            port = parts[3] if len(parts) >= 4 else port
            location = "/" + gophertype + location

        if gophertype == "i":
            gopher_text += u"%s<br>\n" % title
        elif gophertype == "3":
            gopher_text += u"<strong>ERR</strong> <em style='color: red'>%s</em><br>\n" % title
        elif is_web:
            gopher_text += u"<img src='/I/gophermedia/web.png'> <a href='%s'>%s</a> &lt;WEB&gt;<br>\n" % (location, title)
        elif gophertype == "1":
            gopher_text += u"<img src='/I/gophermedia/dir.png'> <a href='%s'>%s/</a><br>\n" % (location, title)
        elif gophertype == "7":
            gopher_text += u"<img src='/I/gophermedia/inp.png'> %s<br>\n" % title
            gopher_text += u"<form action='%s'>" % location
            gopher_text += u"<img src='/I/gophermedia/blank.png'>"
            gopher_text += u"<img src='/I/gophermedia/inp2.png'> "
            gopher_text += u"<input type='text' id='search_%s' name='search'>" % title.replace(" ", "_")
            gopher_text += u"</form>"
        elif gophertype == "8":
            gopher_text += u"<img src='/I/gophermedia/TLN.png'> <a href='telnet://%s'>%s</a> &lt;TLN&gt;<br>\n" % (location, title)
        elif gophertype in "0245679gITs":
            desc = {
                "0": "TXT",
                "2": "CCSO",
                "4": "HQC",
                "5": "DOS",
                "6": "UUE",
                #"8": "TLN",
                "9": "BIN",
                "g": "GIF",
                "I": "IMG",
                "T": "3270",
                "s": "SND"
            }[gophertype]
            gopher_text += u"<img src='/I/gophermedia/%s.png'> <a href='%s'>%s</a> &lt;%s&gt;<br>\n" % (desc.lower(), location, title, desc)
        elif gophertype == "h":
            gopher_text += u"<img src='/I/gophermedia/html.png'> <a href='%s'>%s</a> &lt;HTML&gt; <strong>(No sandbox)</strong><br>\n" % (location, title)
        else:
            gopher_text += u"%s<br>\n" % line

    return "text/html; charset=UTF-8", ("""
<link rel="stylesheet" type="text/css" href="/0/gophermedia/gopher.css"></link>
Welcome to HTTP Gopher proxy!
<hr>
<div id="content">
%s
</div>
""" % gopher_text).encode("utf8")
