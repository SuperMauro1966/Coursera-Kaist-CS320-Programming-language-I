import re
import logging

import VAE as lang

logger = logging.getLogger("VAEParser")
logger.setLevel(logging.DEBUG)

"""
syntax
e ::= n
    | ( e + e )
    | ( e - e )
    | { val <id> = <e> ; <e>}
    | id
"""

# pattern
DIGIT = r"\d+"
WHITESPACES = r"\s*"

OPENPAR = r"\("
CLOSEDPAR = r"\)"

OPENCURLYBRACKET = r"\{"
CLOSECURLYBRACKET = r"\}"

ANYOTHER = r"(.*)"

OPPLUS = r"\+"
OPSUB = r"\-"

IDENTIFIER = r"([a-zA-Z]+)"
SEMICOLON = r";"

# exceptions
class ParserException(Exception):
    pass

class ADDOPException(ParserException):
    pass

class IdException(ParserException):
    pass

class ValException(ParserException):
    pass

class IdentifierException(ParserException):
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

VALEXPR = WHITESPACES + OPENCURLYBRACKET + WHITESPACES + \
          r"val" + WHITESPACES + IDENTIFIER + WHITESPACES + r"=" + WHITESPACES + \
          ANYOTHER +  WHITESPACES + SEMICOLON + WHITESPACES + \
          ANYOTHER + WHITESPACES + CLOSECURLYBRACKET + WHITESPACES

IDENTEXPR = WHITESPACES +  IDENTIFIER + WHITESPACES

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
        return lang.Add( leftop, rightop)
    
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
        return lang.Sub(leftop, rightop)
    
    raise ADDOPException(f"Not and ADD expression: {s}")

def NumberId(s:str, pexpr: str):
    p = re.compile(pexpr) 
    m = p.match(s)

    logger.debug(f"NumberId {m}")
    
    if m is not None:
        num = m.group(1)
        logging.debug(f"NumberId {num=}")
        return lang.Num(int(num))
    
    raise NumException(f"Not and number: {s}")


def ValParser(s: str, pexpr: str):
    p = re.compile(pexpr) 
    m = p.match(s)

    logger.debug(f"ValParser {m}")
    
    if m is not None:
        ident = m.group(1)
        val_expr = m.group(2)
        expr = m.group(3)

        logger.debug(f"ValParser {ident=} {val_expr=} {expr=}" )

        logger.debug(f"calling IdParser with {id}")
        
        try:
            IdParser(ident, IDENTIFIER)
        except IdentifierException as e:
            raise ValException(f"Wrong identifier") from e
        else:    
            return lang.Val(ident,
                        Parse(val_expr, EXPR_START),
                        Parse(expr, EXPR_START))        
        
    raise ValException(f"Not a val expression: {s}")

def IdParser(s: str, pexpr: str):
    p = re.compile(pexpr) 
    m = p.match(s)

    logger.debug(f"IdParser {m}")
    
    if m is not None:
        ident = m.group(1)
        logger.debug(f"Idparser {ident=}")
        
        return lang.Id(ident)

    raise ValException(f"Not an Id expression: {s}")

EXPR_START = { 
    NUMBER: NumberId,
    ADDEXPR: ADDParser,
    SUBEXPR: SUBParser,
    VALEXPR: ValParser, 
    IDENTEXPR: IdParser, 
    }

def Parse(s, root= EXPR_START):
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
             """,
             "{ val ciccio = 3  ; ciccio}"]


    for el in expr_list:
        try:
            print(f"parsing {el}")
            code = Parse(el, EXPR_START)
            print(f"{code=!s}")
            res = lang.interp(code, {})
            print(f"result of execution {res}")
        except (ParserException, lang.InterPreterException) as e:
            print(e)
        print("-"*len(el))

    print("parsing and executing")
