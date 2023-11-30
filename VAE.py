from typing import Dict

# type of environment
Env = Dict[str, int]

# exception
class InterPreterException(Exception):
    pass

class FreeIdentifierError(InterPreterException):
    pass

class UnknownStatementException(InterPreterException):
    pass

# expression types
class Expression():
    pass

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
    
def interp(expr : Expression, env: Env) -> int:
    if isinstance(expr, Num):
        return expr.n
    elif isinstance(expr, Add):
        return interp(expr.left, env) + interp(expr.right, env)
    elif isinstance(expr, Sub):
        return interp(expr.left, env) - interp(expr.right, env)
    elif isinstance(expr, Id):
        return lookup(expr.name, env)
    elif isinstance(expr, Val):
        res = interp(expr.expr, env)
        return interp(expr.body, dict(env, **{expr.name : res}))
    else:
        raise UnknownStatementException(f"Unknown statement {expr}")
    
def lookup(var_name:str, env: Env):
    try:
        return env[var_name]
    except KeyError:
        raise FreeIdentifierError(f"free identifier {var_name}")
    
if __name__ == "__main__":
    assert interp(Num(10), {} ) == 10
    assert interp(Add(Num(10), Num(20)), {}) == 30
    assert interp(Sub(Num(10), Num(20)), {}) == -10
    assert interp(Add(Num(0), Num(3)), {}) == 3

    assert interp(Val("x",Num(1), Id("x")), {}) == 1
    assert interp(Val("x",Num(1), Add(Id("x"), Id("x"))), {}) == 2
    assert interp(Val("x",Num(1),
                    Add(
                        Val("x",Num(4),Add(Id("x"), Num(5))),
                        Id("x"))), 
                        {}) == 10