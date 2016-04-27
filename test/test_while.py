import unittest
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

    def test_while_statement(self):
        self.checkstmt('while(){}', 'while_stmt', False)
        self.checkstmt('while()', 'while_stmt', False)
        self.checkstmt('while(1)', 'while_stmt', False)
        self.checkstmt('while(1) {}', 'while_stmt', True)
        self.checkstmt('while(x<5){}', 'while_stmt', True)
        self.checkstmt('while((x*10+y*100)/z > 10.0) {}', 'while_stmt', True)
        self.checkstmt('while(x<5){int y = 5;}', 'while_stmt', True)
        self.checkstmt('while(x<5){int y = 5; int z = 4;}', 'while_stmt', True)
        self.checkstmt('while(x<5) int y = 5;', 'while_stmt', True)


class TestAST(unittest.TestCase):

    def checkComp(self, ast, *types):
        self.assertEqual(type(ast), parser.CompStmt)
        for stmt, t in zip(ast.stmts, types):
            self.assertEqual(type(stmt), t)

    def test_while(self):
        ast = parser.parse(
            """while(1) {
                int x = 2;
            }""")
        self.assertEqual(type(ast), parser.WhileStmt)
        self.assertEqual(type(ast.expression), parser.Literal)
        self.assertEqual(ast.expression.type, 'int')
        self.assertEqual(ast.expression.val, 1)
        self.checkComp(ast.stmt, parser.DeclStmt)

    def test_while_neighs(self):
        ast = parser.parse(
            """{
                while(1){
                    int x = 1;
                }
                while(2){
                    int x = 2;
                }
                while(3){
                    int x = 3;
                }
            }""")
        self.checkComp(ast, parser.WhileStmt, parser.WhileStmt)
        for i, stmt in enumerate(ast.stmts):
            self.assertEqual(type(stmt), parser.WhileStmt)
            self.assertEqual(type(stmt.expression), parser.Literal)
            self.assertEqual(stmt.expression.type, 'int')
            self.assertEqual(stmt.expression.val, i + 1)
            self.checkComp(stmt.stmt, parser.DeclStmt)

    def test_while_nested(self):
        ast = parser.parse(
            """while(1){
                    while(2){
                        while(3){
                            int x = 2;
                        }
                    }
                }""")
        self.assertEqual(type(ast), parser.WhileStmt)
        self.checkComp(ast.stmt, parser.WhileStmt)
        for stmt in ast.stmt.stmts:
            self.checkComp(stmt.stmt, parser.WhileStmt)

    def test_compound(self):
        ast = parser.parse("""{
            int x;
            while(1 == 2) {
                5+4*8.0;
            }
            2.9;
        }""")
        self.checkComp(ast, parser.DeclStmt, parser.WhileStmt, parser.Literal)


class TestThreeAndBasicBlocks(unittest.TestCase):

    def checkthree(self, three1, three2):
        for el1, el2 in zip(three1, three2):
            if el2 is None:
                continue
            self.assertEqual(el1, el2)

    def checkblock(self, bb1, bb2):
        for el1, el2 in zip(bb1, bb2):
            self.checkthree(el1, el2)

    def test_while(self):
        bbs = codetobbs(
            """while(1) {
                int x = 2;
            }""")
        self.assertEqual(len(bbs), 3)
        # while(1)
        self.checkblock(bbs[0], [
            ['label', None, None, 'L0'],
            ['assign', None, None, None],
            ['jumpfalse', None, None, 'L1'],
        ])
        # int x = 2;
        self.checkblock(bbs[1], [
            ['assign', None, None, None],
            ['assign', None, None, None],
            ['jump', None, None, 'L0']
        ])
        # whileend
        self.checkblock(bbs[2], [
            ['label', None, None, 'L1']
        ])

    def test_while_neighs(self):
        bbs = codetobbs(
            """{
                while(1){
                    int x = 1;
                }
                while(2){
                    int x = 2;
                }
                while(3){
                    int x = 3;
                }
            }""")
        self.assertEqual(len(bbs), 9)
        # while(1)
        self.checkblock(bbs[0], [
            ['label', None, None, 'L0'],
            ['assign', None, None, None],
            ['jumpfalse', None, None, 'L1']
        ])
        # int x = 1;
        self.checkblock(bbs[1], [
            ['assign', None, None, None],
            ['assign', None, None, None],
            ['jump', None, None, 'L0']
        ])
        # whileend
        self.checkblock(bbs[2], [
            ['label', None, None, 'L1']
        ])
        # while(2)
        self.checkblock(bbs[3], [
            ['label', None, None, 'L2'],
            ['assign', None, None, None],
            ['jumpfalse', None, None, 'L3']
        ])
        # int x = 2;
        self.checkblock(bbs[4], [
            ['assign', None, None, None],
            ['assign', None, None, None],
            ['jump', None, None, 'L2']
        ])
        # whileend
        self.checkblock(bbs[5], [
            ['label', None, None, 'L3']
        ])
        # while(3)
        self.checkblock(bbs[6], [
            ['label', None, None, 'L4'],
            ['assign', None, None, None],
            ['jumpfalse', None, None, 'L5']
        ])
        # int x = 3;
        self.checkblock(bbs[7], [
            ['assign', None, None, None],
            ['assign', None, None, None],
            ['jump', None, None, 'L4']
        ])
        # whileend
        self.checkblock(bbs[8], [
            ['label', None, None, 'L5']
        ])

    def test_while_nested(self):
        bbs = codetobbs(
            """while(1){
                    while(2){
                        while(3){
                            int x = 2;
                        }
                    }
                }""")
        self.assertEqual(len(bbs), 7)
        # while(1)
        self.checkblock(bbs[0], [
            ['label', None, None, 'L0'],
            ['assign', None, None, None],
            ['jumpfalse', None, None, 'L1']
        ])
        # while(2)
        self.checkblock(bbs[1], [
            ['label', None, None, 'L2'],
            ['assign', None, None, None],
            ['jumpfalse', None, None, 'L3']
        ])
        # while(3)
        self.checkblock(bbs[2], [
            ['label', None, None, 'L4'],
            ['assign', None, None, None],
            ['jumpfalse', None, None, 'L5']
        ])
        # int x = 2;
        self.checkblock(bbs[3], [
            ['assign', None, None, None],
            ['assign', None, None, None],
            ['jump', None, None, 'L4']
        ])
        # whileend 3
        self.checkblock(bbs[4], [
            ['label', None, None, 'L5'],
            ['jump', None, None, 'L2']
        ])
        # whileend 2
        self.checkblock(bbs[5], [
            ['label', None, None, 'L3'],
            ['jump', None, None, 'L0']
        ])
        # whileend 1
        self.checkblock(bbs[6], [
            ['label', None, None, 'L1']
        ])


class TestCFG(unittest.TestCase):

    def test_nowhilecfg(self):
        code = '''{
            int x = 0;
            int y = 0;
            int z = 0;
            if(1){
                x = 1;
            }else{
                x = 2;
            }
            x = 3;
        }'''
        cfg = codetocfg(code)
        self.assertEqual(cfg, {0: set([1, 2]), 1: set([3]), 2: set([3]), 3: set()})

    def test_simplewhile(self):
        code = '''while(1){
                int x = 1;
            }'''
        cfg = codetocfg(code)
        self.assertEqual(cfg, {0: set([1, 2]), 1: set([0]), 2: set()})

    def test_while_with_distractors(self):
        code = '''{
                int x = 0;
                while(x<5){
                    x = x+1;
                }
                int y = x;
            }'''
        cfg = codetocfg(code)
        self.assertEqual(cfg, {0: set([1]), 1: set([2, 3]), 2: set([1]), 3: set()})

    def test_multiple_while(self):
        code = '''{
                int x = 0;
                int y = 0;
                while(x<5){
                    x = x+1;
                }
                while(y<5){
                    y = y+1;
                }
                y = x;
            }'''
        cfg = codetocfg(code)
        self.assertEqual(cfg, {
            # first block (init x, y)
            0: set([1]),
            # first while connecting to second
            1: set([2, 3]), 2: set([1]), 3: set([4]),
            # second while
            4: set([5, 6]), 5: set([4]), 6: set()
        })

    def test_nested_while(self):
        code = '''{
                int x = 0;
                int y = 0;
                while(x<5){
                    x = x+1;
                    while(y<5){
                        y = y+1;
                    }
                }
                y = x;
            }'''
        cfg = codetocfg(code)
        self.assertEqual(cfg, {
            # first block (init x, y)
            0: set([1]),
            # first while could end into block 6
            1: set([2, 6]),
            2: set([3]),
            # second while
            3: set([4, 5]), 4: set([3]),
            # end of first while and endblock
            5: set([1]), 6: set()
        })


class TestWorklist(unittest.TestCase):

    def check_worklistalgo_is_cfg(self, code):
        bbs = codetobbs(code)
        cfg = codetocfg(code)

        # every block outuputs its block number
        def transfer(b, inb):
            return set([b])

        # if we work backwards we should create the control flow graph
        inb, _ = dataflow.worklist(bbs, cfg, lambda: set(), transfer, backward=True)
        self.assertEqual(inb, cfg)
        # if we work forwards we should create the inverse of the control flow graph
        inb, _ = dataflow.worklist(bbs, cfg, lambda: set(), transfer, backward=False)
        self.assertEqual(dataflow.invertgraph(inb), cfg)

    def test_while(self):
        code = """while(1) {
                int x = 2;
            }"""
        self.check_worklistalgo_is_cfg(code)

    def test_while_neighs(self):
        code = """{
                while(1){
                    int x = 1;
                }
                while(2){
                    int x = 2;
                }
                while(3){
                    int x = 3;
                }
            }"""
        self.check_worklistalgo_is_cfg(code)

    def test_while_nested(self):
        code = """while(1){
                while(2){
                    while(3){
                        int x = 2;
                    }
                }
            }"""
        self.check_worklistalgo_is_cfg(code)

    def test_reaching_definitions(self):
        # example from https://youtu.be/jnbMirDEByY?t=359
        code = """{
            int x = 0;
            int y = 0;
            int z = 1;
            while(x<5){
                x = x+1;
                if(x>=2){
                    y = 7;
                }else{
                    z = y;
                }
            }
            int d = x+y+z;
        }"""
        bbs = codetobbs(code)
        cfg = codetocfg(code)

        # a joinable map is a map from variables to sets
        # the join of a, b is done per element of the map
        # if one of the value's length is too large set it to 'TOP'
        class JoinableMap(dict):

            def __ior__(self, other):
                for el in other:
                    if el not in self:
                        self[el] = set()
                    self[el] |= other[el]
                    if len(self[el]) > 3:
                        self[el] = set(['T'])
                return self

        def transfer(b, inp):
            res = JoinableMap()
            if b == 0:
                res['x'] = set([0])
                res['y'] = set([0])
                res['z'] = set([1])
            if b in [1, 5, 6]:
                res['x'] = inp['x']
                res['y'] = inp['y']
                res['z'] = inp['z']
            if b == 2:
                if 'T' in inp['x']:
                    res['x'] = inp['x']
                else:
                    res['x'] = set([el + 1 for el in inp['x']])
                res['y'] = inp['y']
                res['z'] = inp['z']
            if b == 3:
                res['x'] = inp['x']
                res['y'] = set([7])
                res['z'] = inp['z']
            if b == 4:
                res['x'] = inp['x']
                res['y'] = inp['y']
                res['z'] = inp['y']
            if 'T' in res['x']:
                res['x'] = set(['T'])
            return res

        _, outb = dataflow.worklist(bbs, cfg, lambda: JoinableMap(), transfer, backward=False)
        self.assertEqual(outb[0], {'x': set([0]), 'y': set([0]), 'z': set([1])})
        self.assertEqual(outb[1], {'x': set(['T']), 'y': set([0, 7]), 'z': set([0, 1, 7])})
        self.assertEqual(outb[2], {'x': set(['T']), 'y': set([0, 7]), 'z': set([0, 1, 7])})
        self.assertEqual(outb[3], {'x': set(['T']), 'y': set([7]), 'z': set([0, 1, 7])})
        self.assertEqual(outb[4], {'x': set(['T']), 'y': set([0, 7]), 'z': set([0, 7])})
        self.assertEqual(outb[5], {'x': set(['T']), 'y': set([0, 7]), 'z': set([0, 1, 7])})
        self.assertEqual(outb[6], {'x': set(['T']), 'y': set([0, 7]), 'z': set([0, 1, 7])})


class TestLiveness(unittest.TestCase):

    def test_simplewhile1(self):
        code = """{
            int a = 0;
            int b = 0;
            while(1){
                a = b;
            }
        }"""
        bbs = codetobbs(code)
        cfg = codetocfg(code)

        outb, _ = dataflow.liveness(bbs, cfg)
        self.assertEqual(outb[0], set(['b']))
        self.assertEqual(outb[1], set(['b']))
        self.assertEqual(outb[2], set(['b']))
        self.assertEqual(outb[3], set())

    def test_simplewhile2(self):
        code = """{
            int a = 0;
            int b = 0;
            while(1){
                b = a;
                a = b;
            }
        }"""
        bbs = codetobbs(code)
        cfg = codetocfg(code)

        outb, _ = dataflow.liveness(bbs, cfg)
        self.assertEqual(outb[0], set(['a']))
        self.assertEqual(outb[1], set(['a']))
        self.assertEqual(outb[2], set(['a']))
        self.assertEqual(outb[3], set())

    def test_conswhile(self):
        code = """{
            int a = 0;
            int b = 0;
            while(1){
                b = a;
                a = b;
            }
            while(1){
                a = b;
                b = a;
            }
        }"""
        bbs = codetobbs(code)
        cfg = codetocfg(code)

        outb, _ = dataflow.liveness(bbs, cfg)
        self.assertEqual(outb[0], set(['a','b']))
        self.assertEqual(outb[1], set(['a','b']))
        self.assertEqual(outb[2], set(['a','b']))
        self.assertEqual(outb[3], set(['b']))
        self.assertEqual(outb[4], set(['b']))
        self.assertEqual(outb[5], set(['b']))
        self.assertEqual(outb[6], set())

    def test_nestedwhile(self):
        code = """{
            int a = 0;
            int b = 0;
            while(1){
                a = 1;
                while(2){
                    b = a;
                }
            }
        }"""
        bbs = codetobbs(code)
        cfg = codetocfg(code)
        print(cfg)

        outb, _ = dataflow.liveness(bbs, cfg, verbose=2)
        print(outb)
        # a = 0, b = 0
        self.assertEqual(outb[0], set())
        # while(1)
        self.assertEqual(outb[1], set())
        # a = 1
        self.assertEqual(outb[2], set(['a']))
        # while(2)
        self.assertEqual(outb[3], set(['a']))
        # b = a
        self.assertEqual(outb[4], set(['a']))
        # endwhile(2)
        self.assertEqual(outb[5], set())
        # endwhile(1)
        self.assertEqual(outb[6], set())

if __name__ == '__main__':
    unittest.main()
