import unittest
from src import three
from src import parser
from src import bb
from src import cfg
from src import dataflow


def codetobbs(stringcode):
    return bb.threetobbs(three.asttothree(parser.parse(stringcode)))


def codetocfg(stringcode):
    return cfg.bbstocfg(bb.threetobbs(three.asttothree(parser.parse(stringcode))))


class TestInverseGraph(unittest.TestCase):

    def test_emptygraph(self):
        g = {}
        inv = dataflow.invertgraph(g)
        self.assertEqual(g, inv)

    def test_emptyinversegraph(self):
        g = {0: set(), 1: set(), 2: set()}
        inv = dataflow.invertgraph(g)
        self.assertEqual(inv, g)

    def test_simplegraph(self):
        g = {0: set([1]), 1: set([2]), 2: set()}
        inv = dataflow.invertgraph(g)
        self.assertEqual(inv, {0: set(), 1: set([0]), 2: set([1])})

    def test_loopgraph(self):
        g = {0: set([1]), 1: set([2]), 2: set([0])}
        inv = dataflow.invertgraph(g)
        self.assertEqual(inv, {0: set([2]), 1: set([0]), 2: set([1])})

    def test_fullyconnectedgraph(self):
        g = {0: set([1, 2]), 1: set([0, 2]), 2: set([0, 1])}
        inv = dataflow.invertgraph(g)
        self.assertEqual(inv, {0: set([1, 2]), 1: set([0, 2]), 2: set([0, 1])})

    def test_selfconnection(self):
        g = {0: set([0, 1]), 1: set([1, 2]), 2: set([2, 0])}
        inv = dataflow.invertgraph(g)
        self.assertEqual(inv, {0: set([0, 2]), 1: set([1, 0]), 2: set([2, 1])})

    def test_complexgraph(self):
        g = {0: set([1]), 1: set([2, 3]), 2: set([0, 3]), 3: set([1, 3])}
        inv = dataflow.invertgraph(g)
        self.assertEqual(inv, {0: set([2]), 1: set([0, 3]), 2: set([1]), 3: set([1, 2, 3])})


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

    def test_cfggenerator_singleblock(self):
        code = '''{
            int x = 0;
            int y = 0;
            int z = 0;
        }'''
        self.check_worklistalgo_is_cfg(code)

    def test_cfggenerator_simple_if(self):
        code = '''{
            int x = 0;
            if(1){
                x = 1;
            }else{
                x = 2;
            }
            x = 3;
        }'''
        self.check_worklistalgo_is_cfg(code)

    def test_cfggenerator_nested_if(self):
        code = '''{
            int x = 0;
            if(1){
                if(1){
                    x = 1;
                }else{
                    x = 2;
                }
            }else{
                if(1){
                    x = 3;
                }else{
                    x = 4;
                }
            }
            x = 5;
        }'''
        self.check_worklistalgo_is_cfg(code)

    def test_reaching_definitions(self):
        # example from https://youtu.be/jnbMirDEByY?t=359
        bbs = []
        bbs.append([
            ['assign', 0, None, 'x'],
            ['assign', 0, None, 'y'],
            ['assign', 1, None, 'z']
        ])
        bbs.append([
            ['+', 'x', 1, 'x']
        ])
        bbs.append([
            ['assign', 7, None, 'y']
        ])
        bbs.append([
            ['assign', 'y', None, 'z']
        ])
        bbs.append([
            ['label', None, None, 'L']
        ])
        cfg = {0: set([1, 4]), 1: set([2, 3]), 2: set([1, 4]), 3: set([1, 4]), 4: set()}

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
            if b == 1:
                if 'T' in inp['x']:
                    res['x'] = inp['x']
                else:
                    res['x'] = set([el + 1 for el in inp['x']])
                res['y'] = inp['y']
                res['z'] = inp['z']
            if b == 2:
                res['x'] = inp['x']
                res['y'] = set([7])
                res['z'] = inp['z']
            if b == 3:
                res['x'] = inp['x']
                res['y'] = inp['y']
                res['z'] = inp['y']
            if b == 4:
                res['x'] = inp['x']
                res['y'] = inp['y']
                res['z'] = inp['z']
            if 'T' in res['x']:
                res['x'] = set(['T'])
            return res

        _, outb = dataflow.worklist(bbs, cfg, lambda: JoinableMap(), transfer, backward=False)
        self.assertEqual(outb[0], {'x': set([0]), 'y': set([0]), 'z': set([1])})
        self.assertEqual(outb[1], {'x': set(['T']), 'y': set([0, 7]), 'z': set([0, 1, 7])})
        self.assertEqual(outb[2], {'x': set(['T']), 'y': set([7]), 'z': set([0, 1, 7])})
        self.assertEqual(outb[3], {'x': set(['T']), 'y': set([0, 7]), 'z': set([0, 7])})
        self.assertEqual(outb[4], {'x': set(['T']), 'y': set([0, 7]), 'z': set([0, 1, 7])})


class TestLiveness(unittest.TestCase):

    def test_single_block_no_vars(self):
        bbs = []
        bbs.append([
            ['assign', 3, None, 'a'],
            ['assign', 5, None, 'b'],
            ['assign', 4, None, 'd'],
            ['assign', 100, None, 'x']
        ])
        cfg = {0: set()}

        outb, inb = dataflow.liveness(bbs, cfg)
        # outb should be zero set because no inputs to 1 block
        # inb = uevars | (livein - killed) = 0 | (0 - {a,b,d,x}) = 0
        self.assertEqual(outb[0], set())
        self.assertEqual(inb[0], set())

    def test_single_block_with_vars(self):
        bbs = []
        bbs.append([
            ['assign', 'a', None, 'x'],
            ['assign', 'b', None, 'x'],
            ['assign', 'c', None, 'x'],
        ])
        cfg = {0: set()}

        outb, inb = dataflow.liveness(bbs, cfg)
        # outb should be zero set because no inputs to 1 block
        # inb = uevars | (livein - killed) = {a,b,c} | (0 - {x}) = {a,b,c}
        self.assertEqual(outb[0], set())
        self.assertEqual(inb[0], set(['a', 'b', 'c']))

    def test_two_block_with_killing(self):
        bbs = []
        bbs.append([
            ['assign', 3, None, 'a'],
            ['assign', 5, None, 'b'],
            ['assign', 4, None, 'd'],
        ])
        bbs.append([
            ['assign', 'a', None, 'x'],
            ['assign', 'b', None, 'x'],
            ['assign', 'c', None, 'x'],
        ])
        cfg = {0: set([1]), 1: set()}

        outb, inb = dataflow.liveness(bbs, cfg)
        # outb[0] should be inb[1]
        # inb[0] = uevars | (outb[0] - killed) = 0 | ({a,b,c} - {a,b,d}) = {c}
        # outb[1] should be zero set because no succ. of 1
        # inb[1] = uevars | (outb[1] - killed) = {a,b,c} | (0 - {x}) = {a,b,c}
        self.assertEqual(outb[0], inb[1])
        self.assertEqual(outb[1], set())
        self.assertEqual(inb[0], set(['c']))
        self.assertEqual(inb[1], set(['a','b','c']))

    def test_wikiexample(self):
        # example from https://en.wikipedia.org/wiki/Live_variable_analysis
        bbs = []
        bbs.append([
            ['assign', 3, None, 'a'],
            ['assign', 5, None, 'b'],
            ['assign', 4, None, 'd'],
            ['assign', 100, None, 'x']
        ])
        bbs.append([
            ['+', 'a', 'b', 'c'],
            ['assign', 2, None, 'd']
        ])
        bbs.append([
            ['assign', 4, None, 'c'],
            ['*', 'b', 'd', '.t1'],
            ['+', 'c', '.t1', '.t1'],
            ['assign', '.t1', None, 'y']
        ])
        cfg = {0: set([1, 2]), 1: set([2]), 2: set()}

        outb, inb = dataflow.liveness(bbs, cfg)
        self.assertEqual(inb[0], set())
        self.assertEqual(inb[1], set(['a', 'b']))
        self.assertEqual(inb[2], set(['b', 'd']))
        self.assertEqual(outb[0], set(['a', 'b', 'd']))
        self.assertEqual(outb[1], set(['b', 'd']))
        self.assertEqual(outb[2], set())

    def test_slideexample(self):
        # example from the slides
        bbs = []
        bbs.append([
            ['assign', 1, None, 'i']
        ])
        bbs.append([
            ['assign', 1, None, 'a'],
            ['assign', 1, None, 'c']
        ])
        bbs.append([
            ['assign', 1, None, 'b'],
            ['assign', 1, None, 'c'],
            ['assign', 1, None, 'd']
        ])
        bbs.append([
            ['assign', 1, None, 'a'],
            ['assign', 1, None, 'd']
        ])
        bbs.append([
            ['assign', 1, None, 'd']
        ])
        bbs.append([
            ['assign', 1, None, 'c']
        ])
        bbs.append([
            ['assign', 1, None, 'b']
        ])
        bbs.append([
            ['+', 'a', 'b', 'y'],
            ['+', 'c', 'd', 'z'],
            ['+', 'i', 1, 'i']])
        cfg = {0: set([1]), 1: set([2, 3]), 2: set([7]), 3: set([4, 5]), 4: set([6]), 5: set([6]), 6: set([7]), 7: set([1])}

        outb, _ = dataflow.liveness(bbs, cfg)
        self.assertEqual(outb[0], set(['i']))
        self.assertEqual(outb[1], set(['a', 'c', 'i']))
        self.assertEqual(outb[2], set(['a', 'b', 'c', 'd', 'i']))
        self.assertEqual(outb[3], set(['a', 'c', 'd', 'i']))
        self.assertEqual(outb[4], set(['a', 'c', 'd', 'i']))
        self.assertEqual(outb[5], set(['a', 'c', 'd', 'i']))
        self.assertEqual(outb[6], set(['a', 'b', 'c', 'd', 'i']))
        self.assertEqual(outb[7], set(['i']))

if __name__ == '__main__':
    unittest.main()
