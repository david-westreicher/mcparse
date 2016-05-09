from collections import namedtuple
from warnings import warn
from .parser import parsefile, prettyast
from .parser import FunDef, RetStmt, IfStmt, WhileStmt, ForStmt, DeclStmt, CompStmt, FunCall, BinOp, UnaOp, Literal, Variable


class ScopeException(Exception):
    pass


class ReturnException(Exception):
    pass


class CallException(Exception):
    pass


class FunctionDefinitionException(Exception):
    pass

FunctionSignature = namedtuple('FunctionSignature', ['name', 'returntype', 'params'])


class Scope(object):

    def __init__(self, ast):
        self.varindex = 0
        self.labindex = 0
        self.scopestack = [set()]
        self.function_sigs = []
        self.function_stack = []
        self.function_prepass(ast)

    def open(self):
        self.scopestack.append(set())

    def close(self):
        del self.scopestack[-1]

    def function_prepass(self, ast):
        if type(ast) == CompStmt:
            for stmt in ast.stmts:
                self.function_prepass(stmt)
        if type(ast) == FunDef:
            name, returntype, params = ast.name, ast.ret_type, ast.params
            for fname, _, _ in self.function_sigs:
                if fname == name:
                    raise FunctionDefinitionException('The function "%s" is already defined' % name)
            self.function_sigs.append(FunctionSignature(name, returntype, params))

    def function_begin(self, name, returntype, params):
        # TODO should be fixed in the grammar
        if len(self.function_stack) > 0:
            raise FunctionDefinitionException('The function "%s" is defined in a function scope of "%s" (no nesting)' % (name, self.function_stack[-1]))
        paramnames = set()
        for i, (_, pname) in enumerate(params):
            if pname in paramnames:
                raise FunctionDefinitionException(
                    'The parameter "%s" is already defined in function "%s %s(%s, ...)"' %
                    (pname, returntype, name, ', '.join(['%s %s' % (t, n) for t, n in params[:i]])))
            paramnames.add(pname)
        funcswithname = filter(lambda (fname, _, __): name == fname, self.function_sigs)
        if len(funcswithname) == 0:
            raise CallException('The function "%s" should be defined in the top-level' % name)
        self.function_stack.append(funcswithname[0])
        self.open()

    def function_end(self, three):
        returntype = self.function_stack[-1].returntype
        lastop, _, _, _ = three[-1]
        if lastop != 'return':
            # TODO maybe all previous if/while/for clauses had an exhaustive return
            if returntype == 'void':
                three.append(['return', None, None, None])
            else:
                raise ReturnException('The function %s should return a value of type [%s]' % (self.function_stack[-1], returntype))
        self.function_stack.pop()
        self.close()

    def check_function_return(self, expression):
        returntype = self.function_stack[-1].returntype
        if returntype == 'void':
            if expression is not None:
                raise ReturnException('The function should return a value of type [%s]' % returntype)
        else:
            if expression is not None:
                # TODO returntype is 'int' or 'float -> type of expression should be appropiate
                pass
            else:
                raise ReturnException('The function should return a value of type [%s]' % returntype)

    def check_function_call(self, result, name, expressions):
        for fname, rettype, fparams in self.function_sigs:
            if name != fname:
                continue
            # TODO rettype is 'int' or 'float -> type of expression should be appropiate
            if len(fparams) != len(expressions):
                raise CallException('The function "%s" accepts %d parameters, but you only gave %d' %
                                    (name, len(fparams), len(expressions)))
            if rettype == 'void' and result is not None:
                raise CallException('The function "%s" returns "void". Don\'t use the return value' %
                                    (name))
            return
        raise CallException('The function "%s" is not defined' % name)

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

        Operation   Arg1        Arg2        Result      Effect

        jump                                label       pc := label
        jumpfalse   var                     label       pc := (pc+1) if var else label
        label                               label
        function                            fname
        call                                fname       pc := fp.push(fname)
        end-fun
        return                                          pc := fp.pop()
        push                                var         stack.push(var)
        pop                                 var         var := stack.pop()
        assign      x                       var         var := x
        binop       x           y           var         var := x * y
        unop        x                       var         var := -x

            binop € ['+', '-', '*', '/', '%', '==', '!=', '<=', '>=', '<', '>']
            unop € ['-', '!']

        Function calls are implemented as follows:
            Suppose we have the function:
                int foo(int x, int y){ ... return z;}
            When we call 'int res = foo(4,5)':
                * '4' and '5' get pushed onto the stack (push 4, push 5)
                * we jump into the definition of 'foo' (call foo)
                * 'foo' pops '4' and '5' from the stack (pop x, pop y)
                * 'foo' puts the value of 'z' on the stack (push z)
                * we pop the stack and set 'res' to that value (pop res)
    '''
    scope = Scope(ast) if scope is None else scope
    three = [] if three is None else three

    if type(ast) == FunDef:
        scope.function_begin(ast.name, ast.ret_type, ast.params)
        three.append(['function', None, None, ast.name])
        for paramtype, paramname in ast.params:
            scope.add(paramname)
            three.append(['pop', None, None, paramname])
        asttothree(ast.stmts, three, scope)
        # check if last statement is a return
        scope.function_end(three)
        three.append(['end-fun', None, None, None])

    if type(ast) == RetStmt:
        scope.check_function_return(ast.expression)
        if ast.expression != None:
            tmpvar = scope.newtemp()
            asttothree(ast.expression, three, scope, tmpvar)
            three.append(['push', None, None, tmpvar])
        three.append(['return', None, None, None])

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

    if type(ast) == FunCall:
        scope.check_function_call(result, ast.name, ast.args)
        for expression in ast.args:
            tmpvar = scope.newtemp()
            asttothree(expression, three, scope, tmpvar)
            three.append(['push', None, None, tmpvar])
        three.append(['call', None, None, ast.name])
        if result is not None:
            three.append(['pop', None, None, result])

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
    if op in ['function', 'return', 'end-fun', 'push', 'pop', 'call', 'label', 'jump', 'jumpfalse']:
        if res is None:
            # return, end-fun
            return '{:.10s}'.format(op)
        if arg1 is None:
            return '{:.10s}\t{:.6s}'.format(op, str(res))
        else:
            # jumpfalse
            return '{:.10s}\t{:.6s}\t{:.6s}'.format(op, str(arg1), res)
    elif op == 'assign':
        return '{:.6s}\t:=\t{:.6s}'.format(res, str(arg1))
    elif arg2 is not None:
        # binary operation
        return '{:.6s}\t:=\t{:.6s}\t{:s}\t{:.6s}'.format(res, str(arg1), op, str(arg2))
    else:
        # unary operation
        return '{:.6s}\t:=\t{:s}\t{:.6s}'.format(res, op, str(arg1))


def printthree(three, nice=True):
    if nice:
        indent = False
        for op, arg1, arg2, res in three:
            print(('\t' if indent else '') + prettythreestr(op, arg1, arg2, res))
            indent = not indent if op in ['function', 'end-fun'] else indent
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
