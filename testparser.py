import parser

grammar = parser.mcgrammar
errors = 0
tests = 0


def teststmt(stmt, rule, result):
    global tests, errors
    tests += 1
    try:
        if rule is None:
            grammar.parse(stmt)
        else:
            grammar[rule].parse(stmt)
        if not result:
            errors += 1
            print('"%s" is a %s' % (stmt, rule))
    except Exception, e:
        if result:
            errors += 1
            print('"%s" is not a %s' % (stmt, rule))
            print(e)

# types
teststmt('+', 'type', False)
teststmt('test', 'type', False)
teststmt('int', 'type', True)
teststmt('float', 'type', True)

# literals
teststmt('+', 'int_lit', False)
teststmt('test', 'int_lit', False)
teststmt('1', 'int_lit', True)
teststmt('4.5', 'float_lit', True)

# variables
teststmt('1', 'identifier', False)
teststmt('4.5', 'identifier', False)
teststmt('_asd', 'identifier', False)
teststmt('x', 'identifier', True)
teststmt('asd0123_123', 'identifier', True)
# TODO test variable scope,  ...

# binary operands
teststmt('1', 'bin_op', False)
teststmt('+', 'bin_op', True)
teststmt('*', 'bin_op', True)
teststmt('=', 'bin_op', True)
teststmt('==', 'bin_op', True)
teststmt('<', 'bin_op', True)
teststmt('<=', 'bin_op', True)

# expressions
teststmt('test', 'literal', False)
# TODO test AST val
teststmt('1', 'literal', True)
teststmt('4.5', 'literal', True)

teststmt('test', 'binary_operation', False)
teststmt('4.5', 'binary_operation', False)
teststmt('+', 'binary_operation', False)
teststmt('1+7', 'binary_operation', True)
teststmt('1 +  7.1', 'binary_operation', True)
teststmt('1+', 'binary_operation', False)

teststmt('1', 'unary_expr', False)
teststmt('-4.2', 'unary_expr', True)

teststmt('-4.2', 'paren_expr', False)
teststmt('(1+7)', 'paren_expr', True)

# statements
teststmt('test', 'expr_stmt', False)
teststmt('1;', 'expr_stmt', True)

teststmt('test', 'compound_stmt', False)
teststmt('{}', 'compound_stmt', True)
teststmt('{ 1; { {} 7; }}', 'compound_stmt', True)

teststmt('test', 'if_stmt', False)
teststmt('if(1) {}', 'if_stmt', True)
teststmt('if (1) {} else 5;', 'if_stmt', True)
teststmt('int test;', 'decl_stmt', True)

teststmt(
"""{
    int x;
    if(1 == 2) {
        5+4*8.0;
        7;
        x = 8;
    } else {
        if(2 < 9) {
        }
    }
    2.9;
}""", 'statement', True)
teststmt(
"""{
    int x=1;
    float y = 3.0;
    if(x > 0) {
        y = y * 1.5;
    } else {
        y = y + 2.0;
    }
}""", 'statement', True)

print("[%d/%d] tests succeded!" % (tests-errors, tests))
