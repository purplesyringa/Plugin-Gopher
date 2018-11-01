def format(text, path, ip, port):
    from Config import config
    import urllib

    zn_ui_port = config.ui_port

    gopher_text = u""

    for line in text.decode("utf8").split("\r\n"):
        if line == "" or line == ".":
            continue
        gophertype = line[0]
        parts = line[1:].split('\t')

        title = parts[0] if len(parts) >= 1 else u""
        title = title.replace("    ", "&nbsp;&nbsp;&nbsp;&nbsp;").replace("<", "&lt;").replace(">", "&gt;").replace("\\", "\\\\")

        location = urllib.quote(parts[1]) if len(parts) >= 2 else ""
        host = parts[2] if len(parts) >= 3 else ip
        port = parts[3] if len(parts) >= 4 else port

        if gophertype == "i":
            gopher_text += u"%s<br>\n" % title
        elif gophertype == "3":
            gopher_text += u"<strong>ERR</strong> <em style='color: red'>%s</em><br>\n" % title
        elif gophertype == "1":
            if location.startswith("URL:") or location.startswith("GET "):
                gopher_text += u"<img src='/I/gophermedia/web.png'> <a href='%s'>%s</a> &lt;WEB&gt;<br>\n" % (location[4:], title)
            else:
                gopher_text += u"<img src='/I/gophermedia/dir.png'> <a href='//%s:%s/1%s'>%s/</a><br>\n" % (host, port, location, title)
        elif gophertype == "7":
            gopher_text += u"<img src='/I/gophermedia/inp.png'> %s &lt;INP&gt;<br>\n" % title
            gopher_text += u"<input type='text' id='search_%s' name='search_%s'>" % (title.replace(" ", "_"), title.replace(" ", "_"))
        elif gophertype in "02456789gITs":
            desc = {
                "0": "TXT",
                "2": "CCSO",
                "4": "HQC",
                "5": "DOS",
                "6": "UUE",
                "8": "TLN",
                "9": "BIN",
                "g": "GIF",
                "I": "IMG",
                "T": "3270",
                "s": "SND"
            }[gophertype]
            gopher_text += u"<img src='/I/gophermedia/%s.png'> <a href='//%s:%s/%s%s'>%s</a> &lt;%s&gt;<br>\n" % (desc.lower(), host, port, gophertype, location, title, desc)
        elif gophertype == "h":
            gopher_text += u"<img src='/I/gophermedia/html.png'> <a href='//%s:%s/h%s'>%s</a> &lt;HTML&gt; <strong>(No sandbox)</strong><br>\n" % (host, port, location, title)
        else:
            gopher_text += u"%s<br>\n" % line

    return "text/html; charset=UTF-8", ("""
<link rel="stylesheet" type="text/css" href="/0/gophermedia/gopher.css"></link>
Welcome to HTTP Gopher proxy!
<hr>
<pre>
%s
</pre>
<hr>
See you later!
    """ % gopher_text).encode("utf8")
