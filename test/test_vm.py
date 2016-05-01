import unittest
from src import three
from src import parser
from src import bb
from src import lvn
from src import cfg
from src import dataflow
from src import vm


def executecode2(stringcode):
    print('\n' + stringcode)
    bbs = lvn.lvn(bb.threetobbs(three.asttothree(parser.parse(stringcode, verbose=1)), verbose=1), verbose=1)
    return vm.run(bbs, verbose=1)


def executecode(stringcode):
    bbs = lvn.lvn(bb.threetobbs(three.asttothree(parser.parse(stringcode))))
    return vm.run(bbs)


class TestAssignments(unittest.TestCase):

    def test_empty(self):
        code = '''int x;'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 0)
        code = '''float x;'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 0.0)

    def test_simple(self):
        for i in range(-10, 10):
            code = '''int x = %d;''' % i
            vals = executecode(code)
            self.assertEqual(vals['x'], i)
        for i in range(-10, 10):
            val = i + 0.5
            code = '''float x = %f;''' % val
            vals = executecode(code)
            self.assertEqual(vals['x'], val)

    def test_multiple(self):
        for i in range(-10, 10):
            for j in range(-10, 10):
                code = '''{
                    int x = %d;
                    int y = %d;
                }''' % (i, j)
                vals = executecode(code)
                self.assertEqual(vals['x'], i)
                self.assertEqual(vals['y'], j)
        for i in range(-10, 10):
            for j in range(-10, 10):
                val1 = i + 0.5
                val2 = j + 0.5
                code = '''{
                    float x = %f;
                    float y = %f;
                }''' % (val1, val2)
                vals = executecode(code)
                self.assertEqual(vals['x'], val1)
                self.assertEqual(vals['y'], val2)


class TestCompounds(unittest.TestCase):

    def test_simple(self):
        code = '''{
            int x = 1;
            int y = 2;
            {
                y = x;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 1)
        self.assertEqual(vals['y'], 1)
        code = '''{
            int x = 1;
            int y = 2;
            {
                x = y;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 2)
        self.assertEqual(vals['y'], 2)

    def test_neighbor(self):
        code = '''{
            int x = 1;
            int y = 2;
            {
                x = 3;
            }
            {
                y = 4;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 3)
        self.assertEqual(vals['y'], 4)

    def test_nested(self):
        code = '''{
            int x = 1;
            int y = 2;
            {
                x = 3;
                {
                    y = 4;
                }
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 3)
        self.assertEqual(vals['y'], 4)


class TestExpression(unittest.TestCase):

    def test_bin_simple(self):
        for a in range(-5, 5):
            for b in range(-5, 5):
                code = '''int x = (%d) + (%d);''' % (a, b)
                self.assertEqual(executecode(code)['x'], a + b)
                code = '''int x = (%d) * (%d);''' % (a, b)
                self.assertEqual(executecode(code)['x'], a * b)
                code = '''int x = (%d) - (%d);''' % (a, b)
                self.assertEqual(executecode(code)['x'], a - b)
                if b != 0:
                    code = '''int x = (%d) / (%d);''' % (a, b)
                    self.assertEqual(executecode(code)['x'], a // b)
                    code = '''int x = (%d) %% (%d);''' % (a, b)
                    self.assertEqual(executecode(code)['x'], a % b)
                code = '''int x = (%d) == (%d);''' % (a, b)
                self.assertEqual(executecode(code)['x'], a == b)
                code = '''int x = (%d) != (%d);''' % (a, b)
                self.assertEqual(executecode(code)['x'], a != b)
                code = '''int x = (%d) <= (%d);''' % (a, b)
                self.assertEqual(executecode(code)['x'], a <= b)
                code = '''int x = (%d) >= (%d);''' % (a, b)
                self.assertEqual(executecode(code)['x'], a >= b)
                code = '''int x = (%d) > (%d);''' % (a, b)
                self.assertEqual(executecode(code)['x'], a > b)
                code = '''int x = (%d) < (%d);''' % (a, b)
                self.assertEqual(executecode(code)['x'], a < b)

    def test_un_simple(self):
        for a in range(-5, 5):
            code = '''int x = (%d);''' % a
            self.assertEqual(executecode(code)['x'], a)
            code = '''int x = -(%d);''' % a
            self.assertEqual(executecode(code)['x'], -a)
            code = '''int x = !(%d);''' % a
            self.assertEqual(executecode(code)['x'], not a)

    def test_bin_multiple(self):
        code = '''int x = 1*2*3*4;'''
        self.assertEqual(executecode(code)['x'], 24)
        code = '''int x = 1+2+3+4;'''
        self.assertEqual(executecode(code)['x'], 10)
        # spec says that '-' and '/' is rightassociative :(
        code = '''int x = 1-(2-(3-4));'''
        self.assertEqual(executecode(code)['x'], -2)
        code = '''int x = 1-2-3-4;'''
        self.assertEqual(executecode(code)['x'], -2)
        code = '''int x = ((1-2)-3)-4;'''
        self.assertEqual(executecode(code)['x'], -8)
        code = '''int x = 24/(6/2);'''
        self.assertEqual(executecode(code)['x'], 8)
        code = '''int x = 24/6/2;'''
        self.assertEqual(executecode(code)['x'], 8)
        code = '''int x = (24/6)/2;'''
        self.assertEqual(executecode(code)['x'], 2)

    def test_bin_un_mixed(self):
        code = '''int x = 1*-3;'''
        self.assertEqual(executecode(code)['x'], -3)
        code = '''int x = -1*3;'''
        self.assertEqual(executecode(code)['x'], -3)
        code = '''int x = -1*-3;'''
        self.assertEqual(executecode(code)['x'], 3)
        code = '''int x = 3+-2;'''
        self.assertEqual(executecode(code)['x'], 1)
        # spec says that unop '-' binds stronger :(
        code = '''int x = -(3+2);'''
        self.assertEqual(executecode(code)['x'], -5)
        code = '''int x = -3+2;'''
        self.assertEqual(executecode(code)['x'], -5)
        code = '''int x = (-3)+2;'''
        self.assertEqual(executecode(code)['x'], -1)
        code = '''int x = -3+-2;'''
        self.assertEqual(executecode(code)['x'], -1)
        code = '''int x = -(3+-2);'''
        self.assertEqual(executecode(code)['x'], -1)
        code = '''int x = (-3)+(-2);'''
        self.assertEqual(executecode(code)['x'], -5)
        code = '''int x = 6/-2;'''
        self.assertEqual(executecode(code)['x'], -3)
        code = '''int x = -6/2;'''
        self.assertEqual(executecode(code)['x'], -3)
        code = '''int x = -6/-2;'''
        self.assertEqual(executecode(code)['x'], 3)

    def test_complex(self):
        # spec  doesn't care about which operator binds stronger (all is rightassociative)
        code = '''int x = 3*(2+1)-1;'''
        self.assertEqual(executecode(code)['x'], 6)
        code = '''int x = 3*((2+1)-1);'''
        self.assertEqual(executecode(code)['x'], 6)
        code = '''int x = (3*(2+1))-1;'''
        self.assertEqual(executecode(code)['x'], 8)
        code = '''int x = ((1+2+3)*(1*2+2))-10;'''
        self.assertEqual(executecode(code)['x'], 14)
        code = '''int x = (((1+2+3)*4)/2)*5;'''
        self.assertEqual(executecode(code)['x'], 60)
        code = '''int x = 5*5-1/2/2/2;'''
        self.assertEqual(executecode(code)['x'], 25)
        code = '''int x = 5*(5-(1/(2/(2/2))));'''
        self.assertEqual(executecode(code)['x'], 25)
        code = '''{
            int x = 4*(5-(1/(2/(2/2))));
            int r1 = (x-5)/5;
            int r2 = (x-5)*x;
            int r3 = (5-x)+x;
            int r4 = -x;
            int r5 = 200/x;
        }'''
        self.assertEqual(executecode(code)['x'], 20)
        self.assertEqual(executecode(code)['r1'], 3)
        self.assertEqual(executecode(code)['r2'], 300)
        self.assertEqual(executecode(code)['r3'], 5)
        self.assertEqual(executecode(code)['r4'], -20)
        self.assertEqual(executecode(code)['r5'], 10)


class TestIf(unittest.TestCase):

    def test_simple(self):
        code = '''{
            int x = 0;
            if(1){
                x = 1;
            }else{
                x = 2;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 1)
        code = '''{
            int x = 0;
            if(0){
                x = 1;
            }else{
                x = 2;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 2)

    def test_expression(self):
        code = '''{
            int x = 0;
            if(x==x){
                x = 1;
            }else{
                x = 2;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 1)
        code = '''{
            int x = 0;
            if(x!=x){
                x = 1;
            }else{
                x = 2;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 2)
        code = '''{
            int x = 0;
            if(x>-1){
                x = 1;
            }else{
                x = 2;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 1)
        code = '''{
            int x = 0;
            if(x<-1){
                x = 1;
            }else{
                x = 2;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 2)

    def test_nested(self):
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
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 1)
        code = '''{
            int x = 0;
            if(1){
                if(0){
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
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 2)
        code = '''{
            int x = 0;
            if(0){
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
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 3)
        code = '''{
            int x = 0;
            if(0){
                if(1){
                    x = 1;
                }else{
                    x = 2;
                }
            }else{
                if(0){
                    x = 3;
                }else{
                    x = 4;
                }
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 4)

    def test_neigh(self):
        code = '''{
            int x = 0;
            int y = 0;
            if(1){
                x = 1;
            }
            if(1){
                y = 1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 1)
        self.assertEqual(vals['y'], 1)
        code = '''{
            int x = 0;
            int y = 0;
            if(0){
                x = 1;
            }
            if(1){
                y = 1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 0)
        self.assertEqual(vals['y'], 1)
        code = '''{
            int x = 0;
            int y = 0;
            if(1){
                x = 1;
            }
            if(0){
                y = 1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 1)
        self.assertEqual(vals['y'], 0)
        code = '''{
            int x = 0;
            int y = 0;
            if(0){
                x = 1;
            }
            if(0){
                y = 1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 0)
        self.assertEqual(vals['y'], 0)


class TestWhile(unittest.TestCase):

    def test_simple(self):
        code = '''{
            int x = 0;
            while(0){
                x = x+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 0)
        code = '''{
            int x = 0;
            while(x<10){
                x = x+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 10)
        code = '''{
            int x = 0;
            int y = 0;
            while(x==0){
                x = 1;
                y = y+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 1)
        self.assertEqual(vals['y'], 1)

    def test_nested(self):
        code = '''{
            int x = 0;
            int z = 0;
            while(x<10){
                x = x+1;
                int y = 0;
                while(y<5){
                    z = z+1;
                    y = y+1;
                }
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 10)
        self.assertEqual(vals['y'], 5)
        self.assertEqual(vals['z'], 10 * 5)

    def test_neigh(self):
        code = '''{
            int x = 0;
            int z = 0;
            while(x<10){
                z = z+1;
                x = x+1;
            }
            int y = 0;
            while(y<5){
                z = z+1;
                y = y+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 10)
        self.assertEqual(vals['y'], 5)
        self.assertEqual(vals['z'], 10 + 5)


class TestFor(unittest.TestCase):

    def test_simple(self):
        # condition doesn't hold
        code = '''{
            int i;
            int x = 0;
            for(i=0; 0; i=i+1){
                x = x+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['i'], 0)
        self.assertEqual(vals['x'], 0)
        # for i in range(0,10) : x++
        code = '''{
            int i;
            int x = 0;
            for(i=0; i<10; i=i+1){
                x = x+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['i'], 10)
        self.assertEqual(vals['x'], 10)
        # test afterthought
        code = '''{
            int i;
            int x = 0;
            for(i=0; i<10; i=i+2){
                x = x+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['i'], 10)
        self.assertEqual(vals['x'], 10 / 2)
        code = '''{
            int i;
            int x = 0;
            for(i=0; i<10; i=i+5){
                x = x+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['i'], 10)
        self.assertEqual(vals['x'], 10 / 5)
        # test initialization
        code = '''{
            int i;
            int x = 0;
            for(i=1; i<10; i=i+1){
                x = x+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['i'], 10)
        self.assertEqual(vals['x'], 10 - 1)
        code = '''{
            int i;
            int x = 0;
            for(i=8; i<10; i=i+1){
                x = x+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['i'], 10)
        self.assertEqual(vals['x'], 10 - 8)

    def test_reverse(self):
        # for i in range(10,0,-1) : x++
        code = '''{
            int i;
            int x = 0;
            for(i=10; i>0; i=i-1){
                x = x+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['i'], 0)
        self.assertEqual(vals['x'], 10)

    def test_nested(self):
        code = '''{
            int i;
            int x = 0;
            for(i=0; i<10; i=i+1){
                x = x+1;
                int j;
                for(j=0; j<10; j=j+1){
                    x = x+1;
                }
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['i'], 10)
        self.assertEqual(vals['j'], 10)
        self.assertEqual(vals['x'], 10 + 10 * 10)
        code = '''{
            int i;
            int x = 0;
            for(i=0; i<5; i=i+1){
                x = x+1;
                int j;
                for(j=0; j<4; j=j+1){
                    x = x+1;
                    int k;
                    for(k=0; k<3; k=k+1){
                        x = x+1;
                    }
                }
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['i'], 5)
        self.assertEqual(vals['j'], 4)
        self.assertEqual(vals['k'], 3)
        self.assertEqual(vals['x'], (((1) * 3 + 1) * 4 + 1) * 5)

    def test_neigh(self):
        code = '''{
            int i;
            int x = 0;
            int y = 0;
            for(i=0; i<10; i=i+1){
                x = x+1;
            }
            for(i=0; i<5; i=i+1){
                x = x+1;
                y = y+1;
            }
        }'''
        vals = executecode(code)
        self.assertEqual(vals['x'], 10 + 5)
        self.assertEqual(vals['y'], 5)


class TestAlgorithms(unittest.TestCase):

    def test_minmax(self):
        for a in range(-5, 5):
            for b in range(-5, 5):
                code = '''{
                    int a = %d;
                    int b = %d;
                    int min;
                    int max;
                    if(a>b){
                        max = a;
                        min = b;
                    }else{
                        max = b;
                        min = a;
                    }
                }''' % (a, b)
                vals = executecode(code)
                self.assertEqual(vals['a'], a)
                self.assertEqual(vals['b'], b)
                self.assertEqual(vals['max'], max(a, b))
                self.assertEqual(vals['min'], min(a, b))

    def test_multiples_of_3and5(self):
        # https://projecteuler.net/problem=1
        def pythsol(m):
            res = 0
            for i in range(1, m):
                if i % 3 == 0 or i % 5 == 0:
                    res += i
            return res

        for m in range(10, 100, 10):
            code = '''{
                int max = %d;
                int sol = 0;
                int i;
                for(i=1;i<max;i=i+1){
                    int div3 = i/3;
                    int div5 = i/5;
                    if((div3*3) == i){
                        sol = sol+i;
                    }else{
                        if((div5*5) == i){
                            sol = sol+i;
                        }
                    }
                }
            }''' % m
            vals = executecode(code)
            self.assertEqual(vals['sol'], pythsol(m))

    def test_fibonacci(self):
        def pythsol(m):
            f1 = 0
            f2 = 1
            while(f2 <= m):
                nextfib = f1 + f2
                if nextfib >= m:
                    break
                f1 = f2
                f2 = nextfib
            return f2

        for m in range(1, 100):
            code = '''{
                int max = %d;
                int f1 = 0;
                int f2 = 1;
                int sol;
                while(f2<=max){
                    int nextfib = f1+f2;
                    if(nextfib>=max){
                        sol = f2;
                        f2 = max+1;
                    }else{
                        f1 = f2;
                        f2 = nextfib;
                    }
                }
            }''' % m
            vals = executecode(code)
            self.assertEqual(vals['sol'], pythsol(m))

    def test_reverse(self):
        def pythsol(num):
            return int(''.join(list(reversed(str(num)))))

        for num in range(1, 100):
            code = '''{
                int num = %d;
                int rev = 0;
                int len = 0;
                int num2 = num;
                while(num2>0){
                    num2 = num2/10;
                    len=len+1;
                }
                while(len>0){
                    int mod = num %% 10;
                    num = num/10;
                    rev = (rev*10)+mod;
                    len = len-1;
                }
            }''' % num
            vals = executecode(code)
            self.assertEqual(vals['rev'], pythsol(num))

    def test_palindrome(self):
        # https://projecteuler.net/problem=4
        def pythsol(ndigits):
            largest = 0
            for i in range(10**ndigits):
                for j in range(i, 10**ndigits):
                    if str(i * j) == ''.join(list(reversed(str(i * j)))):
                        if i * j > largest:
                            largest = i * j
            return largest

        for digits in range(1, 3):
            code = '''{
                int ndigits = %d;
                int max = 1;
                int i;
                int j;
                for(i=0;i<ndigits;i=i+1){
                    max = max*10;
                }
                int largest = 0;
                for(i=0;i<max;i=i+1){
                    for(j=i;j<max;j=j+1){
                        int mul = i*j;

                        int num = mul;
                        int rev = 0;
                        int len = 0;
                        int num2 = num;
                        while(num2>0){
                            num2 = num2/10;
                            len=len+1;
                        }
                        while(len>0){
                            int mod = num %% 10;
                            num = num/10;
                            rev = (rev*10)+mod;
                            len = len-1;
                        }

                        if(mul == rev){
                            if(mul > largest){
                                largest = mul;
                            }
                        }
                    }
                }
            }''' % digits
            vals = executecode(code)
            self.assertEqual(vals['largest'], pythsol(digits))

    def test_primes(self):
        def pythsol(n):
            if n <= 1:
                return 1

            for i in range(n + 1):
                isprime = True
                for j in range(2, i):
                    if i % j == 0:
                        isprime = False
                        break
                if isprime:
                    prime = i
            return prime

        for num in range(1, 100):
            code = '''{
                int num = %d;
                int prime;
                if(num<=1){
                    prime = 1;
                }else{
                    int i;
                    int j;
                    for(i=0;i<(num+1);i=i+1){
                        int isprime = 1;
                        for(j=2;j<i;j=j+1){
                            if((i%%j)==0){
                                isprime = 0;
                            }
                        }
                        if(isprime){
                            prime = i;
                        }
                    }
                }
            }''' % num
            vals = executecode(code)
            self.assertEqual(vals['prime'], pythsol(num))

if __name__ == '__main__':
    unittest.main()
