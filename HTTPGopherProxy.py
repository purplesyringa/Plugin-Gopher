def format(text, path, gopher_type, ip, port):
    return "text/html", """
        Welcome to HTTP Gopher proxy! You're browsing type gopher://%s:%s/%s%s
        <hr>
        <pre>
        %s
        </pre>
        <hr>
        See you later!
    """ % (ip, port, gopher_type, path, text)