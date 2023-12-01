import re
import logging
import AE as lang

logger = logging.getLogger("AEParser")
logger.setLevel(logging.DEBUG)

"""
syntax
e ::= n
    | ( e + e )
    | ( e - e )
"""

# pattern
DIGIT = r"\d+"
WHITESPACES = r"\s*"

OPENPAR = r"\("
CLOSEDPAR = r"\)"

ANYOTHER = r"(.*)"

OPPLUS = r"\+"
OPSUB = r"\-"

# exceptions
class ParserException(Exception):
    pass

class ADDOPException(ParserException):
    pass

class SUBOPException(ParserException):
    pass

class NumException(ParserException):
    pass

ADDEXPR = WHITESPACES + OPENPAR + WHITESPACES  \
        + ANYOTHER + WHITESPACES + OPPLUS + WHITESPACES + ANYOTHER \
        + WHITESPACES +CLOSEDPAR + WHITESPACES

SUBEXPR = WHITESPACES + OPENPAR + WHITESPACES  \
        + ANYOTHER + WHITESPACES + OPSUB + WHITESPACES + ANYOTHER \
        + WHITESPACES +CLOSEDPAR + WHITESPACES

NUMBER = WHITESPACES + r"(\d+)" + WHITESPACES

def ADDParser(s: str, pexpr: str):
    p = re.compile(pexpr) 
    m = p.match(s)

    logger.debug(f"ADDParser {m}")
    
    if m is not None:
        leftop = m.group(1)
        rightop = m.group(2)

        logger.debug(f"ADDParser {leftop=} {rightop=}") 
        
        leftop = Parse(leftop, EXPR_START)
        rightop = Parse(rightop, EXPR_START)
        return lang.Add(leftop, rightop)
    
    raise ADDOPException(f"Not an ADD expression: {s}")

def SUBParser(s: str, pexpr: str):
    p = re.compile(pexpr) 
    m = p.match(s)

    logger.debug(f"SUBParser {m}")
    
    if m is not None:
        leftop = m.group(1)
        rightop = m.group(2)

        logger.debug(f"SUBParser {leftop=} {rightop=}")
        
        leftop = Parse(leftop, EXPR_START)
        rightop = Parse(rightop, EXPR_START)
        return lang.Sub(leftop,rightop)
    
    raise SUBOPException(f"Not and ADD expression: {s}")

def NumberId(s:str, pexpr: str):
    p = re.compile(pexpr) 
    m = p.match(s)

    logger.debug(f"NumberId {m}")
    
    if m is not None:
        num = m.group(1)
        logging.debug(f"NumberId {num=}")
        return lang.Num(int(num))
    
    raise NumException(f"Not and number: {s}")

EXPR_START = { 
    NUMBER: NumberId,
    ADDEXPR: ADDParser,
    SUBEXPR: SUBParser}


def Parse(s, root= EXPR_START)->lang.Expression:
    prog = s.replace('\n', ' ').replace('\r',' ').replace('\r\n',' ')

    for pattern, parsePattern in root.items():
        try:
            logger.debug(f"calling {parsePattern.__name__} with {pattern}")
            return parsePattern(prog, pattern)
        except ParserException as e:
            logger.debug("generated exception")
            logger.debug(f"Source string: {s}")
            logger.debug(e)

    raise ParserException(f"Expression not recognized: {s}")


if __name__ == "__main__":
    expr_list = ["  ( Ciccio + Caio      )",
             "  ( Ciccio + Caio      ",
             "  ( 10  + 20)",
             "  (10 + 20",
             "(10 + (20 - 1))",
             "(20 - 1)",
             "  10",
             """
             (
             10
                +
            20
             )
             """]


    for el in expr_list:
        try:
            print(f"parsing {el}")
            code = Parse(el, EXPR_START)
            print(f"{code=!s}")
            res = lang.interp(code)
            print(f"result of execution {res}")
        except (ParserException, ParserException) as e:
            print(e)
        print("-"*len(el))

    print("parsing and executing")

