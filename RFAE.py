from typing import Dict, Callable, List
from functools import partial
import logging

# create logger
logging.basicConfig()

logger = logging.getLogger("RFAE")
logger.setLevel(logging.WARN)

# expression hierarchy
class Expression():
    pass

# Value
class Value():
    pass

# type of environment
Env = Dict[str, Value]

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

class If0(Expression):
    def __init__(self, cond:Expression, true_body:Expression, false_body:Expression):
        self.cond = cond
        self.true_body = true_body
        self.false_body = false_body
    
class Rec(Expression):
    def __init__(self, f:str, par_name:str, body:Expression):
        self.f = f
        self.par_name = par_name
        self.body = body

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

def interp(expr : Expression, env: Env) -> Value:
    logger.debug(f"calling interp with {expr=!s} {env=!s}")
    match expr:
        case Num(n=n):
            logger.debug("calling Num")
            return NumV(n)
        case Add(left=left, right=right):
            logger.debug("calling Add")
            match interp(left, env):
                case NumV(n=n):
                    match interp(right, env):
                        case NumV(n=m):
                            return NumV(n+m)
                        case _:
                            raise NotNumExpression("Add - right operand not an integer")
                case _:
                    raise NotNumExpression("Add - left operand not an integer")
        case Sub(left=left, right=right):
            logger.debug("calling Sub")
            match interp(left, env):
                case NumV(n=n):
                    match interp(right, env):
                        case NumV(n=m):
                            return NumV(n-m)
                        case _:
                            raise NotNumExpression("Sub - right operand not an integer")
                case _:
                    raise NotNumExpression("Sub - left operand not an integer")
        case Id(name=name):
            logger.debug("calling Id")
            return lookup(name, env)
        case Fun(par_name=par_name, body=body):
            logger.debug("calling Fun")
            return CloV(par_name, body, env)
        case App(f_expr=f_expr, val=val):
            f = interp(f_expr, env)
            match f:
                case CloV(param=param, body=body, env=fenv):
                    # env = dynamic scop
                    # fenv = static scope
                    return interp(body, dict(fenv, **{param: interp(val, env)}))
                case _:
                    raise ClosureError(f"not a closure: {f}")
        case If0(cond=cond, true_body=true_body, false_body=false_body):
            match interp(cond, env):
                case NumV(n=0):
                    return interp(true_body, env)
                case NumV(n=n):
                    return interp(false_body, env)
                case _:
                    raise NotNumExpression("if0 {cond} {env} doesn't return a NumV value")
        case Rec(f=f, par_name=par_name, body=body):
            cloV = CloV(par_name, body, env)
            nenv = dict(env, **{f : cloV})
            cloV.env = nenv
            return interp(expr, nenv)
    
        case _:
            raise UnknownStatementException(f"Unknown statement {expr}")

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

# testing if0
assert interp(If0(Num(0), Num(10), Num(5)), {}).n == 10
assert interp(If0(Num(3), Num(10), Num(5)), {}).n == 5

# test Rec
App(Rec("sum", 
        "x", 
        If0(
            Id("x"),
            Num(0),
            App(Id("sum"), Add(Id("x"), Num(1)))
        )
        ) , Num(10)).n = 55

# interp(App(Fun("x", Add(Id("x"), Num(10))), Num(5)), {})