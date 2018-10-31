from util import Switch
import inspect
import builtins
import re


# Builtin functions
builtin_functions = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "//": lambda a, b: a // b,
    "%": lambda a, b: a % b,
    "**": lambda a, b: a ** b,
    "<<": lambda a, b: a << b,
    ">>": lambda a, b: a >> b,
    "&": lambda a, b: a & b,
    "|": lambda a, b: a | b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
    "not": lambda a: not a,
    "^": lambda a, b: a ^ b,
    "len": lambda a: len(a),
    "int": lambda a: int(a),
    "parseInt": lambda a, b: int(a, b),
    "float": lambda a: float(a),
    "re_sub": lambda s, p, r: re.sub(p, r, s)
}


def evaluate(expr, scope):
    # scope is a dict of variables
    # expr is a string we want to evaluate

    # Here we only parse the code blocks; we don't parse the code
    # itself. Code parsing is in evaluate_code() function.
    result = ""
    state = "text"
    current_code = ""
    for c in expr:
        with Switch(state) as Case:
            if Case("text"):
                # When we see regular text, just save it
                if c == "$":
                    state = "$"
                else:
                    result += c
            elif Case("$"):
                # ${} maybe?
                if c == "{":
                    # Start code
                    current_code = ""
                    state = "code"
                else:
                    # Fallback
                    result += "$" + c
                    state = "text"
            elif Case("code"):
                # Here, we'll only check quotes ("), and not really parse
                # the code.
                if c == "\"":
                    # String started -- just save it
                    state = "string"
                    current_code += "\""
                elif c == "}":
                    # End of code -- switch back to text
                    result += str(evaluate_code(current_code, scope))
                    current_code = ""
                    state = "text"
                else:
                    # Just some character
                    current_code += c
            elif Case("string"):
                # We're inside a string -- wait for end
                current_code += c
                if c == "\"":
                    # End of string
                    state = "code"

    # Now check whether the code is correct
    if state == "string":
        raise SyntaxError("Unterminated string literal")
    elif state == "code":
        raise SyntaxError("Unterminated code block")

    return result



class Token(object):
    def __init__(self):
        self.value = ""
    def append(self, c):
        self.value += c
class Number(Token):
    def __call__(self):
        return float(self.value) if "." in self.value else int(self.value)
class String(Token):
    def __call__(self):
        return self.value
class Variable(Token):
    def __call__(self):
        return self.value
class Function(Token):
    def __call__(self):
        return self.value

def evaluate_code(expr, scope):
    # First, do tokenization
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
                elif c in "'`":
                    raise SyntaxError("Unexpected '%s'. Did you mean '\"'?" % c)
                elif c == ":":
                    # Variable
                    state = "variable"
                    current_token = Variable()
                elif c.lower() in "abcdefghijklmnopqrstuvwxyz~!@#$%^&*()_+-=?/<>,.\\|":
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
            elif Case("variable"):
                if c.lower() in "abcdefghijklmnopqrstuvwxyz_":
                    current_token.append(c)
                else:
                    raise SyntaxError("Expected variable name, got '%s'" % c)
            elif Case("function"):
                if c.lower() in "abcdefghijklmnopqrstuvwxyz~!@#$%^&*()_+-=?/<>,.\\|":
                    current_token.append(c)
                else:
                    raise SyntaxError("Expected function name, got '%s'" % c)

    if current_token is not None:
        tokens.append(current_token)


    stack = []

    for token in tokens:
        with Switch(type(token)) as Case:
            if Case(Number):
                stack.append(token())
            elif Case(String):
                stack.append(token())
            elif Case(Variable):
                if token() in scope:
                    stack.append(scope[token()])
                elif token() in builtin_functions:
                    raise SyntaxError("Variable :%s is not defined, though there is builtin function %s. Did you accidentally press ':'?" % (token(), token()))
                else:
                    raise SyntaxError("Variable :%s is not defined" % token())
            elif Case(Function):
                if token() in builtin_functions:
                    f = builtin_functions[token()]
                    # Get argument count
                    args, varargs, _, _ = inspect.getargspec(f)
                    if varargs is None:
                        # Simple case
                        if len(stack) < len(args):
                            raise SyntaxError("Not enough values in stack during call to %s: expected at least %s, got %s" % (token(), len(args), len(stack)))
                        call_args = stack[-len(args):]
                        stack = stack[:-len(args)]
                    else:
                        # Get count from stack head
                        if len(stack) < 1:
                            raise SyntaxError("Expected count value in stack during call to %s; stack is empty" % token())
                        vararg_cnt = stack.pop()
                        if not isinstance(vararg_cnt, int):
                            raise SyntaxError("Expected count value in stack during call to %s; got %r" % (token(), vararg_cnt))
                        if len(stack) < vararg_cnt:
                            raise SyntaxError("Not enough values in stack during call to %s: specified %s, got %s" % (token(), vararg_cnt, len(stack)))
                        call_args = stack[-len(args):]
                        stack = stack[:-len(args)]
                    # Call
                    ret = f(*call_args)
                    if ret is not None:
                        stack.append(ret)
                elif token() in scope:
                    raise SyntaxError("Function %s is not defined, though there is variable :%s. Did you miss ':'?" % (token(), token()))
                else:
                    raise SyntaxError("Function %s is not defined" % token())

    if len(stack) == 0:
        raise SyntaxError("Expected expression to return value; stack is empty")
    elif len(stack) > 1:
        raise SyntaxError("Expected expression to return value; got %s values" % len(stack))
    return stack[0]