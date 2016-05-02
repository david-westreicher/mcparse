operations = {
    '<=': lambda x, y: x <= y,
    '>=': lambda x, y: x >= y,
    '==': lambda x, y: x == y,
    '!=': lambda x, y: x != y,
    '<': lambda x, y: x < y,
    '>': lambda x, y: x > y,
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    '/': lambda x, y: x // y,
    '%': lambda x, y: x % y,
    'u!': lambda x: not x,
    'u-': lambda x: - x,
    '!': None
}


def run(bbs, verbose=0):
    if len(bbs) == 0:
        return {}
    code = [instr for bb in bbs for instr in bb]

    vals = {'default-int': 0, 'default-float': 0.0}

    def toval(arg):
        if type(arg) is str:
            return vals[arg]
        return arg
    label_to_line = {}
    for linenum, (op, _, _, result) in enumerate(code):
        if op != 'label':
            continue
        label_to_line[result] = linenum

    pc = 0
    end = len(code) - 1
    while pc <= end:
        op, arg1, arg2, result = code[pc]
        if op == 'assign':
            vals[result] = toval(arg1)
        if op == 'jump':
            pc = label_to_line[result]
            continue
        if op == 'jumpfalse':
            if not toval(arg1):
                pc = label_to_line[result]
                continue
        if op in operations:
            isunop = op == '!' or (op == '-' and arg2 is None)
            if isunop:
                vals[result] = operations['u' + op](toval(arg1))
            else:
                vals[result] = operations[op](toval(arg1), toval(arg2))
        pc += 1

    tmpvars = [el for el in vals if el.startswith('.t')] + ['default-int', 'default-float']
    vals = {el: vals[el] for el in vals if el not in tmpvars}

    if verbose > 0:
        print('\n' + ' VM result '.center(40, '#'))
        print(vals)
    return vals

if __name__ == '__main__':
    import argparse
    from .parser import parsefile
    from .three import asttothree
    from .bb import threetobbs
    from .lvn import lvn
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The *.mc file to run.")
    parser.add_argument('--lvn', '-l', action='count', default=False)
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    bbs = threetobbs(
        asttothree(
            parsefile(
                args.filename,
                verbose=args.verbose - 2),
            verbose=args.verbose - 1),
        verbose=args.verbose)
    if args.lvn:
        bbs = lvn(bbs, verbose=1)
    run(bbs, args.verbose + 1)
