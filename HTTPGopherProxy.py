def format(text):
    gopherText = ""

    return """
        Welcome to HTTP Gopher proxy!
        <hr>
        <pre>
        %s
        </pre>
        <hr>
        See you later!
    """ % text

    for line in text.split():
        gophertype = line[0]
        parts = line[1:].split('\t')

        title = parts[0] if len(parts) >= 1 else ""
        location = parts[1] if len(parts) >= 2 else ""
        host = parts[2] if len(parts) >= 3 else ""
        port = parts[3] if len(parts) >= 4 else ""

        if gophertype == "i":
            gopherText += "%s<br>\n" % title
        elif gophertype == "1":
            gopherText += "<a href=''>%s/ - %s %s<br>\n" % (title, host, port)
        else:
            gopherText += "%s<br>\n" % line

    return """
Welcome to HTTP Gopher proxy!
<hr>
%s
<hr>
See you later!
    """ % gopherText