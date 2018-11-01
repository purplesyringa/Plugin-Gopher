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
        elif gophertype == "0":
            gopherText += "<a href='//%s:%s/0%s'>%s</a> &lt;TXT&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "1":
            gopherText += "<a href='//%s:%s/1%s'>%s/</a><br>\n" % (host, port, location, title)
        elif gophertype == "9":
            gopherText += "<a href='//%s:%s/9%s'>%s</a> &lt;BIN&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "I":
            gopherText += "<a href='//%s:%s/I%s'>%s</a> &lt;IMG&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "h":
            gopherText += "<a href='//%s:%s%s'>%s</a> &lt;HTML&gt;<br>\n" % (host, zn_ui_port, location, title)
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
