from Gopher.gutil import Switch
from builtin_functions import builtin_functions
from tokenize import tokenize_code
from eutil import *
import inspect


def evaluate_code(expr, scope):
    # Tokenize if not tokenized already
    if isinstance(expr, list):
        tokens = expr
    else:
        tokens = tokenize_code(expr)

    stack = []
    lambda_balance = 0

    for token in tokens:
        # Handle inherited lambdas
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

        # Evaluate tokens
        with Switch(type(token)) as Case:
            # Push numbers, strings onto stack
            if Case(Number):
                stack.append(token())
            elif Case(String):
                stack.append(token())
            elif Case(Variable):
                stack.append(getVariable(scope, token))
            elif Case(Function):
                # Functions
                if token() in builtin_functions or (
                    token() in scope and
                    not isinstance(scope[token()], GopherFunction) and
                    callable(scope[token()])
                ):
                    # Evaluate built-in function. Some built-in functions
                    # are in `scope`, not `builtin_functions` if they are
                    # dependent on context, so we need to check `scope` as
                    # well.
                    f = builtin_functions.get(token(), scope.get(token()))
                    executeBuiltinFunction(f, token, stack)
                elif token() in scope:
                    # Execute GopherFunction
                    if isinstance(scope[token()], GopherFunction):
                        f = scope[token()]
                        executeGopherFunction(f, token, stack)
                    else:
                        raise SyntaxError("Function %s is not defined, though there is variable :%s. Did you miss ':'?" % (token(), token()))
                else:
                    # Handle { }, ( ), [ ], f() ;
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



def getVariable(scope, token):
    # Check variable for existence and return its value
    if token() in scope:
        return scope[token()]
    elif token() in builtin_functions:
        raise SyntaxError("Variable :%s is not defined, though there is builtin function %s. Did you accidentally press ':'?" % (token(), token()))
    else:
        raise SyntaxError("Variable :%s is not defined" % token())

def executeBuiltinFunction(f, token, stack):
    # Get argument count
    args, varargs, _, _ = inspect.getargspec(f)
    if varargs is None:
        # Simple case
        if len(stack) < len(args):
            raise SyntaxError("Not enough values in stack during call to %s: expected at least %s, got %s" % (token(), len(args), len(stack)))
        call_args = safeList(stack[-len(args):])
        del stack[-len(args):]
    else:
        # Get count from stack head
        if len(stack) < 1:
            raise SyntaxError("Expected count value in stack during call to %s; stack is empty" % token())
        vararg_cnt = safePop(stack)
        if not isinstance(vararg_cnt, int):
            raise SyntaxError("Expected count value in stack during call to %s; got %r" % (token(), vararg_cnt))
        if len(stack) < vararg_cnt:
            raise SyntaxError("Not enough values in stack during call to %s: specified %s, got %s" % (token(), vararg_cnt, len(stack)))
        call_args = safeList(stack[-vararg_cnt:])
        del stack[-vararg_cnt:]
    # Call
    ret = f(*call_args)
    if ret is not None:
        stack.append(ret)

def executeGopherFunction(f, token, stack):
    if len(stack) < len(f):
        raise SyntaxError("Not enough values in stack during call to :%s: expected at least %s, got %s" % (token(), len(f), len(stack)))
    call_args = stack[-len(f):]
    stack = stack[:-len(f)]
    ret = f(*call_args)
    if ret is not None:
        stack.append(ret)