import mimetypes
import string


class ServeFile(Exception):
    def __init__(self, file, filename, filesize):
        super(ServeFile, self).__init__("Serving file %s (%sb)" % (filename, filesize))
        self.__file = file
        self.__filename = filename
        self.__filesize = filesize

    def getServedFile(self):
        return self.__file
    def getServedFilename(self):
        return self.__filename
    def getServedFilesize(self):
        return self.__filesize


class Switch(object):
    def __init__(self, value):
        self.value = value
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def __call__(self, *cases):
        return self.value in cases


def getReSafety(pattern):
    # +1 for every 256 bytes
    # +2 for every not-.-before-*{+
    # +1 for every .-before-*{+
    return (
        (len(pattern) // 256) +
        (
            pattern.count("*") + pattern.count("{") + pattern.count("+")
            - pattern.count(".*") - pattern.count(".{") - pattern.count(".+")
        ) * 2 +
        (pattern.count(".*") - pattern.count(".{") - pattern.count(".+"))
    )


def getContentType(file_name, prefix):
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