import unittest
from parsimonious import ParseError
from itertools import product
from src import three
from src import parser
from src import bb
from src import cfg
from src import dataflow


def codetothree(stringcode):
    return three.asttothree(parser.parse(stringcode))


def codetobbs(stringcode):
    return bb.threetobbs(three.asttothree(parser.parse(stringcode)))


def codetocfg(stringcode):
    return cfg.bbstocfg(bb.threetobbs(three.asttothree(parser.parse(stringcode))))

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

    def test_type_or_void(self):
        for typet in ['int', 'float', 'void']:
            self.checkstmt(typet, 'type_or_void', True)
        self.checkstmt('String', 'type_or_void', False)
        self.checkstmt('Integer', 'type_or_void', False)
        self.checkstmt('bool', 'type_or_void', False)

    def test_param(self):
        for typet in ['int', 'float']:
            for blanks in [' ', '  ', '   ', '\t', '\t\t']:
                self.checkstmt(typet + blanks + 'identifier', 'param', True)
        self.checkstmt('void identifier', 'param', False)

    def test_params(self):
        for typet in ['int', 'float']:
            self.checkstmt(typet + ' identifier', 'params', True)
        self.checkstmt('void identifier', 'params', False)
        for typet1 in ['int', 'float']:
            for typet2 in ['int', 'float']:
                for blanks in [' ', '  ', '   ', '\t', '\t\t']:
                    self.checkstmt(typet1 + blanks + 'ident1' + blanks + ','
                                   + blanks + typet2 + blanks + 'ident2', 'params', True)
        stmt = 'int asd'
        for i in range(5):
            stmt += ', ' + ['int', 'float'][i % 2] + ' ident'
            self.checkstmt(stmt, 'params', True)
            self.checkstmt(stmt + ',', 'params', False)

    def test_fun_def(self):
        for typet in ['int', 'float', 'void']:
            params = 'int asd'
            for i in range(5):
                stmt_correct1 = typet + ' func_ident(' + params + ') {}'
                stmt_correct2 = typet + ' func_ident(' + params + '){}'
                stmt_false1 = 'func_ident(' + params + '){}'
                stmt_false2 = 'func_ident(' + params + ')'
                stmt_false3 = 'func_ident ' + params
                self.checkstmt(stmt_correct1, 'fun_def', True)
                self.checkstmt(stmt_correct2, 'fun_def', True)
                self.checkstmt(stmt_false1, 'fun_def', False)
                self.checkstmt(stmt_false2, 'fun_def', False)
                self.checkstmt(stmt_false3, 'fun_def', False)
                params += ', ' + ['int', 'float'][i % 2] + ' ident'

    def test_arguments(self):
        self.checkstmt('int asd', 'arguments', False)
        expr = '1'
        for i in range(5):
            self.checkstmt(expr, 'arguments', True)
            self.checkstmt(expr + ',', 'arguments', False)
            self.checkstmt(',' + expr, 'arguments', False)
            expr = expr + ',' + expr + '+' + expr

    def test_call_expr(self):
        self.checkstmt('f()', 'call_expr', False)
        expr = '1'
        for i in range(5):
            self.checkstmt('fun(' + expr + ')', 'call_expr', True)
            self.checkstmt('(' + expr + ',)', 'call_expr', False)
            self.checkstmt('fun(' + expr + ',)', 'call_expr', False)
            self.checkstmt('fun(,' + expr + ')', 'call_expr', False)
            expr = expr + ',' + expr + '+' + expr


class TestAST(unittest.TestCase):

    def checkComp(self, ast, *types):
        self.assertEqual(type(ast), parser.CompStmt)
        self.assertEqual(len(ast.stmts), len(types))
        for stmt, t in zip(ast.stmts, types):
            self.assertEqual(type(stmt), t)

    def test_fun_def(self):
        for rettype, name, par1type, par2type in product(
                ['void', 'int', 'float'],
                ['_asd', 'function', 'f'],
                ['int', 'float'],
                ['int', 'float']):
            ast = parser.parse(
                """%s %s(%s x, %s y) {
                        x = 2;
                        y = 2;
                    }""" % (rettype, name, par1type, par2type))
            self.assertEqual(type(ast), parser.FunDef)
            self.assertEqual(ast.name, name)
            self.assertEqual(ast.ret_type, rettype)
            self.assertEqual(ast.params, [
                parser.Param(par1type, 'x'),
                parser.Param(par2type, 'y')
            ])
            self.checkComp(ast.stmts, parser.BinOp, parser.BinOp)

    def test_fun_def_noparams(self):
        with self.assertRaises(ParseError):
            parser.parse("""void noparams(){}""")

    def test_fun_def_multiple(self):
        ast = parser.parse("""{
                    void fun1(int x){
                        x = 0;
                    }
                    int fun2(int x, float y){
                        x = 0;
                        y = 0;
                    }
                    float fun3(int x, float y, int z){
                        x = 0;
                        y = 0;
                        z = 0;
                    }
                }""")
        self.checkComp(ast, parser.FunDef, parser.FunDef, parser.FunDef)
        fun1, fun2, fun3 = ast.stmts
        self.assertEqual(fun1.ret_type, 'void')
        self.assertEqual(fun1.name, 'fun1')
        self.assertEqual(fun1.params, [
            parser.Param('int', 'x'),
        ])
        self.checkComp(fun1.stmts, parser.BinOp)

        self.assertEqual(fun2.ret_type, 'int')
        self.assertEqual(fun2.name, 'fun2')
        self.assertEqual(fun2.params, [
            parser.Param('int', 'x'),
            parser.Param('float', 'y'),
        ])
        self.checkComp(fun2.stmts, parser.BinOp, parser.BinOp)

        self.assertEqual(fun3.ret_type, 'float')
        self.assertEqual(fun3.name, 'fun3')
        self.assertEqual(fun3.params, [
            parser.Param('int', 'x'),
            parser.Param('float', 'y'),
            parser.Param('int', 'z'),
        ])
        self.checkComp(fun3.stmts, parser.BinOp, parser.BinOp, parser.BinOp)

    def test_fun_call(self):
        args = '5'
        for arglen in range(1, 10):
            for name in ['_asd', 'function', 'f']:
                ast = parser.parse('%s(%s);' % (name, args))
                self.assertEqual(type(ast), parser.FunCall)
                self.assertEqual(ast.name, name)
                self.assertEqual(len(ast.args), arglen)
                for arg in ast.args:
                    self.assertTrue(type(arg) in [parser.BinOp, parser.Literal])
            args += ',' + str(arglen)

    def test_fun_call_noparams(self):
        with self.assertRaises(ParseError):
            parser.parse("""noparams();""")

    def test_fun_call_multiple(self):
        ast = parser.parse("""{
                    fun1(1);
                    fun2(1, 2);
                    fun3(1, 2, 3);
                }""")
        self.checkComp(ast, parser.FunCall, parser.FunCall, parser.FunCall)
        fun1, fun2, fun3 = ast.stmts
        self.assertEqual(fun1.name, 'fun1')
        self.assertEqual(len(fun1.args), 1)
        self.assertEqual(fun2.name, 'fun2')
        self.assertEqual(len(fun2.args), 2)
        self.assertEqual(fun3.name, 'fun3')
        self.assertEqual(len(fun3.args), 3)

if __name__ == '__main__':
    unittest.main()
