from typing import Dict, List
import logging

# create logger
logging.basicConfig()

logger = logging.getLogger("F1VAE")
logger.setLevel(logging.DEBUG)

# type of environment
Env = Dict[str, int]

# Expression
class Expression():
    pass

# type of functions
class FunDef():
    def __init__(self, f_name:str, par_name: str, body: Expression):
        self.f_name = f_name
        self.par_name = par_name
        self.body = body
    def __str__(self) -> str:
        return f"FunDef({self.f_name}, {self.par_name}, {self.body})"

FEnv = Dict[str, FunDef]

# Expression classes
class Num(Expression):
    def __init__(self, n:int):
        self.n = n
    def __str__(self) -> str:
        return f"Num({self.n})"
    
class Add(Expression):
    def __init__(self, left:Expression, right:Expression):
        self.left = left
        self.right = right
    def __str__(self) -> str:
        return f"Add({self.left!s}, {self.right!s})"

class Sub(Expression):
    def __init__(self, left:Expression, right:Expression):
        self.left = left
        self.right = right
    def __str__(self) -> str:
        return f"Sub({self.left!s}, {self.right!s})"

class Id(Expression):
    def __init__(self, name: str):
        self.name = name
    def __str__(self) -> str:
        return f"Id({self.name!s})"
    
class Val(Expression):
    def __init__(self, name:str, expr:Expression, body:Expression):
        self.name = name
        self.expr = expr
        self.body = body
    def __str__(self) -> str:
        return f"Val({self.name!s}, {self.expr!s}, {self.body!s})"

class Call(Expression):
    def __init__(self, f: str, a: Expression):
        self.f = f
        self.a = a
    def __str__(self) -> str:
        return f"Call({self.f}, {self.a!s})"

# execution exception
# exception
class InterPreterException(Exception):
    pass

class FreeIdentifierError(InterPreterException):
    pass

class UnknownStatementException(InterPreterException):
    pass
 
class UnknownFunction(InterPreterException):
    pass

def interp(expr : Expression, env: Env, fs: FEnv) -> int:
    logger.debug(f"calling interp with {expr=!s} {env=!s} {fs=!s}")
    match expr:
        case Num(n=n):
            logger.debug("calling Num")
            return n
        case Add(left=left, right=right):
            logger.debug("calling Add")
            return interp(left, env, fs) + interp(right, env, fs)
        case Sub(left=left, right=right):
            logger.debug("calling Sub")
            return interp(left, env, fs) - interp(right, env, fs)
        case Id(name=name):
            logger.debug("calling Id")
            return lookup(name, env)
        case Val(name=name, expr=expr, body=body):
            logger.debug("calling Val")
            res = interp(expr, env, fs)
            return interp(body, dict(env, **{name : res}), fs)
        case Call(f=f, a=a):
            logger.debug("calling Call")
            func = lookupFD(f, fs)
            aval = interp(a, env, fs)
            return interp(func.body, dict(env, **{func.par_name: aval}), fs)
        case _:
            raise UnknownStatementException(f"Unknown statement {expr}")


def lookupFD(f_name: str, fds: FEnv) -> FunDef:
    logger.debug(f"lookupFD called: {f_name=!s} {fds=!s}")
    
    try:
        return fds[f_name]
    except KeyError:
        raise UnknownFunction("unknow function {f_name}")
        
def lookup(var_name:str, env: Env):
    logger.debug(f"lookup called with {var_name=!s} {env=!s}")
    try:
        return env[var_name]
    except KeyError:
        raise FreeIdentifierError(f"free identifier {var_name}")

if __name__ == "__main__": 
    assert interp(Num(10), {}, [] ) == 10
    assert interp(Add(Num(10), Num(20)), {}, []) == 30
    assert interp(Sub(Num(10), Num(20)), {}, []) == -10
    assert interp(Add(Num(0), Num(3)), {}, []) == 3

    assert interp(Val("x",Num(1), Id("x")), {}, []) == 1
    assert interp(Val("x",Num(1), Add(Id("x"), Id("x"))), {}, []) == 2
    assert interp(Val("x",Num(1),
                    Add(
                        Val("x",Num(4),Add(Id("x"), Num(5))),
                        Id("x"))), 
                        {}, []) == 10

    fs = {}
    fs["double"] = FunDef("double", "x", Add(Id("x"), Id("x")))
    fs["free-var"] = FunDef("free-var", "x", Add(Id("x"), Id("y")))

    assert interp(Call("double", Num(10)), {}, fs) == 20
    assert interp(
        Add(
            Call("double", Num(10)),
            Num(3)),
        {}, fs) == 23

    # test dynamic scope
    assert interp(
        Val("y", Num(10), Call("free-var", Num(2))),
        {}, fs
    ) == 12