import unittest
from itertools import product
from src import three
from src import parser


def codetothree(stringcode):
    return three.asttothree(parser.parse(stringcode))

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
        except Exception as e:
            if result:
                passed = False
                print('"%s" is not a %s' % (stmt, rule))
                print(e)
        self.assertTrue(passed)

    def test_array_def(self):
        for typet in ['int', 'float']:
            for num in ['7', '0', '8']:
                for varname in ['a', '_b', 'abcdef']:
                    self.checkstmt(typet + '[' + num + '] ' + varname + ';', 'array_def', True)
        self.checkstmt('int[] asd;', 'array_def', False)
        self.checkstmt('int[-1] asd;', 'array_def', False)
        self.checkstmt('int[4*3] asd;', 'array_def', False)

    def test_array_expression(self):
        for varname in ['a', '_b', 'abcdef']:
            for expression in ['(f(1))*2', '0', '3*8+a']:
                self.checkstmt(varname + '[' + expression + ']', 'array_exp', True)
                self.checkstmt(varname + '[' + expression + ']', 'expression', True)
        for expression in ['(f(1))*2', '0', '3*8+a']:
            self.checkstmt('int ' + varname + '[' + expression + ']', 'array_exp', False)


class TestAST(unittest.TestCase):

    def checkComp(self, ast, *types):
        self.assertEqual(type(ast), parser.CompStmt)
        self.assertEqual([type(el) for el in ast.stmts], list(types))

    def test_array_def(self):
        for typet, size, name in product(
                ['int', 'float'],
                [8, 100, 0],
                ['bla', 'arrayname']):
            ast = parser.parse(
                """%s[%s] %s;""" % (typet, size, name))
            self.assertEqual(type(ast), parser.ArrayDef)
            self.assertEqual(ast.name, name)
            self.assertEqual(ast.type, typet)
            self.assertEqual(ast.size, size)

    def test_array_exp(self):
        for name, expression in product(
                ['bla', 'arrayname'],
                ['2*9', '0+f(10)', '3*8+a']):
            ast = parser.parse(
                """%s[%s];""" % (name, expression))
            self.assertEqual(type(ast), parser.ArrayExp)
            self.assertEqual(ast.name, name)
            self.assertEqual(type(ast.expression), parser.BinOp)

        for name, expression in product(
                ['bla', 'arrayname'],
                ['2*9', '0+f(10)', '3*8+a']):
            ast = parser.parse(
                """(%s[%s])*10+5;""" % (name, expression))
            self.assertEqual(type(ast), parser.BinOp)
            self.assertEqual(type(ast.rhs), parser.BinOp)
            self.assertEqual(type(ast.lhs), parser.ArrayExp)
            self.assertEqual(ast.lhs.name, name)
            self.assertEqual(type(ast.lhs.expression), parser.BinOp)

    def test_array_exp_nested(self):
        ast = parser.parse("""a[b[c[d[10]]]];""")
        self.assertEqual(type(ast), parser.ArrayExp)
        self.assertEqual(ast.name, 'a')
        self.assertEqual(type(ast.expression), parser.ArrayExp)
        self.assertEqual(ast.expression.name, 'b')
        self.assertEqual(type(ast.expression.expression), parser.ArrayExp)
        self.assertEqual(ast.expression.expression.name, 'c')
        self.assertEqual(type(ast.expression.expression.expression), parser.ArrayExp)
        self.assertEqual(ast.expression.expression.expression.name, 'd')
        self.assertEqual(ast.expression.expression.expression.expression, parser.Literal('int', 10))


class TestThree(unittest.TestCase):

    def checkthree(self, three1, three2):
        for el1, el2 in zip(three1, three2):
            if el2 is None:
                continue
            self.assertEqual(el1, el2)

    def test_array_def(self):
        for typet, name, num in product(
                ['int', 'float'],
                ['bla', 'arrayname'],
                [0, 1, 2, 8, 100, 99]):
            three = codetothree(
                """%s[%s] %s;""" % (typet, num, name))
            self.assertEqual(len(three), 1)
            self.checkthree(three[0], ['arr-def', num, name, None])

    def test_array_assignment(self):
        three = codetothree(
            """{
                int[10] foo;
                foo[5] = 5;
            }""")
        self.assertEqual(len(three), 4)
        self.checkthree(three[0], ['arr-def', 10, 'foo'])
        self.checkthree(three[1], ['assign', 5, None, '.t0'])
        self.checkthree(three[2], ['assign', 5, None, '.t1'])
        self.checkthree(three[3], ['arr-ass', '.t1', '.t0', 'foo'])

if __name__ == '__main__':
    unittest.main()
