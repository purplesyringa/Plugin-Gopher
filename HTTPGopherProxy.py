def format(text, path_gopher_type, path, ip, port):
    from Config import config
    import urllib

    # TODO(Christian): Kinda hacky. In _handle, the gophertype is removed from the path
    # We need the gophertype from the path to implement an input that correctly displays
    # the current path
    if path.startswith("gopher://"):
        path_parts = path.replace("gopher://", "").split("/", 2)
        host = path_parts[0]
        selector = path_parts[2] if len(path_parts) > 2 else path_parts[1]
        path = "gopher://" + host + "/" + path_gopher_type + "/" + selector
    else:
        path = path_gopher_type + ("" if path.startswith("/") else "/") +  path

    gopher_text = u""

    for line in text.decode("utf8").split("\r\n"):
        if line == "" or line == ".":
            continue
        gophertype = line[0]
        parts = line[1:].split('\t')

        title = parts[0] if len(parts) >= 1 else u""
        title = title.replace(" ", "&nbsp;").replace("<", "&lt;").replace(">", "&gt;")

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
            if gophertype == "8":
                location = "telnet://%s:%s/%s" % (host, port, location)
            else:
                location = "/gopher://%s:%s/%s%s" % (host, port, gophertype, location)
        else:
            # Local
            host = parts[2] if len(parts) >= 3 else ip
            port = parts[3] if len(parts) >= 4 else port
            if gophertype == "8":
                location = "telnet://%s:%s/%s" % (host, port, location)
            else:
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
            gopher_text += u"<img src='/I/gophermedia/%s.png'> <a href='%s'>%s</a> &lt;%s&gt;<br>\n" % (desc.lower(), location, title, desc)
        elif gophertype == "h":
            gopher_text += u"<img src='/I/gophermedia/html.png'> <a href='%s'>%s</a> &lt;HTML&gt; <strong>(No sandbox)</strong><br>\n" % (location, title)
        elif gophertype in "pd;w": # Potential gophertypes - their meaning and use not yet confimed
            gopher_text += u"<img src='/I/gophermedia/bin.png'> <a href='%s'>%s</a><br>\n" % (location, title)
        else:
            gopher_text += u"%s<br>\n" % line

    return "text/html; charset=UTF-8", ("""
<link rel="stylesheet" type="text/css" href="/0/gophermedia/gopher.css"></link>
<div id="header">
    <div style="max-width: 1000px; margin: auto;">
        <div style="display: inline-block; margin-top: calc(calc(25px - 16px) / 2);">
            HTTP Proxy for ZeroNet Gopher
        </div>
        <div style="float: right;">
            <input type="text" placeholder="Gopher URL" id="input" value="%s" style="margin-left: 10px; width: 250px;" onkeypress="keypress_goto(event)">
            <button onclick="btn_goto()">Go</button>
            <button onclick="btn_search()">V2 Search</button>
        </div>
        <div style="clear: both;"></div>
    </div>
</div>
<div id="content">
%s
</div>
<script>
    function keypress_goto(e) {
        if (e.keyCode === 13) {
            e.preventDefault();
            window.location.href = "/" + document.getElementById('input').value;
        }
    }

    function btn_goto() {
        inputVal = document.getElementById('input').value;
        window.location.href = "/" + inputVal;
    }

    function btn_search() {
        window.location.href = "/gopher://gopher.floodgap.com:70/7/v2/vs?search=" + document.getElementById('input').value;
    }
</script>
""" % (path, gopher_text)).encode("utf8")
