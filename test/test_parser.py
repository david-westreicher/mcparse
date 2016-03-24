import unittest
from src import parser


grammar = parser.mcgrammar


class TestParser(unittest.TestCase):

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
        # TODO test variable scope,  ...
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
        # TODO test AST val
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
        self.checkstmt('(1+7)', 'paren_expr', True)

    def test_statements(self):
        self.checkstmt('test', 'expr_stmt', False)
        self.checkstmt('1;', 'expr_stmt', True)

        self.checkstmt('test', 'compound_stmt', False)
        self.checkstmt('{}', 'compound_stmt', True)
        self.checkstmt('{ 1; { {} 7; }}', 'compound_stmt', True)

        self.checkstmt('test', 'if_stmt', False)
        self.checkstmt('if(1) {}', 'if_stmt', True)
        self.checkstmt('if (1) {} else 5;', 'if_stmt', True)
        self.checkstmt('int test;', 'decl_stmt', True)

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

if __name__ == '__main__':
    unittest.main()
