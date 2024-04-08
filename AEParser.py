import re
import logging
import string

import AE as lang

logging.basicConfig()
logger = logging.getLogger("AEParser")
logger.setLevel(logging.DEBUG)

"""
syntax
e ::= n
    | ( e + e )
    | ( e - e )
"""

# pattern
DIGIT = r"(\d+)"
WHITESPACES = r"\s*"

OPENPAR = r"\("
CLOSEDPAR = r"\)"

OPPLUS = r"\+"
OPSUB = r"\-"

# exceptions
class ParserException(Exception):
    pass

class NumException(ParserException):
    pass

class SymbolException(ParserException):
    pass

def ConsumeSymbol(sym: str, prog: str)-> str:
    logger.debug(f"ConsumeSymbol called - {sym=!s} {prog=!s}")
    prog = prog.lstrip(string.whitespace)
    m = re.match(sym, prog)

    logger.debug(f"Match: {m!s}")
    if m is None:
        raise SymbolException(f"Symbol {sym!s} not found")

    return prog[m.end():]

def SpitAtSymbol(sym: str, prog: str)-> tuple[str, str]:
    prog = prog.lstrip(string.whitespace)
    m = re.search(sym, prog)

    if m is None:
        raise SymbolException(f"Symbol {sym!s} not found")
    
    return (prog[:m.start()], prog[m.end():])

def NumberId(prog:str, num_pattern: str)-> tuple[str, str]:
    logger.debug(f"NumberId called: {prog=} {num_pattern=}")
    prog = prog.lstrip(string.whitespace)
    m = re.match(num_pattern, prog)

    logger.debug(f"Match {m=!s}")

    if m is not None:
        num = m.group(1)
        logger.debug(f"NumberId {num=}")
        return num, prog[m.end():]
    
    raise NumException(f"Not and number: {prog}")

def iterParser(s)->tuple[lang.Expression, str]:
    logger.debug(f"iterparser - {s}")
    if len(s) == 0:
        return None, ""
    
    gen_expr = None
    try:
        s = ConsumeSymbol(OPENPAR, s)
    except SymbolException:
        # Num + Num
        # Num - Num
        # possible patterns

        try:
            left, s = SpitAtSymbol(OPPLUS, s)
        except SymbolException:
            try:
                left, s = SpitAtSymbol(OPSUB, s)
            except SymbolException:
                raise
            else:
                plus_operator = False
        else:
            plus_operator = True

        num, right_part = NumberId(left, DIGIT)
        left_op = lang.Num(int(num))
        checkEmptyTailProgram(right_part)

        right_op, s = Parser(s) 
        
        # checkEmptyTailProgram(right_part)

        if plus_operator:
            return lang.Add(left_op, right_op), s
        
        return lang.Sub(left_op, right_op), s

    else:
        gen_expr, s = Parser(s)
        s = ConsumeSymbol(CLOSEDPAR, str)
        return gen_expr, s
    
def checkEmptyTailProgram(prog: str):
    logger.debug(f"checkEmptyTailProgram called - {prog=!s}")
    prog = prog.lstrip(string.whitespace).rstrip(string.whitespace)
    if len(prog) != 0:
        raise ParserException(f"Error: Found {prog} instead of space chars")

def Parser(s)->lang.Expression:
    logger.debug(f"Parser - {s=}")
    if len(s) == 0:
        return None
    
    gen_expr = None
    try:
        s = ConsumeSymbol(OPENPAR, s)
    except SymbolException:
        # Num expected
        num, s = NumberId(s, DIGIT)
        gen_expr = lang.Num(int(num))
        # checkEmptyTailProgram(s)
    else:
        gen_expr , s = iterParser(s) 
        s = ConsumeSymbol(CLOSEDPAR, s)

    return gen_expr, s

if __name__ == "__main__":
    expr_list = [
             "10",
             " ( 10 + 20        )",
             " ( 10 + (20 + 30 ))",
             " (( 10 +     1) + ( 3 - 1) )",
             ]


    for el in expr_list:
        try:
            print(f"parsing {el}")
            code, _ = Parser(el)
            print(f"{code=!s}")
            res = lang.interp(code)
            print(f"result of execution {res}")
        except (ParserException, ParserException) as e:
            print(e)
        print("-"*len(el))

    print("parsing and executing")

