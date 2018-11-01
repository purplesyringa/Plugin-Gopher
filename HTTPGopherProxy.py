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
        elif gophertype == "0":
            gopherText += "<a href='//%s:%s/0%s'>%s</a> &lt;TXT&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "1":
            if location.startswith("URL:") or location.startswith("GET "):
                gopherText += "<a href='%s'>%s</a> &lt;WEB&gt;<br>\n" % (location[4:], title)
            else:
                gopherText += "<a href='//%s:%s/1%s'>%s/</a><br>\n" % (host, port, location, title)
        elif gophertype == "2":
            gopherText += "<a href='//%s:%s/2%s'>%s</a> &lt;CCSO&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "4":
            gopherText += "<a href='//%s:%s/4%s'>%s</a> &lt;HQC&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "5":
            gopherText += "<a href='//%s:%s/5%s'>%s</a> &lt;DOS&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "6":
            gopherText += "<a href='//%s:%s/6%s'>%s</a> &lt;UUE&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "7":
            gopherText += "<a href='//%s:%s/7%s'>%s</a> &lt;INP&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "8":
            gopherText += "<a href='//%s:%s/8%s'>%s</a> &lt;TLN&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "9":
            gopherText += "<a href='//%s:%s/9%s'>%s</a> &lt;BIN&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "g":
            gopherText += "<a href='//%s:%s/g%s'>%s</a> &lt;GIF&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "I":
            gopherText += "<a href='//%s:%s/I%s'>%s</a> &lt;IMG&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "T":
            gopherText += "<a href='//%s:%s/T%s'>%s</a> &lt;3270&gt;<br>\n" % (host, port, location, title)
        elif gophertype == "h":
            gopherText += "<a href='//%s:%s/h%s'>%s</a> &lt;HTML&gt; <strong>(No sandbox)</strong><br>\n" % (host, port, location, title)
        elif gophertype == "s":
            gopherText += "<a href='//%s:%s/s%s'>%s</a> &lt;SND&gt;<br>\n" % (host, port, location, title)
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
