from parser import parsefile, prettyast
from parser import IfStmt, DeclStmt, CompStmt, BinOp, UnaOp, Literal, Variable
import warnings


class Scope(object):
    def __init__(self):
        self.varindex = 0
        self.labindex = 0
        self.scopestack = [set()]

    def open(self):
        self.scopestack.append(set())

    def close(self):
        del self.scopestack[-1]

    def newtemp(self):
        varname = 'tmp'+str(self.varindex).zfill(3)
        self.varindex += 1
        return varname

    def newlabel(self):
        varname = 'lab'+str(self.labindex).zfill(3)
        self.labindex += 1
        return varname

    def add(self, variable):
        self.scopestack[-1].add(variable)

    def __contains__(self, variable):
        for scope in reversed(self.scopestack):
            if variable in scope:
                return True
        return False


def asttothree(ast, three=[], scope=Scope(), result=None):
    if type(ast) == IfStmt:
        tmpvar = scope.newtemp()
        label1 = scope.newlabel()
        label2 = scope.newlabel()

        asttothree(ast.expression, three, scope, tmpvar)
        three.append(['jumpfalse', tmpvar, None, label1])

        scope.open()
        asttothree(ast.if_stmt, three, scope)
        three.append(['jump', None, None, label2])
        three.append(['label', None, None, label1])
        scope.close()

        scope.open()
        asttothree(ast.else_stmt, three, scope)
        three.append(['label', None, None, label2])
        scope.close()

    if type(ast) == DeclStmt:
        if ast.variable in scope:
            raise Exception('Variable "%s" is already declared' % ast.variable)
        scope.add(ast.variable)
        if ast.expression is not None:
            tmpvar = scope.newtemp()
            asttothree(ast.expression, three, scope, tmpvar)
            three.append(['assign', tmpvar, None, ast.variable])
        else:
            three.append(['load', 'default-'+ast.type, None, ast.variable])

    if type(ast) == CompStmt:
        scope.open()
        for stmt in ast.stmts:
            asttothree(stmt, three, scope)
        scope.close()

    if type(ast) == BinOp:
        if ast.operation == '=' and type(ast.lhs) == Variable:
            tmpvarrhs = scope.newtemp()
            asttothree(ast.rhs, three, scope, tmpvarrhs)
            three.append(['assign', tmpvarrhs, None, ast.lhs.name])
        else:
            if result is None:
                warnmsg = 'No result set, computation is unnecessary.\n %s' % prettyast(ast)
                warnings.warn(warnmsg)
            tmpvarlhs = scope.newtemp()
            tmpvarrhs = scope.newtemp()
            asttothree(ast.lhs, three, scope, tmpvarlhs)
            asttothree(ast.rhs, three, scope, tmpvarrhs)
            three.append([ast.operation, tmpvarlhs, tmpvarrhs, result])

    if type(ast) == UnaOp:
        tmpvar = scope.newtemp()
        asttothree(ast.expression, three, scope, tmpvar)
        three.append([ast.operation, tmpvar, None, result])

    if type(ast) == Literal:
        if result is None:
            raise Exception('No result set')
        three.append(['load', str(ast.val), None, result])

    if type(ast) == Variable:
        if result is None:
            raise Exception('No result set')
        if ast.name not in scope:
            raise Exception('Variable "%s" not in scope' % ast.name)
        three.append(['assign', ast.name, None, result])
    return three


def printthree(three):
    for row in three:
        print(''.join([' '*10 if el is None else el.ljust(10) for el in row]))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to translate to three-address code")
    args = parser.parse_args()
    three = asttothree(parsefile(args.filename))
    printthree(three)
