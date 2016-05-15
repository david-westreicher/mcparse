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

op_sets_result = [
    'pop',
    'assign',
    'binop',
    'unop',
]

bin_ops = ['+', '-', '*', '/', '%', '==', '!=', '<=', '>=', '<', '>']
op_commutative = ['+', '*', '==', '!=']
op_is_comp = ['==', '!=', '<=', '>=', '<', '>']
un_ops = ['u-', 'u!']


def simplify_op(op):
    if op in bin_ops:
        return 'binop'
    if op in un_ops:
        return 'unop'
    return op


def printcode(code):
    from .three import prettythreestr
    fun_ranges = function_ranges2(code)
    for fun, start, end in fun_ranges:
        for funline, tac in enumerate(code[start:end]):
            op, _, _, _ = tac
            linenum = str(funline + start).rjust(3)
            indent = '' if fun == '__global__' or op == 'function' else '\t'
            print(linenum + '\t' + indent + prettythreestr(*tac))


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


# TODO function_ranges should only work on code, not basic blocks
def function_ranges(bbs, asDic=False):
    '''
    Generates the following array:
        [
            ["__global__",  0,  5],
            ["fun1",        5, 10],
            ["fun2",       10, 20],
        ]
    '''
    functions = {}
    currfunc = '__global__'
    for blocknum, bb in enumerate(bbs):
        for op, _, _, fname in bb:
            if op == 'function':
                currfunc = fname
        if currfunc not in functions:
            functions[currfunc] = [blocknum, blocknum + 1]
        else:
            functions[currfunc][1] = blocknum + 1
    if not asDic:
        return sorted([(name, start, end) for name, (start, end) in functions.items()], key=lambda x: x[1])
    return functions


def function_ranges2(code, asDic=False):
    functions = {}
    currfunc = '__global__'
    for codeline, (op, _, _, fname) in enumerate(code):
        if op == 'function':
            currfunc = fname
        if currfunc not in functions:
            functions[currfunc] = [codeline, codeline + 1]
        else:
            functions[currfunc][1] = codeline + 1
    if not asDic:
        return sorted([(name, start, end) for name, (start, end) in functions.items()], key=lambda x: x[1])
    return functions


def makeDotFile(dotfile, bbs, ctrlflowgraph=None):
    if ctrlflowgraph is None:
        from .cfg import bbstocfg
        ctrlflowgraph = bbstocfg(bbs, verbose=1)

    def gen_block_calls_fun(bbs):
        block_calls_fun = {i: set() for i in range(len(bbs))}
        for i, bb in enumerate(bbs):
            for op, _, _, fname in bb:
                if op == 'call':
                    block_calls_fun[i].add(fname)
        if 'main' in fun_ranges and '__global__' in fun_ranges:
            last_glob_block = fun_ranges['__global__'][1]
            block_calls_fun[last_glob_block].add('main')
        return block_calls_fun

    def bb_to_dotnode(bb, num, children):
        import cgi
        from .three import prettythreestr
        dotnode = 'node [shape=plaintext]\n'
        html = ['<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0">']
        for op, arg1, arg2, res in bb:
            if op in ['end-fun', 'function']:
                continue
            html.append('<TR>')
            parts = cgi.escape(prettythreestr(op, arg1, arg2, res)).split('\t')
            for part in parts:
                html.append('<TD>' + part + '</TD>')
            for _ in range(5 - len(parts)):
                html.append('<TD></TD>')
            html.append('</TR>')
        html.append('</TABLE>>')
        dotnode += str(num) + ' [label=' + '\n'.join(html) + '];\n'
        for child in children:
            dotnode += '%s -> %s;\n' % (num, child)
        return dotnode

    fun_ranges = function_ranges(bbs, asDic=True)
    block_calls_fun = gen_block_calls_fun(bbs)

    with open(dotfile, 'w') as f:
        f.write('digraph R {\n')
        for cluster, fun in enumerate(fun_ranges):
            f.write('subgraph cluster%d {\n' % cluster)
            startblock, endblock = fun_ranges[fun]
            for i in range(startblock, endblock):
                bb = bbs[i]
                children = ctrlflowgraph[i]
                bbnode = bb_to_dotnode(bb, i, children)
                f.write(bbnode.replace('\n', '\n\t'))
            f.write('label = "%s";\n' % fun)
            f.write('}\n')
        for block, fnames in block_calls_fun.items():
            for fname in fnames:
                f.write('%s -> %s;\n' % (block, fun_ranges[fname][0]))
        f.write('}')

lib_sigs = [
    ('read_int', 'int', []),
    ('read_float', 'float', []),
    ('print_int', 'void', [('int', 'x')]),
    ('print_float', 'void', [('float', 'x')]),
]
