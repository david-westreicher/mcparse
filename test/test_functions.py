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
                stmt_correct3 = typet + ' func_ident( ){}'
                stmt_false1 = 'func_ident(' + params + '){}'
                stmt_false2 = 'func_ident(' + params + ')'
                stmt_false3 = 'func_ident ' + params
                self.checkstmt(stmt_correct1, 'fun_def', True)
                self.checkstmt(stmt_correct2, 'fun_def', True)
                self.checkstmt(stmt_correct3, 'fun_def', True)
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
        self.checkstmt('f()', 'call_expr', True)
        expr = '1'
        for i in range(5):
            self.checkstmt('fun(' + expr + ')', 'call_expr', True)
            self.checkstmt('(' + expr + ',)', 'call_expr', False)
            self.checkstmt('fun(' + expr + ',)', 'call_expr', False)
            self.checkstmt('fun(,' + expr + ')', 'call_expr', False)
            expr = expr + ',' + expr + '+' + expr

    def test_ret_stmt(self):
        self.checkstmt('return;', 'return_stmt', True)
        for expression, blanks in product(
                ['1', '1*4', '1+x*(10/2.0)'],
                [' ', '  ', ' \t']):
            self.checkstmt('return' + blanks + expression + blanks + ';', 'return_stmt', True)


class TestAST(unittest.TestCase):

    def checkComp(self, ast, *types):
        self.assertEqual(type(ast), parser.CompStmt)
        self.assertEqual([type(el) for el in ast.stmts], list(types))

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
                        return;
                    }""" % (rettype, name, par1type, par2type))
            self.assertEqual(type(ast), parser.FunDef)
            self.assertEqual(ast.name, name)
            self.assertEqual(ast.ret_type, rettype)
            self.assertEqual(ast.params, [
                parser.Param(par1type, 'x'),
                parser.Param(par2type, 'y')
            ])
            self.checkComp(ast.stmts, parser.BinOp, parser.BinOp, parser.RetStmt)
            retstmt = ast.stmts.stmts[2]
            self.assertEqual(retstmt.expression, None)

    def test_fun_def_noparams(self):
        for rettype, name in product(
                ['void', 'int', 'float'],
                ['_asd', 'function', 'f']):
            ast = parser.parse(
                """%s %s() {
                        x = 2;
                        y = 2;
                        return;
                    }""" % (rettype, name))
            self.assertEqual(type(ast), parser.FunDef)
            self.assertEqual(ast.name, name)
            self.assertEqual(ast.ret_type, rettype)
            self.assertEqual(ast.params, [])
            self.checkComp(ast.stmts, parser.BinOp, parser.BinOp, parser.RetStmt)
            retstmt = ast.stmts.stmts[2]
            self.assertEqual(retstmt.expression, None)

    def test_fun_def_multiple(self):
        ast = parser.parse("""{
                    void fun1(int x){
                        x = 0;
                        return x;
                    }
                    int fun2(int x, float y){
                        x = 0;
                        y = 0;
                        return x+y;
                    }
                    float fun3(int x, float y, int z){
                        x = 0;
                        y = 0;
                        z = 0;
                        return (x+y)*z;
                    }
                }""")
        self.checkComp(ast, parser.FunDef, parser.FunDef, parser.FunDef)
        fun1, fun2, fun3 = ast.stmts
        self.assertEqual(fun1.ret_type, 'void')
        self.assertEqual(fun1.name, 'fun1')
        self.assertEqual(fun1.params, [
            parser.Param('int', 'x'),
        ])
        self.checkComp(fun1.stmts, parser.BinOp, parser.RetStmt)

        self.assertEqual(fun2.ret_type, 'int')
        self.assertEqual(fun2.name, 'fun2')
        self.assertEqual(fun2.params, [
            parser.Param('int', 'x'),
            parser.Param('float', 'y'),
        ])
        self.checkComp(fun2.stmts, parser.BinOp, parser.BinOp, parser.RetStmt)

        self.assertEqual(fun3.ret_type, 'float')
        self.assertEqual(fun3.name, 'fun3')
        self.assertEqual(fun3.params, [
            parser.Param('int', 'x'),
            parser.Param('float', 'y'),
            parser.Param('int', 'z'),
        ])
        self.checkComp(fun3.stmts, parser.BinOp, parser.BinOp, parser.BinOp, parser.RetStmt)

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
        for name in ['_asd', 'function', 'f']:
            ast = parser.parse('%s();' % (name))
            self.assertEqual(type(ast), parser.FunCall)
            self.assertEqual(ast.name, name)
            self.assertEqual(ast.args, [])

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


class TestThreeExceptions(unittest.TestCase):

    def test_fun_def_double_param(self):
        with self.assertRaises(three.FunctionDefinitionException) as e:
            tac = codetothree("""{
                void sameparams(int x, int x){
                }
            }""")
        msg = str(e.exception)
        self.assertIn('sameparams', msg)
        self.assertIn('x', msg)
        self.assertIn('already', msg)
        self.assertIn('defined', msg)

    def test_fun_def_double(self):
        with self.assertRaises(three.FunctionDefinitionException) as e:
            tac = codetothree("""{
                void samename(){
                }
                void samename(){
                }
            }""")
        msg = str(e.exception)
        self.assertIn('samename', msg)
        self.assertIn('already', msg)
        self.assertIn('defined', msg)

    def test_fun_def_no_return(self):
        with self.assertRaises(three.ReturnException) as e:
            tac = codetothree("""int returnsvoid(int x){
            }""")
        msg = str(e.exception)
        self.assertIn('should', msg)
        self.assertIn('return', msg)
        self.assertIn('int', msg)

    def test_fun_def_void_return(self):
        with self.assertRaises(three.ReturnException) as e:
            tac = codetothree("""void returnsint(int x){
                return 100;
            }""")
        msg = str(e.exception)
        self.assertIn('should', msg)
        self.assertIn('return', msg)
        self.assertIn('void', msg)
        with self.assertRaises(three.ReturnException) as e:
            tac = codetothree("""int returnsvoid(int x){
                return;
            }""")
        msg = str(e.exception)
        self.assertIn('should', msg)
        self.assertIn('return', msg)
        self.assertIn('int', msg)

    def test_fun_call_void_return(self):
        with self.assertRaises(three.CallException) as e:
            tac = codetothree("""{
                void voidfunc(){
                    return;
                }
                int x = voidfunc();
            }""")
        msg = str(e.exception)
        self.assertIn('voidfunc', msg)
        self.assertIn('returns', msg)
        self.assertIn('void', msg)

    def test_fun_call_undefined(self):
        with self.assertRaises(three.CallException) as e:
            tac = codetothree("""{
                int x = undefinedfunc();
            }""")
        msg = str(e.exception)
        self.assertIn('undefinedfunc', msg)
        self.assertIn('not', msg)
        self.assertIn('defined', msg)

    def test_fun_call_wrong_params(self):
        with self.assertRaises(three.CallException) as e:
            tac = codetothree("""{
                int takesonearg(int x){
                    return x;
                }
                int x = takesonearg();
            }""")
        msg = str(e.exception)
        self.assertIn('takesonearg', msg)
        self.assertIn('accepts', msg)
        self.assertIn('1', msg)
        self.assertIn('gave', msg)
        self.assertIn('0', msg)
        with self.assertRaises(three.CallException) as e:
            tac = codetothree("""{
                int takesonearg(int x){
                    return x;
                }
                int x = takesonearg(1,2);
            }""")
        msg = str(e.exception)
        self.assertIn('takesonearg', msg)
        self.assertIn('accepts', msg)
        self.assertIn('1', msg)
        self.assertIn('gave', msg)
        self.assertIn('2', msg)


class TestThree(unittest.TestCase):

    def checkthree(self, three1, three2):
        for el1, el2 in zip(three1, three2):
            if el2 is None:
                continue
            self.assertEqual(el1, el2)

    def test_fun_def_empty(self):
        three = codetothree(
            """void fun1(){
        }""")
        self.assertEqual(len(three),3)
        self.checkthree(three[0], ['function', None, None, 'fun1'])
        self.checkthree(three[1], ['return'])
        self.checkthree(three[2], ['end-fun', None, None, None])

    def test_fun_def_return_void(self):
        three = codetothree(
            """void fun1(){
                return;
        }""")
        self.assertEqual(len(three),3)
        self.checkthree(three[0], ['function', None, None, 'fun1'])
        self.checkthree(three[1], ['return'])
        self.checkthree(three[2], ['end-fun', None, None, None])

    def generate_params(self, paramlen):
        params = '' if paramlen == 0 else 'int x0'
        for varnum in range(1, paramlen):
            params = params + (', int x%s' % (varnum))
        return params

    def generate_args(self, arglen):
        args = '' if arglen == 0 else '1'
        for _ in range(1, arglen):
            args = args + ', 1'
        return args

    def test_fun_def_params(self):
        for rettype, paramlen in product(['float', 'int', 'void'], range(5)):
            three = codetothree("""{
                %s fun1(%s){
                    return %s;
                }
            }""" % (rettype, self.generate_params(paramlen), '' if rettype == 'void' else '0'))
            self.checkthree(three[0], ['function', None, None, 'fun1'])
            for codenum in range(paramlen):
                self.checkthree(three[codenum + 1], ['pop', None, None, 'x%s' % codenum])
            if rettype != 'void':
                self.checkthree(three[-3], ['push'])
            self.checkthree(three[-2], ['return'])
            self.checkthree(three[-1], ['end-fun', None, None, None])

    def test_fun_def_params_multiple(self):
        for rettype1, paramlen1, rettype2, paramlen2 in product(
                ['float', 'int', 'void'], range(5),
                ['float', 'int', 'void'], range(5)):
            three = codetothree("""{
                %s fun1(%s){
                    return %s;
                }
                %s fun2(%s){
                    return %s;
                }
            }""" % (rettype1, self.generate_params(paramlen1), '' if rettype1 == 'void' else '0',
                    rettype2, self.generate_params(paramlen2), '' if rettype2 == 'void' else '0',
                    ))

            lastlinefun1 = three.index(['end-fun', None, None, None])
            for start, end, rettype, parlen, fname in [
                    (0, lastlinefun1, rettype1, paramlen1, 'fun1'),
                    (lastlinefun1 + 1, -1, rettype2, paramlen2, 'fun2')]:
                self.checkthree(three[start], ['function', None, None, fname])
                for codenum in range(parlen):
                    self.checkthree(three[start + codenum + 1], ['pop', None, None, 'x%s' % codenum])
                if rettype != 'void':
                    self.checkthree(three[end - 2], ['push'])
                self.checkthree(three[end - 1], ['return'])
                self.checkthree(three[end], ['end-fun', None, None, None])

    def test_fun_call_simple(self):
        for rettype, paramlen in product(['float', 'int'], range(5)):
            three = codetothree("""{
                %s fun(%s){
                    return 0;
                }
                %s x = fun(%s);
            }""" % (rettype, self.generate_params(paramlen), rettype, self.generate_args(paramlen)))
            afterfun = three.index(['end-fun', None, None, None]) + 1
            for offset in range(paramlen):
                self.checkthree(three[afterfun + offset * 2 + 1], ['push'])
            afterpushes = afterfun + paramlen * 2
            self.checkthree(three[afterpushes + 0], ['call', None, None, 'fun'])
            self.checkthree(three[afterpushes + 1], ['pop'])
            self.checkthree(three[afterpushes + 2], ['assign', None, None, 'x'])

    def test_fun_call_void(self):
        for paramlen in range(5):
            three = codetothree("""{
                void fun(%s){
                }
                fun(%s);
            }""" % (self.generate_params(paramlen), self.generate_args(paramlen)))
            self.checkthree(three[-1], ['call', None, None, 'fun'])
            # no pop, because we don't need the result

if __name__ == '__main__':
    unittest.main()
