all_ops = [
    'jump',
    'jumpfalse',
    'label',
    'function',
    'call',
    'end-fun',
    'return',
    'push',
    'pop',
    'assign',
    'binop',
    'unop',
]

op_uses_values = {
    'push': [1],
    'pop': [3],
    'jumpfalse': [1],
    'assign': [1],
    'binop': [1, 2],
    'unop': [1],
}

op_commutative = ['+', '*', '==', '!=']


def isvar(arg):
    if arg is None:
        return False
    if type(arg) is not str:
        return False
    if arg.startswith('.t'):
        return False
    if arg.startswith('default-'):
        return False
    return True
