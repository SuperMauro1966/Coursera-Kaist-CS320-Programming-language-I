import re
import logging
from typing import Dict, List

import F1VAE as lang

logger = logging.getLogger("F1VAEParser")
logger.setLevel(logging.DEBUG)

"""
syntax
e ::= n
    | ( <e> + <e> )
    | ( <e> - <e> )
    | { val <id> = <e> ; <e>}
    | <id>
    | <id> ( <e> )                 # function call

fdef ::= def <id> ( <id> ) = <e>
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

class F1DefinitionException(ParserException):
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

F1EXPR = WHITESPACES + r"def" + WHITESPACES + IDENTIFIER + \
         WHITESPACES + OPENPAR + WHITESPACES + IDENTIFIER + \
         WHITESPACES + CLOSEDPAR + WHITESPACES + ANYOTHER

def ADDParser(s: str, pexpr: str):
    p = re.compile(pexpr) 
    m = p.match(s)

    logger.debug(f"ADDParser {m}")
    
    if m is not None:
        logger.debug(f"{m.groups()=}")
        leftop = m.group(1)
        rightop = m.group(2)

        logger.debug(f"ADDParser {leftop=} {rightop=}") 
        
        _, leftop = parse(leftop, EXPR_START)
        _, rightop = parse(rightop, EXPR_START)
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
        
        _, leftop = parse(leftop, EXPR_START)
        _, rightop = parse(rightop, EXPR_START)
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
                        parse(val_expr, EXPR_START)[1],
                        parse(expr, EXPR_START)[1])        
        
    raise ValException(f"Not a val expression: {s}")

def IdParser(s: str, pexpr: str)->lang.Id:
    p = re.compile(pexpr) 
    m = p.match(s)

    logger.debug(f"IdParser {m}")
    
    if m is not None:
        ident = m.group(1)
        logger.debug(f"Idparser {ident=}")
        
        return lang.Id(ident)

    raise ValException(f"Not an Id expression: {s}")

def parseF1Def(s: str)->tuple[List[lang.Fdef], str]:
    p = re.compile(F1EXPR + ANYOTHER) 
    m = p.match(s)

    logger.debug(f"parseF1Def {s}")
    
    if m is not None:
        fname = m.group(1)
        par_name = m.group(2)
        body = m.group(3)

        try:
            logging.debug(f"Verify func name {fname}")
            IdParser(fname, IDENTEXPR)
        except IdentifierException:
            raise F1DefinitionException(f"not a valid function name {fname}")

        try:
            logging.debug(f"Verify func parameter name {par_name}")
            IdParser(par_name, IDENTEXPR)
        except IdentifierException:
            raise F1DefinitionException(f"not a valid parameter name: {par_name}")
        
        logging.debug(f"Verify func body {fname}")
        code = None

        for pattern, pattern_parser in EXPR_START.items():
            logger.debug(f"calling: {pattern_parser.__name__!s} with pattern {(pattern+ANYOTHER) } and body= {body!s}")
            try:
                code = pattern_parser(body, pattern+ANYOTHER)
            except ParserException:
                continue
            else:
                logger.debug(f"generated {code!s}")
                body_match = re.match(pattern+ANYOTHER, body)
                other_expr = body_match.groups()[-1]

                logger.debug("founded match")
                logger.debug(f"other string to be parsed {other_expr}")
                # parse the function body
                fds = []
                try:
                    # try to find another function definition
                    fds, other_expr = parseF1Def(other_expr)
                except F1DefinitionException:
                    return fds, other_expr
                else:
                    return fds.append(lang.Fdef(fname, par_name, code)), other_expr

    raise F1DefinitionException(f"Not an function definition: {s}")

EXPR_START = { 
    NUMBER: NumberId,
    ADDEXPR: ADDParser,
    SUBEXPR: SUBParser,
    VALEXPR: ValParser, 
    IDENTEXPR: IdParser, 
    }

def parse(s, root=EXPR_START)->tuple[List[lang.Fdef], lang.Env]:
    prog = s.replace('\n', ' ').replace('\r',' ').replace('\r\n',' ')

    # parsing for all the first order function
    fds = []

    if root is F1EXPR:
        try:
            root = EXPR_START 
            fds, prog = parseF1Def(prog)
        except F1DefinitionException:
            pass
    
    # then parser for the expression
    logger.debug(f"root: {root}")
    for pattern, parsePattern in root.items():
        try:
            logger.debug(f"calling {parsePattern.__name__} with {pattern} and string {prog}")
            return fds, parsePattern(prog, pattern)
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
             "{ val ciccio = 3  ; ciccio}",
             """
                def f(x) 
                    (x + 1)

                x(2)
             """]


    for el in expr_list:
        try:
            print(f"parsing {el}")
            fds , code = parse(el, F1EXPR)
            print(f"{code=!s}")
            res = lang.interp(code, {}, fds)
            print(f"result of execution {res}")
        except (ParserException, lang.InterPreterException) as e:
            print(e)
        print("-"*len(el))

    print("parsing and executing")
