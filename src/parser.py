from collections import namedtuple
from parsimonious import Grammar, NodeVisitor

# TODO expression precedence is not expressed: - (unary) > * > +
# i.e.: -5.0*10.0 => (- (* 5 10))

mcgrammar = Grammar(
    """
    statement        = if_stmt / while_stmt / for_stmt / decl_stmt / compound_stmt / expr_stmt
    if_stmt          = "if" _ paren_expr _ statement (_ "else" _ statement)?
    while_stmt       = "while" _ paren_expr _ statement
    for_stmt         = "for" _ "(" _ expression _ ";" _ expression _ ";" _ expression _ ")" _ statement
    decl_stmt        = type _ identifier (_ "=" _ expression)? _ ";"
    compound_stmt    = "{" _ (statement _)* "}"
    expr_stmt        = expression _ ";"
    type             = "int" / "float"
    expression       = binary_operation / single_expr
    binary_operation = single_expr _ bin_op _ expression
    single_expr      = paren_expr / unary_expr / literal / identifier
    bin_op           = "+" / "-" / "*" / "/" / "%" / "==" / "!=" / "<=" / ">=" / "<" / ">" / "="
    paren_expr       = "(" _ expression _ ")"
    unary_expr       = unop _ expression
    unop             = "-" / "!"
    literal          = float_lit / int_lit
    int_lit          = ~"\d+"
    float_lit        = ~"\d+\.\d*"
    identifier       = ~"[a-zA-Z_][a-zA-Z_0-9]*"
    _                = ~"\s*"
    """)

IfStmt = namedtuple('IfStmt', ['expression', 'if_stmt', 'else_stmt'])
WhileStmt = namedtuple('WhileStmt', ['expression', 'stmt'])
ForStmt = namedtuple('ForStmt', ['initexpr', 'conditionexpr', 'afterexpr', 'stmt'])
DeclStmt = namedtuple('DeclStmt', ['type', 'variable', 'expression'])
CompStmt = namedtuple('CompStmt', ['stmts'])
BinOp = namedtuple('BinOp', ['operation', 'lhs', 'rhs'])
UnaOp = namedtuple('UnaOp', ['operation', 'expression'])
Literal = namedtuple('Literal', ['type', 'val'])
Variable = namedtuple('Variable', ['name'])


class ASTFormatter(NodeVisitor):
    grammar = mcgrammar

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
        vartype, variable, expression = (childs[i] for i in [0, 2, 3])
        return DeclStmt(vartype, variable.name, expression)

    def visit_compound_stmt(self, node, childs):
        stmts = childs[2]
        if stmts is None:
            return None
        if not isinstance(stmts, list):
            stmts = [stmts]
        return CompStmt(stmts)

    def visit_type(self, node, childs):
        return node.text

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

    def visit_identifier(self, node, childs):
        return Variable(node.text)

    def visit__(self, node, childs):
        return None

    def generic_visit(self, node, childs):
        if node.expr_name == '' and len(childs) == 0:
            return None
        res = [x for x in childs if x is not None]
        if len(res) == 0:
            return None
        if len(res) == 1:
            return res[0]
        if len(res) > 1:
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
