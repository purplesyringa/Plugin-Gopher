from Gopher.gutil import Switch
from eutil import Number, String, Variable, Function


def tokenize_code(expr):
    state = "word"
    tokens = []
    current_token = None
    tmp = None
    for c in expr:
        with Switch(state) as Case:
            if Case("word", "number", "float", "string_space", "variable", "function") and c.strip() == "":
                # A new word
                state = "word"
                tokens.append(current_token)
                current_token = None
            elif Case("word"):
                # It can be any word
                if c in "0123456789":
                    # Likely a number
                    state = "number"
                    current_token = Number()
                    current_token.append(c)
                elif c == "\"":
                    # A string
                    state = "string"
                    current_token = String()
                elif c == "`":
                    # A raw string
                    state = "raw_string"
                    current_token = String()
                elif c == "'":
                    raise SyntaxError("Unexpected '%s'. Did you mean '\"'?" % c)
                elif c == ":":
                    # Variable
                    state = "variable"
                    current_token = Variable()
                elif c.lower() in "abcdefghijklmnopqrstuvwxyz~!@#$%^&*()_+-=?/<>,.\\|{}[];:":
                    # Function
                    state = "function"
                    current_token = Function()
                    current_token.append(c)
                else:
                    raise SyntaxError("Unexpected '%s'" % c)
            elif Case("number"):
                if c in "0123456789":
                    current_token.append(c)
                elif c == ".":
                    current_token.append(c)
                    state = "float"
                else:
                    raise SyntaxError("Unexpected '%s' in number" % c)
            elif Case("float"):
                if c in "0123456789":
                    current_token.append(c)
                elif c == ".":
                    raise SyntaxError("Two decimal points in a number")
                else:
                    raise SyntaxError("Unexpected '%s' in number" % c)
            elif Case("string"):
                if c == "\"":
                    tokens.append(current_token)
                    current_token = None
                    state = "string_space"
                elif c == "\\":
                    state = "string_escape"
                else:
                    current_token.append(c)
            elif Case("string_space"):
                raise SyntaxError("Expected space after string literal, got '%s'" % c)
            elif Case("string_escape"):
                if c in "xX":
                    state = "string_hex1"
                else:
                    current_token.append({
                        "n": "\n",
                        "r": "\r",
                        "t": "\t",
                        "b": "\b"
                    }.get(c, c))
                    state = "string"
            elif Case("string_hex1"):
                if c in "0123456789abcdefABCDEF":
                    state = "string_hex2"
                    tmp = c
                else:
                    raise SyntaxError("Expected hexadimical number, got '%s' inside \\x??" % c)
            elif Case("string_hex2"):
                if c in "0123456789abcdefABCDEF":
                    state = "string"
                    current_token.append(chr(int(tmp, 16) * 256 + int(c, 16)))
                    tmp = None
                else:
                    raise SyntaxError("Expected hexadimical number, got '%s' inside \\x??" % c)
            elif Case("raw_string"):
                if c == "`":
                    tokens.append(current_token)
                    current_token = None
                    state = "string_space"
                else:
                    current_token.append(c)
            elif Case("variable"):
                if c.lower() in "abcdefghijklmnopqrstuvwxyz0123456789_":
                    current_token.append(c)
                else:
                    raise SyntaxError("Expected variable name, got '%s'" % c)
            elif Case("function"):
                if c.lower() in "abcdefghijklmnopqrstuvwxyz0123456789~!@#$%^&*()_+-=?/<>,.\\|":
                    current_token.append(c)
                else:
                    raise SyntaxError("Expected function name, got '%s'" % c)

    if current_token is not None:
        tokens.append(current_token)

    return tokens