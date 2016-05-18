import unittest
import os
from subprocess import call, Popen, PIPE
from tempfile import NamedTemporaryFile
from collections import defaultdict
from src.three import asttothree
from src.parser import parse
from src.bb import threetobbs
from src.lvn import lvn
from src.assembler import codetoassembly, ASMInstruction


def codetoasm(stringcode, asmfile=None):
    bbs = threetobbs(asttothree(parse(stringcode)))
    bbs = lvn(bbs)
    code = [tac for bblock in bbs for tac in bblock]
    return codetoassembly(code, verbose=-1, assemblyfile=asmfile)


class TestAssembler(unittest.TestCase):

    def evaluate(self, asm):
        vals = {'%esp': 0}
        valmapping = {}
        line = 6
        while asm[line].op is None and asm[line].comment is not None:
            var, stackstr = asm[line].comment.strip().split(':=')
            valmapping[stackstr.strip()] = var.strip()
            line += 1

        def const(mem_or_const):
            if type(mem_or_const) == str:
                if '$' in mem_or_const:
                    return int(mem_or_const[1:])
                else:
                    return vals[mem_or_const]
            return mem_or_const
        zf = False
        sf = False
        for instr in asm:
            if type(instr) == str or instr.op is None:
                continue
            if instr.op in ['mov', 'movl']:
                vals[instr.arg2] = const(instr.arg1)
            if instr.op == 'add':
                vals[instr.arg2] += const(instr.arg1)
            if instr.op == 'imul':
                vals['%eax'] = vals['%eax'] * const(instr.arg1)
            if instr.op == 'cdq':
                vals['%edx'] = 0
            if instr.op == 'idivl':
                vals['%eax'] = vals['%eax'] // const(instr.arg1)
                vals['%edx'] = vals['%eax'] % const(instr.arg1)
            if instr.op == 'sub':
                vals[instr.arg2] -= const(instr.arg1)
            if instr.op == 'cmp':
                tmp = const(instr.arg1) - const(instr.arg2)
                zf = tmp == 0
                sf = const(instr.arg1) > const(instr.arg2)
            if instr.op == 'sete':
                vals[instr.arg1] = 1 if (zf) else 0
            if instr.op == 'setne':
                vals[instr.arg1] = 1 if (not zf) else 0
            if instr.op == 'setg':
                vals[instr.arg1] = 1 if (not zf and not sf) else 0
            if instr.op == 'setge':
                vals[instr.arg1] = 1 if (not sf) else 0
            if instr.op == 'setl':
                vals[instr.arg1] = 1 if (sf) else 0
            if instr.op == 'setle':
                vals[instr.arg1] = 1 if (zf or sf) else 0

        for stackstr, var in valmapping.items():
            vals[var] = vals[stackstr]
        return vals

    def test_hasglobl(self):
        code = '''{
            int main(){
                return 0;
            }
        }'''
        asm = codetoasm(code)
        self.assertIn('.globl main', asm)

    def test_stackalloc(self):
        for vardefs in [[], ['x'], ['x', 'y'], ['x', 'y', 'z'], ['a', 'b', 'c', 'd', 'e', 'f', 'g']]:
            code = '''{
                void main(){
                    %s
                }
            }''' % ('\n'.join(['int %s = %d;' % (name, val) for val, name in enumerate(vardefs)]))
            asm = codetoasm(code)
            asm = [el for el in asm if type(el) is not str and el.op is not None]

            # save basepointer and set it to top of the stack
            self.assertEqual(ASMInstruction('push', '%ebp'), asm[1])
            self.assertEqual(ASMInstruction('mov', '%esp', '%ebp'), asm[2])

            # make space for n local registers
            n = len(vardefs)
            self.assertEqual(ASMInstruction('sub', '$' + str(n * 4), '%esp'), asm[3])

            # restore stack/base pointer and return
            self.assertEqual(ASMInstruction('mov', '%ebp', '%esp'), asm[-3])
            self.assertEqual(ASMInstruction('pop', '%ebp'), asm[-2])
            self.assertEqual(ASMInstruction('ret'), asm[-1])

    def test_compare_ops(self):
        for expr in [
                '10>2', '2>10', '10>10', '2<10', '10<2', '10<10',
                '10>=2', '2>=10', '10>=10', '2<=10', '10<=2', '10<=10',
                '10==2', '10==10', '2!=10', '10!=10']:
            code = '''{
                int main(){
                    return %s;
                }
            }''' % expr
            asm = codetoasm(code)
            vals = self.evaluate(asm)
            self.assertEqual(vals['%eax'], eval(expr))

    def test_unops(self):
        for expr in ['-(-4)', '-4', '! 0', '! 1', '- (! 0)']:
            code = '''{
                int main(){
                    return %s;
                }
            }''' % expr
            result = eval(expr.replace('!', 'not'))
            asm = codetoasm(code)
            vals = self.evaluate(asm)
            self.assertEqual(vals['%eax'], result)

    def test_expression(self):
        for expr in ['1', '1+2+3+4', '10-4', '1*2*3*4*5', '10/2', '10%4', '(31*20)/(4+(40-3))']:
            code = '''{
                int main(){
                    return %s;
                }
            }''' % expr
            result = int(eval(expr))
            asm = codetoasm(code)
            vals = self.evaluate(asm)
            self.assertEqual(vals['%eax'], result)

    def test_vars(self):
        code = '''{
            void main(){
                int x = 1;
                int y = x+1;
                int z = y*2;
            }
        }'''
        asm = codetoasm(code)
        vals = self.evaluate(asm)
        x = 1
        y = x + 1
        z = y * 2
        self.assertEqual(vals['x'], x)
        self.assertEqual(vals['y'], y)
        self.assertEqual(vals['z'], z)


class IntegrationTest(unittest.TestCase):

    def compile(self, codestr):
        asmfile = NamedTemporaryFile(suffix='.s', delete=False)
        code = codetoasm(codestr, asmfile.name)
        # print('\n'.join(map(str, code)))
        gcc = ['gcc', '-o', asmfile.name + '.bin', asmfile.name, 'assembler/lib.c', '-m32']
        call(gcc)
        return asmfile.name

    def execute_code(self, asmfile, inp=0):
        p = Popen([asmfile + '.bin'], stdin=PIPE, stdout=PIPE)
        inp = b'%d\n' % inp
        p.stdin.write(inp)
        p.stdin.flush()
        result = []
        for num in p.stdout:
            num = num.decode('utf-8')
            if ':' in num:
                _, num = num.split(':')
            result.append(int(num))
        p.stdin.close()
        p.stdout.close()
        p.wait()
        return result

    def clean(self, asmfile):
        os.remove(asmfile)
        os.remove(asmfile + '.bin')

    def test_fib(self):
        def fib(num):
            f1 = 0
            f2 = 1
            for i in range(num):
                nextfib = f1 + f2
                f1 = f2
                f2 = nextfib
            return f1
        code = '''{
            int fib(int n){
                int f1 = 0;
                int f2 = 1;
                for(int i=0;i<n;i=i+1){
                    int nextfib = f1+f2;
                    f1 = f2;
                    f2 = nextfib;
                }
                return f1;
            }
            void main(){
                int fib = fib(read_int());
                print_int(fib);
            }
        }'''
        asmfile = self.compile(code)
        for num in range(20):
            result = self.execute_code(asmfile, num)
            self.assertEqual(result, [fib(num)])
        self.clean(asmfile)

    def test_mutrec(self):
        code = '''{
            int is_even(int n){
                if (n!=0)
                    return is_odd(n-1);
                return 1;
            }
            int is_odd(int n){
                if (n!=0)
                    return is_even(n-1);
                return 0;
            }
            void main(){
                int x = read_int();
                print_int(is_even(x));
                print_int(is_odd(x));
            }
        }'''
        asmfile = self.compile(code)
        for num in range(20):
            result = self.execute_code(asmfile, num)
            self.assertEqual(result, [num % 2 == 0, num % 2 == 1])
        self.clean(asmfile)

    def test_multiple_params(self):
        code = '''{
            int first(int x, int y, int z, int a, int b){
                return x;
            }
            int second(int x, int y, int z, int a, int b){
                return y;
            }
            int third(int x, int y, int z, int a, int b){
                return z;
            }
            int fourth(int x, int y, int z, int a, int b){
                return a;
            }
            int fifth(int x, int y, int z, int a, int b){
                return b;
            }
            int main(){
                read_int();
                print_int(first(1,2,3,4,5));
                print_int(second(1,2,3,4,5));
                print_int(third(1,2,3,4,5));
                print_int(fourth(1,2,3,4,5));
                print_int(fifth(1,2,3,4,5));
                return 0;
            }
        }'''
        asmfile = self.compile(code)
        result = self.execute_code(asmfile)
        self.assertEqual(result, list(range(1, 6)))
        self.clean(asmfile)

    def test_primes(self):
        def primes(num):
            if num <= 1:
                return [1]
            primeres = []
            for i in range(num + 1):
                isprime = True
                for j in range(2, i):
                    if (i % j) == 0:
                        isprime = False
                if isprime:
                    primeres.append(i)
            return primeres

        code = '''{
            void primes(int num){
                if(num<=1){
                    print_int(1);
                    return;
                }
                for(int i=0;i<(num+1);i=i+1){
                    int isprime = 1;
                    for(int j=2;j<i;j=j+1){
                        if((i%j)==0){
                            isprime = 0;
                        }
                    }
                    if(isprime){
                        print_int(i);
                    }
                }
                return;
            }
            int main(){
                primes(read_int());
                return 0;
            }
        }'''
        asmfile = self.compile(code)
        for num in range(0, 5000, 1000):
            result = self.execute_code(asmfile, num)
            self.assertEqual(result, primes(num))
        self.clean(asmfile)


if __name__ == '__main__':
    unittest.main()
