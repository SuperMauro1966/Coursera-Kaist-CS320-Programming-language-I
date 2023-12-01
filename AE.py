class Expression():
    pass

class Num(Expression):
    def __init__(self, n):
        self.n = n

class Add(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Sub(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right

def interp(expr : Expression):
    if isinstance(expr, Num):
        return expr.n
    elif isinstance(expr, Add):
        return interp(expr.left) + interp(expr.right)
    elif isinstance(expr, Sub):
        return interp(expr.left) - interp(expr.right)
    
if __name__ == "__main__":
    assert interp(Num(10)) == 10
    assert interp(Add(Num(10), Num(20))) == 30
    assert interp(Sub(Num(10), Num(20))) == -10
    assert interp(Add(Num(0), Num(3))) == 3