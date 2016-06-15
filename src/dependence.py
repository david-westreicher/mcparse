from .utils import function_ranges
from .parser import parsefile, prettyast
from .parser import ArrayDef, ArrayExp, FunDef, RetStmt, IfStmt, WhileStmt, ForStmt, DeclStmt, CompStmt, FunCall, BinOp, UnaOp, Literal, Variable


def getchildren(ast):
    if type(ast) in [str, int, float, list]:
        return []
    children = [val for name, val in ast._asdict().items()]
    if len(children) == 1 and type(children[0]) is list:
        return children[0]
    return children


def getindex_of_for(initexpr, conditionexpr, afterexp, stmt):
    if type(afterexp) == BinOp and afterexp.operation == '=':
        return afterexp.lhs.name
    return None


def expression_to_str(expression):
    if type(expression) == Variable:
        return expression.name
    if type(expression) == BinOp:
        return expression_to_str(expression.lhs) + expression.operation + expression_to_str(expression.rhs)
    if type(expression) == Literal:
        return str(expression.val)


def arrayexpr_to_str(ast):
    return '%s[%s]' % (ast.name, expression_to_str(ast.expression))


def vars_of_expression(expression):
    if type(expression) == Variable:
        yield expression.name
    for child in getchildren(expression):
        for var in vars_of_expression(child):
            yield var

def all_arrayexp(ast, res=None):

    if type(ast) in [str, int, float, list]:
        return

    if res is None:
        res = []

    if type(ast) == ArrayExp:
        res.append(ast)
        return res

    for child in getchildren(ast):
        all_arrayexp(child, res)

    return res

class Dependence:
    def __init__(self, deptype, source, sink, loop_indices, isloopdep):
        self.type = deptype
        self.source = source
        self.sink = sink
        self.cat = None
        if isloopdep:
            self.cat = Dependence.category(source, sink, loop_indices)

    @staticmethod
    def category(source, sink, loop_indices):
        sourcevars = set(vars_of_expression(source.expression))
        sinkvars = set(vars_of_expression(sink.expression))
        allvars = sourcevars | sinkvars
        depvars = allvars & set(loop_indices)
        # print(depvars)
        if len(depvars) == 0:
            return 'ZIV'
        if len(depvars) == 1:
            return 'SIV'
        return 'MIV'

    def __str__(self):
        return '%s: %s -> %s, %s' % (self.type, arrayexpr_to_str(self.source), arrayexpr_to_str(self.sink), self.cat)
    def __repr__(self):
        return str(self)


def collect_dependencies(ast, forscope=None, loop_index_stack=None):

    if type(ast) in [str, int, float, list]:
        return

    if forscope is None:
        forscope = [([], [])]
    if loop_index_stack is None:
        loop_index_stack = []
    lhs, rhs = forscope[-1]

    if type(ast) == ForStmt:
        indexvar = getindex_of_for(ast.initexpr, ast.conditionexpr, ast.afterexpr, ast.stmt)
        loop_index_stack.append(indexvar)
        forscope.append(([], []))

    rhsexpr = None
    if type(ast) == DeclStmt:
        rhsexpr = ast.expression
    if type(ast) == BinOp:
        if ast.operation == '=':
            rhsexpr = ast.rhs

    if rhsexpr is not None:
        for arrexp in all_arrayexp(rhsexpr):
            for upperlhs, _ in forscope[:1]:
                for flow in upperlhs:
                    if arrexp.name == flow.name:
                        yield Dependence('flow', flow, arrexp, loop_index_stack, False)
            for upperlhs, _ in forscope[1:]:
                for flow in upperlhs:
                    if arrexp.name == flow.name:
                        yield Dependence('anti', arrexp, flow, loop_index_stack, True)
        for arrexp in all_arrayexp(rhsexpr):
            rhs.append(arrexp)

    if type(ast) == BinOp:
        if ast.operation == '=':
            if type(ast.lhs) == ArrayExp:
                for _, upperrhs in forscope[:1]:
                    for anti in upperrhs:
                        if ast.lhs.name == anti.name:
                            yield Dependence('anti', anti, ast.lhs, loop_index_stack, False)
                for _, upperrhs in forscope[1:]:
                    for anti in upperrhs:
                        if ast.lhs.name == anti.name:
                            yield Dependence('flow', ast.lhs, anti, loop_index_stack, True)
                for upperlhs, _ in forscope[:1]:
                    for output in upperlhs:
                        if ast.lhs.name == output.name:
                            yield Dependence('output', output, ast.lhs, loop_index_stack, False)
                for upperlhs, _ in forscope[1:]:
                    for output in upperlhs:
                        if ast.lhs.name == output.name:
                            yield Dependence('output', output, ast.lhs, loop_index_stack, True)
                lhs.append(ast.lhs)

            '''
            for el in lhs:
                print(arrayexpr_to_str(el))
            for el in rhs:
                print(arrayexpr_to_str(el))
            print('__')
            '''
            return

    for child in getchildren(ast):
        for childsubs in collect_dependencies(child, forscope, loop_index_stack):
            yield childsubs

    if type(ast) == ForStmt:
        forscope.pop()
        loop_index_stack.pop()


def dependence(ast, verbose=0):

    deps = list(collect_dependencies(ast))
    if verbose:
        # print(prettyast(ast))
        print('\n' + ' Loop Dependencies '.center(40, '#'))
        for dep in deps:
            print(dep)

    return deps

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to analyze for loop dependencies")
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    ast = parsefile(args.filename, verbose=args.verbose)
    dependence(ast, verbose=1)
