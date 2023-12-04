from typing import Dict, Callable, List
import logging

# create logger
logger = logging.getLogger("F1VAE")
logger.setLevel(logging.DEBUG)

# type of environment
Env = Dict[str, int]

class Expression():
    pass

# type of functions
class Fdef():
    def __init__(self, f_name:str, par_name: str, body: Expression):
        self.f_name = f_name
        self.par_name = par_name
        self.body = body

FDs = List[Fdef]

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

class App(Expression):
    def __init__(self, f_name: str, val: Expression):
        self.f_name = f_name
        self.val = val
    def __str__(self) -> str:
        return f"App({self.f_name}, {self.val!s})"

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

def interp(expr : Expression, env: Env, fs: FDs) -> int:
    logger.debug(f"calling interp with {expr=!s} {env=!s} {fs=!s}")
    if isinstance(expr, Num):
        return expr.n
    elif isinstance(expr, Add):
        logger.debug("calling Add")
        print("Add")
        return interp(expr.left, env, fs) + interp(expr.right, env, fs)
    elif isinstance(expr, Sub):
        return interp(expr.left, env, fs) - interp(expr.right, env, fs)
    elif isinstance(expr, Id):
        return lookup(expr.name, env)
    elif isinstance(expr, Val):
        res = interp(expr.expr, env, fs)
        return interp(expr.body, dict(env, **{expr.name : res}), fs)
    elif isinstance(expr, App):
        func = lookupFD(expr.f_name, fs)
        aval = interp(expr.val, env, fs)
        return interp(func.body, {func.par_name: aval}, fs) # static scope
        # return interp(func.body, dict(env, **{func.f_name: aval}), fs) # dynamic scope

def lookupFD(f_name: str, fds: FDs) -> Fdef:
    logger.debug(f"lookupFD called: {f_name=!s} {fds=!s}")
    if fds == []:
        raise UnknownFunction(f"lookupFD - Unknown function: {f_name}")
    else:
        if f_name == fds[0].f_name:
            return fds[0]
        else:
            lookupFD(f_name, fds[1:])

    """
    # pythonic version
    # l = [f for f in fds if f_name == f.f_name]
    
    if len(l) == 0:
        raise UnknownFunction(f"Unknown function: {f_name}")
    else:
        return l[0]
    """

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

    fs = [Fdef("double", "x", Add(Id("x"), Id("x")))]

    assert interp(App("double", Num(10)), {}, fs) == 20
    assert interp(Add(
        App("double", Num(10)),
        Num(3)),
        {}, fs) == 23
