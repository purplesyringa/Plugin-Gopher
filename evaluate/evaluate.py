from Gopher.gutil import Switch
from code import evaluate_code


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