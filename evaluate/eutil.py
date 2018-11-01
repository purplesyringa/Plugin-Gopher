class GasHolder(object):
    def __init__(self, gas):
        self.__gas = gas
    def needGas(self, cnt):
        if self.__gas < cnt:
            raise SyntaxError("Out of gas")
        self.__gas -= cnt
    def addGas(self, cnt):
        self.__gas += cnt
    def getGas(self):
        return self.__gas
    def setGas(self, gas):
        self.__gas = gas


class GopherFunction(object):
    def __init__(self, expr, arg_names, gas_holder):
        self.expr = expr
        self.arg_names = arg_names
        self.gas_holder = gas_holder
    def __len__(self):
        return len(self.arg_names)
    def __call__(self, *args):
        import code
        scope = {}
        for i, arg in enumerate(args):
            scope[self.arg_names[i]] = arg
        return code.evaluateCode(self.expr, scope, self.gas_holder)


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


# Raise error if value is Mark (or contains Mark)
def safePop(stack):
    return safeList([stack.pop()])[0]
def safeList(l):
    for val in l:
        if isinstance(val, Mark):
            val.unsafe()
    return l