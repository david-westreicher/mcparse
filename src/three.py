from .parser import parsefile, prettyast
from .parser import IfStmt, WhileStmt, ForStmt, DeclStmt, CompStmt, BinOp, UnaOp, Literal, Variable
import warnings


class ScopeException(Exception):
    pass


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
        varname = '.t' + str(self.varindex)
        self.varindex += 1
        return varname

    def newlabel(self):
        varname = 'L' + str(self.labindex)
        self.labindex += 1
        return varname

    def add(self, variable):
        self.scopestack[-1].add(variable)

    def __contains__(self, variable):
        for scope in reversed(self.scopestack):
            if variable in scope:
                return True
        return False


def asttothree(ast, three=None, scope=None, result=None, verbose=0):
    ''' converts an AST into a list of 3-addr.-codes

        ['jump'     , None, None, result]
            Jump to label 'result'
            ['jump', None, None, 'L3']      ->  jump        L3

        ['jumpfalse', arg1, None, result]
            Jump to label 'result' if value/register 'arg1' equals to false
            ['jumpfalse', 1, None, 'L2']    ->  jumpfalse   1   L2

        ['label'    , None, None, result]
            A label with the name 'result'
            ['label', None, None, 'L1']     ->  label       L1

        ['assign'   , arg1, None, result]
            Assigns the value/register 'arg1' to the register 'result'
            ['assign', 'y', None, 'x']      ->  x   :=      y

        [binop      , arg1, arg2, result]
            binop can be any of ['+', '-', '*', '/', '%', '==', '!=', '<=', '>=', '<', '>']
            Assigns the result of the operation 'binop' (of the value/register 'arg1'
            and the value/register 'arg2') to the register 'result'
            ['+', 4, t1, 'x']               ->  x   :=      4   +   t1

        [unop       , arg1, None, result]
            unop can be any of ['-', '!']
            Assigns the result of the operation 'unnop' (of the value/register 'arg1')
            to the register 'result'
            ['-', 4, None, 'x']             ->  x   :=      -       4
    '''

    scope = Scope() if scope is None else scope
    three = [] if three is None else three

    if type(ast) == IfStmt:
        tmpvar = scope.newtemp()
        endiflabel = scope.newlabel()

        if ast.if_stmt is None and ast.else_stmt is None:
            asttothree(ast.expression, three, scope, tmpvar)
        # TODO could optimize further if if_stmt is None (-> empty if compound)
        elif ast.else_stmt is None:
            asttothree(ast.expression, three, scope, tmpvar)
            three.append(['jumpfalse', tmpvar, None, endiflabel])

            scope.open()
            asttothree(ast.if_stmt, three, scope)
            scope.close()

            three.append(['label', None, None, endiflabel])
        else:
            elselabel = scope.newlabel()

            asttothree(ast.expression, three, scope, tmpvar)
            three.append(['jumpfalse', tmpvar, None, elselabel])

            scope.open()
            asttothree(ast.if_stmt, three, scope)
            three.append(['jump', None, None, endiflabel])
            scope.close()

            three.append(['label', None, None, elselabel])
            scope.open()
            asttothree(ast.else_stmt, three, scope)
            scope.close()

            three.append(['label', None, None, endiflabel])

    if type(ast) == WhileStmt:
        startwhilelabel = scope.newlabel()
        three.append(['label', None, None, startwhilelabel])

        tmpvar = scope.newtemp()
        endwhilelabel = scope.newlabel()
        asttothree(ast.expression, three, scope, tmpvar)
        three.append(['jumpfalse', tmpvar, None, endwhilelabel])

        scope.open()
        asttothree(ast.stmt, three, scope)
        three.append(['jump', None, None, startwhilelabel])
        scope.close()

        three.append(['label', None, None, endwhilelabel])

    if type(ast) == ForStmt:
        # initialization
        asttothree(ast.initexpr, three, scope, None)
        # condition
        conditionlabel = scope.newlabel()
        three.append(['label', None, None, conditionlabel])
        condvar = scope.newtemp()
        asttothree(ast.conditionexpr, three, scope, condvar)
        endforlabel = scope.newlabel()
        three.append(['jumpfalse', condvar, None, endforlabel])
        # body
        scope.open()
        asttothree(ast.stmt, three, scope)
        # afterthought
        asttothree(ast.afterexpr, three, scope, None)
        three.append(['jump', None, None, conditionlabel])
        scope.close()
        # end
        three.append(['label', None, None, endforlabel])

    if type(ast) == DeclStmt:
        if ast.variable in scope.scopestack[-1]:
            # TODO double declaration should be valid if in new scope
            raise ScopeException('Variable "%s" is already declared' % ast.variable)
        if ast.expression is not None:
            tmpvar = scope.newtemp()
            asttothree(ast.expression, three, scope, tmpvar)
            three.append(['assign', tmpvar, None, ast.variable])
        else:
            three.append(['assign', 'default-' + ast.type, None, ast.variable])
        scope.add(ast.variable)

    if type(ast) == CompStmt:
        scope.open()
        for stmt in ast.stmts:
            asttothree(stmt, three, scope)
        scope.close()

    if type(ast) == BinOp:
        if ast.operation == '=' and type(ast.lhs) == Variable:
            # this is an assignment posing as a binop
            tmpvarrhs = scope.newtemp()
            varname = ast.lhs.name
            if varname not in scope:
                raise ScopeException('Variable "%s" not in scope (probably not declared before)' % varname)
            asttothree(ast.rhs, three, scope, tmpvarrhs)
            three.append(['assign', tmpvarrhs, None, varname])
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
        if result is None:
            warnmsg = 'No result set, computation is unnecessary.\n %s' % prettyast(ast)
            warnings.warn(warnmsg)
        tmpvar = scope.newtemp()
        asttothree(ast.expression, three, scope, tmpvar)
        three.append([ast.operation, tmpvar, None, result])

    if type(ast) == Literal:
        if result is None:
            warnmsg = 'No result set, computation is unnecessary.\n %s' % prettyast(ast)
            warnings.warn(warnmsg)
        three.append(['assign', ast.val, None, result])

    if type(ast) == Variable:
        if result is None:
            raise Exception('no result set')
        if ast.name not in scope:
            raise ScopeException('Variable "%s" not in scope (probably not declared before)' % ast.name)
        three.append(['assign', ast.name, None, result])

    if verbose > 0:
        print('\n' + ' 3-address-code '.center(40, '#'))
        printthree(three)
    return three


def prettythreestr(op, arg1, arg2, res):
    if op in ['assign']:
        return "%s\t:=\t%s" % (res, arg1)
    elif op in ['label', 'jump']:
        return "%s\t\t%s" % (op, res)
    elif op == 'jumpfalse':
        return "%s\t%s\t%s" % ('jumpfalse', arg1, res)
    elif arg2 is not None:
        # binary operation
        return "%s\t:=\t%s\t%s\t%s" % (res, arg1, op, arg2)
    else:
        # unary operation
        return "%s\t:=\t%s\t%s" % (res, op, arg1)


def printthree(three, nice=True):
    if nice:
        for op, arg1, arg2, res in three:
            print(prettythreestr(op, arg1, arg2, res))
    else:
        for row in three:
            print(''.join([' ' * 10 if el is None else str(el).ljust(10) for el in row]))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to translate to three-address code")
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    three = asttothree(parsefile(args.filename, verbose=args.verbose), verbose=1)
