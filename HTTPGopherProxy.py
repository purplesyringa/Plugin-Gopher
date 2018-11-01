def format(text, path, ip, port):
    from Config import config

    zn_ui_port = config.ui_port

    gopherText = ""

    for line in text.split("\r\n"):
        if line == "" or line == ".":
            continue
        gophertype = line[0]
        parts = line[1:].split('\t')

        title = parts[0] if len(parts) >= 1 else ""
        title = title.replace("    ", "&nbsp;&nbsp;&nbsp;&nbsp;").replace("<", "&lt;").replace(">", "&gt;").replace("\\", "\\\\")

        location = parts[1] if len(parts) >= 2 else ""
        host = parts[2] if len(parts) >= 3 else ip
        port = parts[3] if len(parts) >= 4 else port

        if gophertype == "i":
            gopherText += "%s<br>\n" % title
        elif gophertype == "3":
            gopherText += "<strong>ERR</strong> <em style='color: red'>%s</em><br>\n" % title
        elif gophertype == "1":
            if location.startswith("URL:") or location.startswith("GET "):
                gopherText += "<img src='/I/gophermedia/web.png'> <a href='%s'>%s</a> &lt;WEB&gt;<br>\n" % (location[4:], title)
            else:
                gopherText += "<img src='/I/gophermedia/dir.png'> <a href='//%s:%s/1%s'>%s/</a><br>\n" % (host, port, location, title)
        elif gophertype in "02456789gITs":
            desc = {
                "0": "TXT",
                "2": "CCSO",
                "4": "HQC",
                "5": "DOS",
                "6": "UUE",
                "7": "INP",
                "8": "TLN",
                "9": "BIN",
                "g": "GIF",
                "I": "IMG",
                "T": "3270",
                "s": "SND"
            }[gophertype]
            gopherText += "<img src='/I/gophermedia/%s.png'> <a href='//%s:%s/%s%s'>%s</a> &lt;%s&gt;<br>\n" % (desc.lower(), host, port, gophertype, location, title, desc)
        elif gophertype == "h":
            gopherText += "<img src='/I/gophermedia/html.png'> <a href='//%s:%s/h%s'>%s</a> &lt;HTML&gt; <strong>(No sandbox)</strong><br>\n" % (host, port, location, title)
        else:
            gopherText += "%s<br>\n" % line

    return "text/html", """
<style>body { line-height: 9px; }</style>
Welcome to HTTP Gopher proxy!
<hr>
<pre>
%s
</pre>
<hr>
See you later!
    """ % gopherText
