import unittest
from src import parser


grammar = parser.mcgrammar


class TestGrammar(unittest.TestCase):

    def checkstmt(self, stmt, rule, result):
        passed = True
        try:
            if rule is None:
                grammar.parse(stmt)
            else:
                grammar[rule].parse(stmt)
            if not result:
                passed = False
                print('"%s" is a %s' % (stmt, rule))
        except Exception, e:
            if result:
                passed = False
                print('"%s" is not a %s' % (stmt, rule))
                print(e)
        self.assertTrue(passed)

    def test_types(self):
        self.checkstmt('+', 'type', False)
        self.checkstmt('test', 'type', False)
        self.checkstmt('int', 'type', True)
        self.checkstmt('float', 'type', True)

    def test_literals(self):
        self.checkstmt('+', 'int_lit', False)
        self.checkstmt('test', 'int_lit', False)
        self.checkstmt('1', 'int_lit', True)
        self.checkstmt('4.5', 'float_lit', True)

    def test_variables(self):
        self.checkstmt('1', 'identifier', False)
        self.checkstmt('4.5', 'identifier', False)
        self.checkstmt('_asd', 'identifier', True)
        self.checkstmt('x', 'identifier', True)
        self.checkstmt('asd0123_123', 'identifier', True)

    def test_binary_operands(self):
        self.checkstmt('1', 'bin_op', False)
        self.checkstmt('+', 'bin_op', True)
        self.checkstmt('*', 'bin_op', True)
        self.checkstmt('=', 'bin_op', True)
        self.checkstmt('==', 'bin_op', True)
        self.checkstmt('<', 'bin_op', True)
        self.checkstmt('<=', 'bin_op', True)

    def test_expressions(self):
        self.checkstmt('test', 'literal', False)
        self.checkstmt('1', 'literal', True)
        self.checkstmt('4.5', 'literal', True)

        self.checkstmt('test', 'binary_operation', False)
        self.checkstmt('4.5', 'binary_operation', False)
        self.checkstmt('+', 'binary_operation', False)
        self.checkstmt('1+7', 'binary_operation', True)
        self.checkstmt('1 +  7.1', 'binary_operation', True)
        self.checkstmt('1+', 'binary_operation', False)

        self.checkstmt('1', 'unary_expr', False)
        self.checkstmt('-4.2', 'unary_expr', True)

        self.checkstmt('-4.2', 'paren_expr', False)
        self.checkstmt('( 1+7 )', 'paren_expr', True)

    def test_statements(self):
        self.checkstmt('test', 'expr_stmt', False)
        self.checkstmt('1;', 'expr_stmt', True)
        self.checkstmt('2.0*x ;', 'expr_stmt', True)

        self.checkstmt('test', 'compound_stmt', False)
        self.checkstmt('{}', 'compound_stmt', True)
        self.checkstmt('{ 1; { {} 7; }}', 'compound_stmt', True)

        self.checkstmt('test', 'if_stmt', False)
        self.checkstmt('if(1) {}', 'if_stmt', True)
        self.checkstmt('if (1) {} else 5;', 'if_stmt', True)
        self.checkstmt('int test;', 'decl_stmt', True)
        self.checkstmt('int test = 2 ;', 'decl_stmt', True)

    def test_complex_statements(self):
        self.checkstmt(
        """{
            int x;
            if(1 == 2) {
                5+4*8.0;
                7;
                x = 8;
            } else {
                if(2 < 9) {
                }
            }
            2.9;
        }""", 'statement', True)
        self.checkstmt(
        """{
            int x=1;
            float y = 3.0;
            if(x > 0) {
                y = y * 1.5;
            } else {
                y = y + 2.0;
            }
        }""", 'statement', True)

class TestAST(unittest.TestCase):

    def checkComp(self, ast, *types):
        self.assertEqual(type(ast),parser.CompStmt)
        for stmt, t in zip(ast.stmts, types):
            self.assertEqual(type(stmt),t)

    def checkLiteral(self, ast, typ, val):
        self.assertEqual(type(ast),parser.Literal)
        self.assertEqual(ast.type,typ)
        self.assertEqual(ast.val,val)

    def test_ifelse(self):
        ast = parser.parse(
            """if(1) {
                int x = 2;
            } else {
                int x = 3;
            }""")
        self.assertEqual(type(ast),parser.IfStmt)
        self.assertEqual(type(ast.expression),parser.Literal)
        self.assertEqual(ast.expression.type,'int')
        self.assertEqual(ast.expression.val,1)
        self.checkComp(ast.if_stmt, parser.DeclStmt)
        self.checkComp(ast.else_stmt, parser.DeclStmt)

    def test_if(self):
        ast = parser.parse(
            """if(1) {
                int x = 2;
            }""")
        self.assertEqual(type(ast),parser.IfStmt)
        self.assertEqual(type(ast.expression),parser.Literal)
        self.assertEqual(ast.expression.type,'int')
        self.assertEqual(ast.expression.val,1)
        self.checkComp(ast.if_stmt, parser.DeclStmt)
        self.assertEqual(ast.else_stmt,None)

    def test_decl(self):
        ast = parser.parse('int x;')
        self.assertEqual(type(ast),parser.DeclStmt)
        self.assertEqual(ast.type,'int')
        self.assertEqual(ast.variable,'x')
        self.assertEqual(ast.expression,None)

        ast = parser.parse('float y = 1.0;')
        self.assertEqual(type(ast),parser.DeclStmt)
        self.assertEqual(ast.type,'float')
        self.assertEqual(ast.variable,'y')
        self.assertEqual(type(ast.expression),parser.Literal)
        self.assertEqual(ast.expression.type,'float')
        self.assertEqual(ast.expression.val,1.0)

    def test_compound(self):
        ast = parser.parse("""{
            int x;
            if(1 == 2) {
                5+4*8.0;
                7;
                x = 8;
            } else {
                if(2 < 9) {
                }
            }
            2.9;
        }""")
        self.checkComp(ast, parser.DeclStmt, parser.IfStmt, parser.Literal)

    def test_expression(self):
        ast = parser.parse('(4*3)+(2-1);')
        self.assertEqual(type(ast),parser.BinOp)
        self.assertEqual(ast.operation,'+')
        self.assertEqual(type(ast.lhs),parser.BinOp)
        self.assertEqual(ast.lhs.operation,'*')
        self.checkLiteral(ast.lhs.lhs,'int',4)
        self.checkLiteral(ast.lhs.rhs,'int',3)
        self.assertEqual(type(ast.rhs),parser.BinOp)
        self.assertEqual(ast.rhs.operation,'-')
        self.checkLiteral(ast.rhs.lhs,'int',2)
        self.checkLiteral(ast.rhs.rhs,'int',1)

    def test_dangling_else(self):
        ast = parser.parse(
        """if(1)
            if(2){
            }else
                1.0;""")
        self.assertEqual(type(ast),parser.IfStmt)
        # else belongs to inner if
        self.assertEqual(ast.else_stmt,None)
        self.assertEqual(type(ast.if_stmt),parser.IfStmt)
        self.assertNotEqual(ast.if_stmt.else_stmt,None)
        self.assertEqual(type(ast.if_stmt.else_stmt),parser.Literal)


if __name__ == '__main__':
    unittest.main()
