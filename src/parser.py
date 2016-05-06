from collections import namedtuple
from parsimonious import Grammar, NodeVisitor

# TODO expression precedence is not expressed: - (unary) > * > +
# i.e.: -5.0*10.0 => (- (* 5 10))
# TODO identifier should really be a variable in most cases
# TODO maybe can ommit childs[0] visits?

mcgrammar = Grammar(
    """
    statement        = fun_def / if_stmt / while_stmt / for_stmt / decl_stmt / compound_stmt / expr_stmt
    fun_def          = type_or_void _ identifier _ "(" _ params _ ")" _ compound_stmt
    params           = param ( _ "," _ param )*
    param            = type _ identifier
    if_stmt          = "if" _ paren_expr _ statement (_ "else" _ statement)?
    while_stmt       = "while" _ paren_expr _ statement
    for_stmt         = "for" _ "(" _ expression _ ";" _ expression _ ";" _ expression _ ")" _ statement
    decl_stmt        = type _ identifier (_ "=" _ expression)? _ ";"
    compound_stmt    = "{" _ (statement _)* "}"
    expr_stmt        = expression _ ";"
    type             = "int" / "float"
    type_or_void     = type / "void"
    expression       = call_expr / binary_operation / single_expr
    call_expr        = identifier _ "(" _ arguments _ ")"
    arguments        = expression ( _ "," _ expression )*
    binary_operation = single_expr _ bin_op _ expression
    single_expr      = paren_expr / unary_expr / literal / variable
    bin_op           = "+" / "-" / "*" / "/" / "%" / "==" / "!=" / "<=" / ">=" / "<" / ">" / "="
    paren_expr       = "(" _ expression _ ")"
    unary_expr       = unop _ expression
    unop             = "-" / "!"
    literal          = float_lit / int_lit
    int_lit          = ~"\d+"
    float_lit        = ~"\d+\.\d*"
    variable         = ~"[a-zA-Z_][a-zA-Z_0-9]*" 
    identifier       = ~"[a-zA-Z_][a-zA-Z_0-9]*"
    _                = ~"\s*"
    """)

FunDef = namedtuple('FunDef', ['ret_type', 'name', 'params', 'stmts'])
Param = namedtuple('Param', ['type', 'name'])
IfStmt = namedtuple('IfStmt', ['expression', 'if_stmt', 'else_stmt'])
WhileStmt = namedtuple('WhileStmt', ['expression', 'stmt'])
ForStmt = namedtuple('ForStmt', ['initexpr', 'conditionexpr', 'afterexpr', 'stmt'])
DeclStmt = namedtuple('DeclStmt', ['type', 'variable', 'expression'])
CompStmt = namedtuple('CompStmt', ['stmts'])
FunCall = namedtuple('FunCall', ['name', 'args'])
BinOp = namedtuple('BinOp', ['operation', 'lhs', 'rhs'])
UnaOp = namedtuple('UnaOp', ['operation', 'expression'])
Literal = namedtuple('Literal', ['type', 'val'])
Variable = namedtuple('Variable', ['name'])


class ASTFormatter(NodeVisitor):
    grammar = mcgrammar

    def rightrecursive_flatten(self, children):
        head, tail = children
        if tail is None:
            return [head]
        if isinstance(tail, list):
            return [head] + tail
        return children

    def visit_fun_def(self, node, childs):
        ret_type, name, params, stmts = (childs[i] for i in [0, 2, 6, 10])
        return FunDef(ret_type, name, params, stmts)

    def visit_params(self, node, childs):
        return self.rightrecursive_flatten(childs)

    def visit_param(self, node, childs):
        paramtype, name = (childs[i] for i in [0, 2])
        return Param(paramtype, name)

    def visit_if_stmt(self, node, childs):
        expression, if_stmt, else_stmt = (childs[i] for i in [2, 4, 5])
        return IfStmt(expression, if_stmt, else_stmt)

    def visit_while_stmt(self, node, childs):
        expression, stmt = (childs[i] for i in [2, 4])
        return WhileStmt(expression, stmt)

    def visit_for_stmt(self, node, childs):
        initexpr, conditionexpr, afterexp, stmt = (childs[i] for i in [4, 8, 12, 16])
        return ForStmt(initexpr, conditionexpr, afterexp, stmt)

    def visit_decl_stmt(self, node, childs):
        vartype, varname, expression = (childs[i] for i in [0, 2, 3])
        return DeclStmt(vartype, varname, expression)

    def visit_compound_stmt(self, node, childs):
        stmts = childs[2]
        if stmts is None:
            return None
        if not isinstance(stmts, list):
            stmts = [stmts]
        return CompStmt(stmts)

    def visit_type(self, node, childs):
        return node.text

    def visit_type_or_void(self, node, childs):
        return node.text

    def visit_call_expr(self, node, childs):
        name, args = (childs[i] for i in [0, 4])
        return FunCall(name, args)

    def visit_arguments(self, node, childs):
        return self.rightrecursive_flatten(childs)

    def visit_binary_operation(self, node, childs):
        operation, lhs, rhs = (childs[i] for i in [2, 0, 4])
        return BinOp(operation, lhs, rhs)

    def visit_bin_op(self, node, childs):
        return node.text

    def visit_unary_expr(self, node, childs):
        return UnaOp(*(childs[i] for i in [0, 2]))

    def visit_unop(self, node, childs):
        return node.text

    def visit_int_lit(self, node, childs):
        return Literal('int', int(node.text))

    def visit_float_lit(self, node, childs):
        return Literal('float', float(node.text))

    def visit_variable(self, node, childs):
        return Variable(node.text)

    def visit_identifier(self, node, childs):
        return node.text

    def generic_visit(self, node, childs):
        res = [x for x in childs if x is not None]
        if len(res) == 0:
            return None
        if len(res) == 1:
            return res[0]
        return res


def prettyast(ast, level=0, tostr=True):
    res = []
    if isinstance(ast, list):
        for el in ast:
            res.extend(prettyast(el, level, tostr=False))
    elif isinstance(ast, tuple):
        res.append('\t' * level + type(ast).__name__)
        for el in ast:
            res.extend(prettyast(el, level + 1, tostr=False))
    else:
        res.append('\t' * level + str(ast))
    if tostr:
        return '\n'.join(res)
    return res


def parse(stringcode, verbose=0):
    parsetree = mcgrammar.parse(stringcode)
    if verbose > 1:
        print('\n' + ' Parse Tree '.center(40, '#'))
        print(parsetree)
    ast = ASTFormatter().visit(parsetree)
    if verbose > 0:
        print('\n' + ' AST '.center(40, '#'))
        print(prettyast(ast))
    return ast


def parsefile(fname, verbose=0):
    with open(fname, 'r') as mcfile:
        print('\n' + ' Source code '.center(40, '#'))
        stringcode = mcfile.read()[:-1]
        print(stringcode)
        return parse(stringcode, verbose)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to parse")
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    parsefile(args.filename, verbose=args.verbose + 1)
