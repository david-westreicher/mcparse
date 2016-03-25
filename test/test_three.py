import unittest
from src import three
from src import parser


def codetothree(stringcode):
    return three.asttothree(parser.parse(stringcode))


class TestThree(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(three.asttothree(None), [])


class TestScope(unittest.TestCase):

    def test_doubledeclar(self):
        with self.assertRaises(three.ScopeException) as e:
            codetothree('{int x=1;int x=2;}')

    def test_notinscope_left(self):
        with self.assertRaises(three.ScopeException) as e:
            codetothree('x=1;')

    def test_notinscope_right(self):
        with self.assertRaises(three.ScopeException) as e:
            codetothree('int x=y;')

    def test_ref_before_decl(self):
        with self.assertRaises(three.ScopeException) as e:
            codetothree('int x=x;')

    def test_compound_scopes(self):
        try:
            codetothree('{{int x=1;}{int x=2;}}')
        except:
            self.fail('shouldn\'t cause an exception')

    def test_if_scopes(self):
        try:
            codetothree('if(1){int x=1;}else{int x=2;}')
        except:
            self.fail('shouldn\'t cause an exception')


if __name__ == '__main__':
    unittest.main()
