import unittest
from itertools import product
from src import three
from src import parser
from src import bb
from src import cfg
from src import dataflow
from src import lvn
from src import vm
from src import callgraph


def codetocallgraph(stringcode):
    return callgraph.bbstocallgraph(bb.threetobbs(three.asttothree(parser.parse(stringcode))))


class TestCallGraph(unittest.TestCase):

    def test_nothing(self):
        code = """{
        }"""
        cg = codetocallgraph(code)
        self.assertEqual(cg, {
            '__global__': set()
        })

    def test_just_global(self):
        code = """{
            int x = 0;
            int y = 0;
        }"""
        cg = codetocallgraph(code)
        self.assertEqual(cg, {
            '__global__': set()
        })

    def test_global_simplecall(self):
        code = """{
            int x = init();
            int init(){
                return 0;
            }
        }"""
        cg = codetocallgraph(code)
        self.assertEqual(cg, {
            '__global__': set(['init']),
            'init': set()
        })

    def test_global_main_implicit(self):
        code = """{
            int x = init();
            int init(){
                return 0;
            }
            int main(){
                return 0;
            }
        }"""
        cg = codetocallgraph(code)
        self.assertEqual(cg, {
            '__global__': set(['init', 'main']),
            'init': set(),
            'main': set(),
        })

    def test_no_global(self):
        code = """{
            int main(){
                return 0;
            }
        }"""
        cg = codetocallgraph(code)
        self.assertEqual(cg, {
            'main': set(),
        })

    def test_rec(self):
        code = """{
            int rec(){
                return rec();
            }
        }"""
        cg = codetocallgraph(code)
        self.assertEqual(cg, {
            'rec': set(['rec']),
        })

    def test_mut_rec(self):
        code = """{
            int even(int n){
                return !odd(n-1);
            }
            int odd(int n){
                return !even(n-1);
            }
        }"""
        cg = codetocallgraph(code)
        self.assertEqual(cg, {
            'even': set(['odd']),
            'odd': set(['even']),
        })

    def test_chain(self):
        code = """{
            int a(){
                return b();
            }
            int b(){
                return c();
            }
            int c(){
                return d();
            }
            int d(){
                return e();
            }
            int e(){
                return 0;
            }
        }"""
        cg = codetocallgraph(code)
        self.assertEqual(cg, {
            'a': set(['b']),
            'b': set(['c']),
            'c': set(['d']),
            'd': set(['e']),
            'e': set(),
        })

    def test_long_cycle(self):
        code = """{
            int a(){
                return b();
            }
            int b(){
                return c();
            }
            int c(){
                return d();
            }
            int d(){
                return e();
            }
            int e(){
                return a();
            }
        }"""
        cg = codetocallgraph(code)
        self.assertEqual(cg, {
            'a': set(['b']),
            'b': set(['c']),
            'c': set(['d']),
            'd': set(['e']),
            'e': set(['a']),
        })

    def test_complex_graph(self):
        code = """{
            void a(){
                b();
                c();
                e();
            }
            void b(){
                f();
            }
            void c(){
                b();
                a();
            }
            void d(){
            }
            void e(){
                b();
                d();
            }
            void f(){
                a();
                b();
                c();
                d();
                e();
                f();
            }
        }"""
        cg = codetocallgraph(code)
        self.assertEqual(cg, {
            'a': set(['b', 'c', 'e']),
            'b': set(['f']),
            'c': set(['b', 'a']),
            'd': set([]),
            'e': set(['b', 'd']),
            'f': set(['a', 'b', 'c', 'd', 'e', 'f']),
        })

if __name__ == '__main__':
    unittest.main()
