import unittest
from src import three
from src import parser
from src import bb
from src import cfg


def codetobbs(stringcode):
    return bb.threetobbs(three.asttothree(parser.parse(stringcode)))

def codetocfg(stringcode):
    return cfg.bbstocfg(bb.threetobbs(three.asttothree(parser.parse(stringcode))))

class TestCFG(unittest.TestCase):

    def test_singlenode(self):
        code = '''{
            int x=1;
            int y=1;
            int z=1;
        }'''
        cfg = codetocfg(code)
        self.assertEqual(len(cfg),1)
        for el in cfg:
            children = cfg[el]
            self.assertEqual(len(children),0)

    def test_nestedcompound(self):
        code = '''{
            int x=1;
            int y=1;
            {
                int z=1;
            }
        }'''
        cfg = codetocfg(code)
        self.assertEqual(len(cfg),1)
        for el in cfg:
            children = cfg[el]
            self.assertEqual(len(children),0)

    def test_ifwithoutelse(self):
        code = '''{
            int x=1;
            if(x){
                int z=1;
            }
        }'''
        # should produce 0 -> 1,2 ; 1 -> 2
        cfg = codetocfg(code)
        self.assertEqual(len(cfg),3)
        self.assertEqual(cfg[0],set([1,2]))
        self.assertEqual(cfg[1],set([2]))
        self.assertEqual(cfg[2],set([]))

    def test_ifcomplete(self):
        code = '''{
            int x=1;
            if(x){
                int z=1;
            }else{
                int z=2;
            }
        }'''
        # should produce 0 -> 1,2 ; 1 -> 3 ; 2 -> 3
        cfg = codetocfg(code)
        self.assertEqual(len(cfg),4)
        self.assertEqual(cfg[0],set([1,2]))
        self.assertEqual(cfg[1],set([3]))
        self.assertEqual(cfg[2],set([3]))
        self.assertEqual(cfg[3],set([]))

    def test_nestedif(self):
        code = '''{
            int x=1;
            if(x){
                int z=1;
                if(z){
                    z=2;
                }else{
                    z=2;
                }
            }else{
                int z=1;
                if(z){
                    z=2;
                }else{
                    z=2;
                }
            }
        }'''
        # should produce 0 -> 
        cfg = codetocfg(code)
        self.assertEqual(len(cfg),10)
        self.assertEqual(cfg[0],set([1,5]))
        self.assertEqual(cfg[1],set([2,3]))
        self.assertEqual(cfg[2],set([4]))
        self.assertEqual(cfg[3],set([4]))
        self.assertEqual(cfg[4],set([9]))
        self.assertEqual(cfg[5],set([6,7]))
        self.assertEqual(cfg[6],set([8]))
        self.assertEqual(cfg[7],set([8]))
        self.assertEqual(cfg[8],set([9]))
        self.assertEqual(cfg[9],set())

if __name__ == '__main__':
    unittest.main()
