import unittest
from copy import deepcopy
from src import three
from src import parser
from src import bb
from src import cfg
from src import lvn


def codetobbs(stringcode):
    return bb.threetobbs(three.asttothree(parser.parse(stringcode)))

def codetocfg(stringcode):
    return cfg.bbstocfg(bb.threetobbs(three.asttothree(parser.parse(stringcode))))

def extractvars(blocks):
    variables = set()
    tmpvariables = set()
    for bb in blocks:
        for op, _, _, name in bb:
            if op in ['jump','label','jumpfalse']: continue
            if name.startswith('.t'):
                tmpvariables.add(name)
            else:
                variables.add(name)
    return variables, tmpvariables

def valrec(values,name):
    if name is None:
        return None
    if type(name) is tuple:
        op, arg1, arg2 = name
        if op=='assign':
            return valrec(values,arg1)
        else:
            if op in ['+','*','==','!=']:
                return (op,set([valrec(values,arg1),valrec(values,arg2)]))
            else:
                return (op,valrec(values,arg1),valrec(values,arg2))
    if name in values:
        return valrec(values,values[name])
    return name

def getrecassignment(blocks,vrs):
    values = {}
    for bb in blocks:
        for op, arg1, arg2, result in bb:
            if op in ['jump', 'label', 'jumpfalse']: continue
            values[result] = (op, arg1, arg2)
    
    res = {}
    for v in vrs:
        res[v] = valrec(values,v)
    return res

class TestLVN(unittest.TestCase):

    def codetest(self, code):
        origblocks = codetobbs(code)
        newblocks = lvn.lvn(deepcopy(origblocks))
        # print(origblocks)
        # print(newblocks)

        # only one basic block
        self.assertEqual(len(origblocks),1)
        self.assertEqual(len(newblocks),1)

        # new code should be smaller
        self.assertTrue(len(origblocks[0])>len(newblocks[0]))

        # cfg should stay the same
        self.assertEqual(cfg.bbstocfg(origblocks),cfg.bbstocfg(newblocks))

        # all nontemporary variables should still be defined
        # a subset of temporary variables should still be defined
        vrs,tmpvrs = extractvars(origblocks)
        nvrs,ntmpvrs = extractvars(newblocks)
        self.assertEqual(vrs,nvrs)
        self.assertTrue(len(tmpvrs-ntmpvrs)>0)
        self.assertEqual(ntmpvrs-tmpvrs,set())

        # values should still be the same
        ass1 = getrecassignment(origblocks,vrs)
        ass2 = getrecassignment(newblocks,nvrs)
        self.assertEqual(ass1,ass2)
        return ntmpvrs

    def test_simplereplacement(self):
        code = '''{
            int x=1;
            int z=1;
        }'''
        self.codetest(code)

    def test_expressionreplacement(self):
        code = '''{
            int x=5+5;
            int z=5+5;
        }'''
        self.codetest(code)

    def test_varexpressionreplacement(self):
        code = '''{
            int x;
            int y = x + 1;
            int z = x + 1;
        }'''
        self.codetest(code)

    def test_complexreplacement(self):
        code = '''{
            int x=1;
            int y=2;
            int a = x+y;
            int b = x+y;
            a = 42;
            int c = x+y;
        }'''
        self.codetest(code)

    def test_jumpreplacement(self):
        code = '''{
            int x=1;
            if(x){
            }else{
            }
        }'''
        self.codetest(code)

    def test_expressioncommutative(self):
        code = '''{
            int x= 1+2;
            int y= 2+1;
            int z= 1*2;
            int a= 2*1;
            int b= 1==2;
            int c= 2==1;
        }'''
        ntmpvars = self.codetest(code)
        self.assertEqual(len(ntmpvars),3)

if __name__ == '__main__':
    unittest.main()
