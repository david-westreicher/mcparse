import unittest
from src.parser import parse
from src.dependence import dependence


class TestSimpleDependence(unittest.TestCase):

    def test_flow(self):
        code = """{
            int[4] arr;
            arr[2] = 0;
            int x = arr[3];
        }"""
        ast = parse(code)
        flow_source = ast.stmts[1].lhs
        flow_sink = ast.stmts[2].expression
        deps = dependence(ast)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].type, 'flow')
        self.assertEqual(deps[0].source, flow_source)
        self.assertEqual(deps[0].sink, flow_sink)
        self.assertEqual(deps[0].cat, None)

    def test_anti(self):
        code = """{
            int[4] arr;
            int x = arr[3];
            arr[2] = 0;
        }"""
        ast = parse(code)
        flow_sink = ast.stmts[2].lhs
        flow_source = ast.stmts[1].expression
        deps = dependence(ast)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].type, 'anti')
        self.assertEqual(deps[0].source, flow_source)
        self.assertEqual(deps[0].sink, flow_sink)
        self.assertEqual(deps[0].cat, None)

    def test_output(self):
        code = """{
            int[4] arr;
            arr[1] = 0;
            arr[2] = 0;
        }"""
        ast = parse(code)
        flow_source = ast.stmts[1].lhs
        flow_sink = ast.stmts[2].lhs
        deps = dependence(ast)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].type, 'output')
        self.assertEqual(deps[0].source, flow_source)
        self.assertEqual(deps[0].sink, flow_sink)
        self.assertEqual(deps[0].cat, None)

class TestLoopDependence(unittest.TestCase):

    def test_flow_ziv(self):
        code = """{
            int[4] arr;
            for(int i=0;i <3;i=i+1){
                arr[0] = arr[1];
            }
        }"""
        ast = parse(code)
        innerstmt = ast.stmts[1].stmt.stmts[0]
        flow_source = innerstmt.lhs
        flow_sink = innerstmt.rhs
        deps = dependence(ast)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].type, 'flow')
        self.assertEqual(deps[0].source, flow_source)
        self.assertEqual(deps[0].sink, flow_sink)
        self.assertEqual(deps[0].cat, 'ZIV')

    def test_flow_siv(self):
        code = """{
            int[4] arr;
            for(int i=0;i <3;i=i+1){
                arr[i] = arr[i+1];
            }
        }"""
        ast = parse(code)
        innerstmt = ast.stmts[1].stmt.stmts[0]
        flow_source = innerstmt.lhs
        flow_sink = innerstmt.rhs
        deps = dependence(ast)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].type, 'flow')
        self.assertEqual(deps[0].source, flow_source)
        self.assertEqual(deps[0].sink, flow_sink)
        self.assertEqual(deps[0].cat, 'SIV')

    def test_flow_miv(self):
        code = """{
            int[4] arr;
            for(int i=0;i<3;i=i+1){
                for(int j=0;j<3;j=j+1){
                    arr[i+j] = arr[i+1];
                }
            }
        }"""
        ast = parse(code)
        innerstmt = ast.stmts[1].stmt.stmts[0].stmt.stmts[0]
        flow_source = innerstmt.lhs
        flow_sink = innerstmt.rhs
        deps = dependence(ast)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].type, 'flow')
        self.assertEqual(deps[0].source, flow_source)
        self.assertEqual(deps[0].sink, flow_sink)
        self.assertEqual(deps[0].cat, 'MIV')

if __name__ == '__main__':
    unittest.main()
