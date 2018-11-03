from Gopher.gutil import getReSafety
from eutil import GopherFunction
import re
import string
import random


# Builtin functions
def re_sub(gas_holder, s, p, r):
    gas_holder.needGas(getReSafety(p))
    if isinstance(r, GopherFunction):
        return re.sub(p, lambda match: r(*match.groups()), s)
    else:
        return re.sub(p, r, s)
def random_str(len):
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(len))
def setitem(v, i, a):
    v[i] = a
def delitem(v, i):
    del v[i]
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
    "in": lambda v, i: i in v,
    "[]": lambda v, i: v[i],
    "[]?": lambda v, i, o: v.get(i, o),
    "[]=": setitem,
    "del[]": delitem,
    "len": lambda a: len(a),
    "str": lambda a: str(a),
    "int": lambda a: int(a),
    "parseInt": lambda a, b: int(a, b),
    "float": lambda a: float(a),
    "re_sub": re_sub,
    "random_str": random_str
}