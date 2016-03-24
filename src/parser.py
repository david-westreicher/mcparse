from collections import namedtuple
from parsimonious import Grammar, NodeVisitor

# TODO expression precedence is not expressed: - (unary) > * > +
# i.e.: -5.0*10.0 => (- (* 5 10))

mcgrammar = Grammar(
    """
    statement        = if_stmt / decl_stmt / compound_stmt / expr_stmt
    if_stmt          = "if" _ paren_expr _ statement (_ "else" _ statement)?
    decl_stmt        = type _ identifier (_ "=" _ expression)? ";"
    compound_stmt    = "{" _ (statement _)* "}"
    expr_stmt        = expression ";"
    type             = "int" / "float"
    expression       = binary_operation / single_expr
    binary_operation = single_expr _ bin_op _ expression
    single_expr      = paren_expr / unary_expr / literal / identifier
    bin_op           = "+" / "-" / "*" / "/" / "==" / "!=" / "<=" / ">=" / "<" / ">" / "="
    paren_expr       = "(" expression ")"
    unary_expr       = unop _ expression
    unop             = "-" / "!"
    literal          = float_lit / int_lit
    int_lit          = ~"\d+"
    float_lit        = ~"\d+\.\d*"
    identifier       = ~"[a-zA-Z_][a-zA-Z_0-9]*"
    _                = ~"\s*"
    """)

IfStmt = namedtuple('IfStmt', ['expression', 'if_stmt', 'else_stmt'])
DeclStmt = namedtuple('DeclStmt', ['type', 'variable', 'expression'])
CompStmt = namedtuple('CompStmt', ['stmts'])
BinOp = namedtuple('BinOp', ['operation', 'lhs', 'rhs'])
UnaOp = namedtuple('UnaOp', ['operation', 'expression'])
Literal = namedtuple('Literal', ['type', 'val'])
Variable = namedtuple('Variable', ['name'])


class ASTFormatter(NodeVisitor):
    grammar = mcgrammar
    def visit_statement(self, node, childs):
        return childs[0]
    def visit_if_stmt(self, node, childs):
        expression, if_stmt, else_stmt = (childs[i] for i in [2, 4, 5])
        return IfStmt(expression, if_stmt, else_stmt)
    def visit_decl_stmt(self, node, childs):
        vartype, variable, expression = (childs[i] for i in [0, 2, 3])
        return DeclStmt(vartype, variable.name, expression)
    def visit_compound_stmt(self, node, childs):
        stmts = childs[2]
        if not isinstance(stmts, list):
            stmts = [stmts]
        return CompStmt(stmts)
    def visit_expr_stmt(self, node, childs):
        return childs[0]
    def visit_type(self, node, childs):
        return node.text
    def visit_expression(self, node, childs):
        return childs[0]
    def visit_binary_operation(self, node, childs):
        operation, lhs, rhs = (childs[i] for i in [2, 0, 4])
        return BinOp(operation, lhs, rhs)
    def visit_single_expr(self, node, childs):
        return childs[0]
    def visit_bin_op(self, node, childs):
        return node.text
    def visit_paren_expr(self, node, childs):
        return childs[1]
    def visit_unary_expr(self, node, childs):
        return UnaOp(*(childs[i] for i in [0, 2]))
    def visit_unop(self, node, childs):
        return node.text
    def visit_literal(self, node, childs):
        return childs[0]
    def visit_int_lit(self, node, childs):
        return Literal(node.expr_name, int(node.text))
    def visit_float_lit(self, node, childs):
        return Literal(node.expr_name, float(node.text))
    def visit_identifier(self, node, childs):
        return Variable(node.text)
    def visit__(self, node, childs):
        return None
    def generic_visit(self, node, childs):
        if node.expr_name == '' and len(childs) == 0:
            return None
        res = [x for x in childs if x is not None]
        if len(res) == 0:
            raise Exception
        if len(res) == 1:
            return res[0]
        if len(res) > 1:
            return res


def prettyast(ast, level=0, res=None):
    if res is None:
        res = ''
    if isinstance(ast, list):
        for el in ast:
            res = prettyast(el, level, res)
    elif isinstance(ast, tuple):
        res += '\t'*level+type(ast).__name__+'\n'
        for el in ast:
            res = prettyast(el, level+1, res)
    else:
        res += '\t'*level+str(ast)+'\n'
    return res


def parse(stringcode):
    print(stringcode)
    parsetree = mcgrammar.parse(stringcode)
    # print(parsetree)
    ast = ASTFormatter().visit(parsetree)
    print(prettyast(ast))
    return ast


def parsefile(fname):
    with open(fname, 'r') as mcfile:
        return parse(mcfile.read()[:-1])

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to parse")
    args = parser.parse_args()
    print(prettyast(parsefile(args.filename)))
