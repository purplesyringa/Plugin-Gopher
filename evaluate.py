from gutil import Switch
from util import SafeRe
import inspect
import re


# Builtin functions
def re_sub(s, p, r):
    if isinstance(r, GopherFunction):
        return SafeRe.sub(p, lambda match: r(*match.groups()), s)
    else:
        return SafeRe.sub(p, r, s)
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
    "[]": lambda v, i: v[i],
    "len": lambda a: len(a),
    "str": lambda a: str(a),
    "int": lambda a: int(a),
    "parseInt": lambda a, b: int(a, b),
    "float": lambda a: float(a),
    "re_sub": re_sub
}


class GopherFunction(object):
    def __init__(self, expr, arg_names):
        self.expr = expr
        self.arg_names = arg_names
    def __len__(self):
        return len(self.arg_names)
    def __call__(self, *args):
        scope = {}
        for i, arg in enumerate(args):
            scope[self.arg_names[i]] = arg
        return evaluate_code(self.expr, scope)


def evaluate(expr, scope):
    # scope is a dict of variables
    # expr is a string we want to evaluate

    # Here we only parse the code blocks; we don't parse the code
    # itself. Code parsing is in evaluate_code() function.
    result = u""
    state = "text"
    current_code = ""
    balance = 0
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
                    balance = 0
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
                elif c == "{":
                    balance += 1
                    current_code += c
                elif c == "}":
                    if balance == 0:
                        # End of code -- switch back to text
                        result += unicode(evaluate_code(current_code, scope))
                        current_code = ""
                        state = "text"
                    else:
                        current_code += c
                        balance -= 1
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


class Mark(object):
    begin = SyntaxError("Unmatched begin")
    end = SyntaxError("Unmatched end")
    @classmethod
    def get(cls, stack):
        return cls.getMark(stack)[0]
    @classmethod
    def getMark(cls, stack):
        l = []
        mark = None
        while stack:
            value = stack.pop()
            if isinstance(value, cls):
                mark = value
                break
            elif isinstance(value, Mark):
                raise cls.end
            else:
                l.append(value)
        else:
            raise cls.end
        return l[::-1], mark
    def unsafe(self):
        raise self.begin
class DictMark(Mark):
    begin = SyntaxError("Unmatched '{'")
    end = SyntaxError("Unmatched '}'")
class TupleMark(Mark):
    begin = SyntaxError("Unmatched '('")
    end = SyntaxError("Unmatched ')'")
class ListMark(Mark):
    begin = SyntaxError("Unmatched '['")
    end = SyntaxError("Unmatched ']'")
class LambdaMark(Mark):
    begin = SyntaxError("Unmatched '(...)'")
    end = SyntaxError("Unmatched ';'")
    def __init__(self, arg_names):
        super(LambdaMark, self).__init__()
        self.arg_names = arg_names
        self.tokens = []
    def append(self, token):
        self.tokens.append(token)


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
                elif c in "'`":
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


def evaluate_code(expr, scope):
    # Tokenize if not tokenized already
    if isinstance(expr, list):
        tokens = expr
    else:
        tokens = tokenize_code(expr)

    stack = []
    lambda_balance = 0

    for token in tokens:
        if lambda_balance > 0:
            if isinstance(token, Function) and token() == ";":
                lambda_balance -= 1
                if lambda_balance > 0:
                    # Save
                    stack[-1].append(token)
                    continue
                else:
                    # Fallthrough -- we handle this case below
                    pass
            elif isinstance(token, Function) and token().startswith("f("):
                lambda_balance += 1
            else:
                # Save
                stack[-1].append(token)
                continue

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
                # Functions
                if token() in builtin_functions or (
                    token() in scope and
                    not isinstance(scope[token()], GopherFunction) and
                    callable(scope[token()])
                ):
                    f = builtin_functions.get(token(), scope.get(token()))
                    # Get argument count
                    args, varargs, _, _ = inspect.getargspec(f)
                    if varargs is None:
                        # Simple case
                        if len(stack) < len(args):
                            raise SyntaxError("Not enough values in stack during call to %s: expected at least %s, got %s" % (token(), len(args), len(stack)))
                        call_args = safeList(stack[-len(args):])
                        stack = stack[:-len(args)]
                    else:
                        # Get count from stack head
                        if len(stack) < 1:
                            raise SyntaxError("Expected count value in stack during call to %s; stack is empty" % token())
                        vararg_cnt = safePop(stack)
                        if not isinstance(vararg_cnt, int):
                            raise SyntaxError("Expected count value in stack during call to %s; got %r" % (token(), vararg_cnt))
                        if len(stack) < vararg_cnt:
                            raise SyntaxError("Not enough values in stack during call to %s: specified %s, got %s" % (token(), vararg_cnt, len(stack)))
                        call_args = safeList(stack[-len(args):])
                        stack = stack[:-len(args)]
                    # Call
                    ret = f(*call_args)
                    if ret is not None:
                        stack.append(ret)
                elif token() in scope:
                    if isinstance(scope[token()], GopherFunction):
                        f = scope[token()]
                        if len(stack) < len(f):
                            raise SyntaxError("Not enough values in stack during call to :%s: expected at least %s, got %s" % (token(), len(f), len(stack)))
                        call_args = stack[-len(f):]
                        stack = stack[:-len(f)]
                        ret = f(*call_args)
                        if ret is not None:
                            stack.append(ret)
                    else:
                        raise SyntaxError("Function %s is not defined, though there is variable :%s. Did you miss ':'?" % (token(), token()))
                else:
                    with Switch(token()) as Case:
                        # Dictionaries
                        if Case("{"):
                            stack.append(DictMark())
                        elif Case("}"):
                            # Build dictionary
                            d = DictMark.get(stack)
                            if len(d) % 2 != 0:
                                raise SyntaxError("Expected dictionary; got odd count of values")
                            cur_dict = {}
                            for key, value in zip(d[::2], d[1::2]):
                                cur_dict[key] = value
                            stack.append(cur_dict)
                        # Tuples
                        elif Case("("):
                            stack.append(TupleMark())
                        elif Case(")"):
                            # Build tuple
                            t = TupleMark.get(stack)
                            stack.append(tuple(t))
                        # Lists
                        elif Case("["):
                            stack.append(ListMark())
                        elif Case("]"):
                            # Build list
                            l = ListMark.get(stack)
                            stack.append(l)
                        # Lambdas
                        elif token().startswith("f("):
                            arg_names = token()[2:-1].split(",")
                            if arg_names == [""]:
                                arg_names = []
                            stack.append(LambdaMark(arg_names))
                            lambda_balance += 1
                        elif Case(";"):
                            _, m = LambdaMark.getMark(stack)
                            stack.append(GopherFunction(m.tokens, m.arg_names))
                        else:
                            raise SyntaxError("Function %s is not defined" % token())

    if len(stack) == 0:
        raise SyntaxError("Expected expression to return value; stack is empty")

    # Check for Mark
    safeList(stack)
    if len(stack) > 1:
        raise SyntaxError("Expected expression to return value; got %s values" % len(stack))
    return stack[0]


# Raise error if value is Mark (or contains Mark)
def safePop(stack):
    return safeList([stack.pop()])[0]
def safeList(l):
    for val in l:
        if isinstance(val, Mark):
            val.unsafe()
    return l