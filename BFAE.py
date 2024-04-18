from typing import Dict, Callable, List
from functools import partial
import logging

# create logger
logging.basicConfig()

logger = logging.getLogger("FAE")
logger.setLevel(logging.WARN)

# expression hierarchy
class Expression():
    pass

# Value
class Value():
    pass

# type of environment
Env = Dict[str, Value]

# type addr
Addr = int

# type Storage
Sto = Dict[Addr, Value]

# types of values
class NumV(Value):
    def __init__(self, n: int):
        self.n = n
    def __str__(self) -> str:
        return f"NumV({self.n})"

class CloV(Value):
    def __init__(self, param: str, body: Expression, env: Env):
        self.param = param
        self.body = body
        self.env = env
    def __str__(self) -> str:
        return f"CloV({self.param}, {self.body}, {self.env})"


class BoxV(Value):
    def __init__(self, a: Addr):
        self.a = a

# types of expression
class Num(Expression):
    def __init__(self, n):
        self.n = n
    def __str__(self) -> str:
        return f"Num({self.n})"

class Add(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __str__(self) -> str:
        return f"Add({self.left}, {self.right})"
    
class Sub(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __str__(self) -> str:
        return f"Sub({self.left}, {self.right})"
    
class Id(Expression):
    def __init__(self, name: str):
        self.name = name
    def __str__(self) -> str:
        return f"Id({self.name})"
        
class App(Expression):
    def __init__(self, f_expr: Expression, val: Expression):
        self.f_expr = f_expr
        self.val = val
    def __str__(self) -> str:
        return f"App({self.f_expr}, {self.val} )"

class Fun(Expression):
    def __init__(self, par_name: str, body: Expression):
        self.par_name = par_name
        self.body = body
    def __str__(self) -> str:
        return f"Fun({self.par_name}, {self.body})"

class NewBox(Expression):
    def __init__(self, e: Expression) -> None:
        self.e = e
    def __str__(self) -> str:
        return f"NewBox({self.e})"
    
class OpenBox(Expression):
    def __init__(self, b: Expression) -> None:
        self.b = b
    def __str__(self) -> str:
        return f"OpenBox({self.b})"
    
class SetBox(Expression):
    def __init__(self, b: Expression, e: Expression) -> None:
        self.e = e
    def __str__(self) -> str:
        return f"SetBox({self.b}, {self.e})"
    
class Seqn(Expression):
    def __init__(self, l: Expression, r: Expression) -> None:
        self.l = l
        self.r = r
    def __str__(self) -> str:
        return f"Seqn({self.l}, {self.r})"




NumFunc = Callable[[int, int], int]

# exceptions
class InterPreterException(Exception):
    pass

class FreeIdentifierError(InterPreterException):
    pass

class UnknownStatementException(InterPreterException):
    pass
 
class UnknownFunction(InterPreterException):
    pass
 
class NotNumExpression(InterPreterException):
    pass

class ClosureError(InterPreterException):
    pass

class BoxException(InterPreterException)
    pass

class BoxValueException():
    pass

def interp(expr : Expression, env: Env, sto: Sto) -> tuple[Value, Sto]:
    logger.debug(f"calling interp with {expr=!s} {env=!s}")
    match expr:
        case Num(n=n):
            logger.debug("calling Num")
            return (NumV(n), sto)
        case Seqn(l=l, r=r):
            _, lstore = interp(l, env, sto)
            return interp(r, env, lstore)
        case Add(left=left, right=right):
            logger.debug("calling Add")
            match interp(left, env, sto):
                case (NumV(n=n), lstore):
                    match interp(right, env, lstore):
                        case (NumV(n=m), rstore):
                            return (NumV(n+m), rstore)
                        case _:
                            raise NotNumExpression("Add - right operand not an integer")
                case _:
                    raise NotNumExpression("Add - left operand not an integer")
        case Sub(left=left, right=right):
            logger.debug("calling Sub")
            match interp(left, env, sto):
                case (NumV(n=n), lstore):
                    match interp(right, env, lstore):
                        case (NumV(n=m), rstore):
                            return NumV(n-m), rstore
                        case _:
                            raise NotNumExpression("Sub - right operand not an integer")
                case _:
                    raise NotNumExpression("Sub - left operand not an integer")
        case Id(name=name):
            logger.debug("calling Id")
            return (lookup(name, env), sto)
        case Fun(par_name=par_name, body=body):
            logger.debug("calling Fun")
            return (CloV(par_name, body, env), sto)
        case App(f_expr=f_expr, val=val):
            match interp(f_expr, env, sto):
                case CloV(param=param, body=body, env=fenv), lstore:
                    v, rstore = interp(v, env, lstore)
                    return interp(body, dict(fenv, **{param: v}), rstore)
                case _:
                    raise ClosureError(f"not a closure: {f_expr}")
        case NewBox(e=e):
            v, s = interp(e, env, sto)
            a = max(sto.keys, 0)
            return BoxV(a), dict(sto, **{a: v})
        case OpenBox(e=e):
            match interp(e, env, sto):
                case BoxV(a=a), s:
                    return s[a], s
                case _:
                    raise BoxValueException(f"{e}!r not a box value")
        case SetBox(b=b, e=e):
           match interp(b, env, sto):
               case BoxV(a=a), bs:
                    v, es = interp(e, env, bs)
                    es[a] = v
                    return v, es
        case _:
            raise UnknownStatementException(f"Unknown statement {expr}")

"""
Note that 
Val is syntactic sugar for CloV

CloV
    interp(body, dict(fenv, **{par_name: interp(val, env)}))

Val
    interp(body, dict(env, **{name : res}))

    { val x = 10; x} è quivalente a ( x => x )(10)
"""

def lookup(var_name:str, env: Env):
    try:
        return env[var_name]
    except KeyError:
        raise FreeIdentifierError(f"free identifier {var_name}")
    
def numOp(op: NumFunc, lexpr: Value, rexpr: Value)-> Value:
    if isinstance(lexpr, NumV) and isinstance (rexpr, NumV):
        return NumV(op(lexpr.n, rexpr.n))
    else:
        raise NotNumExpression(f"not both numbers: {lexpr} {rexpr}")

numAddV = partial(numOp, lambda x,y: x + y)
numSubV = partial(numOp, lambda x,y: x - y)

# test section
assert interp(Num(10), {}).n  == 10
assert interp(Add(Num(10), Num(20)), {}).n == 30
assert interp(Sub(Num(10), Num(20)), {}).n == -10
assert interp(Add(Num(0), Num(3)), {}).n == 3

assert interp(
        App(Fun("x", Id("x")), Num(1)),
      {}).n == 1

assert interp(
    App(Fun("x", Add(Id("x"), Id("x"))), Num(1)),
    {}).n == 2

assert interp(
    App(Fun("x", 
            Add(
                App(Fun("x", Add(Id("x"), Num(5))), Num(4)),
                Id("x"))
            ), 
        Num(1)), {}).n  == 10

assert interp(App(Fun("x", Add(Id("x"), Num(10))), Num(5)), {}).n == 15 
# interp(App(Fun("x", Add(Id("x"), Num(10))), Num(5)), {})